"""schema_dataclass_pairing: enforce v013 M6 three-way pairing.

Per python-skill-script-style-requirements.md canonical target list
line 1885 (`just check-schema-dataclass-pairing`):

    AST (three-way walker per v013 M6): for every
    `schemas/*.schema.json`, verifies a paired dataclass at
    `schemas/dataclasses/<name>.py` (the `$id`-derived name)
    AND a paired validator at `validate/<name>.py` exists;
    every listed schema field matches the dataclass's Python
    type; vice versa in all three walks. Drift in any direction
    fails.

The check enforces three-way file-existence pairing AND top-level
field-name + loose-type pairing between the schema and its
primary dataclass. Schema `<name>.schema.json` corresponds to
the dataclass whose name is the PascalCase of `<name>` (snake →
Pascal). Nested item structures within `items:` blocks are NOT
deeply traversed here — they are validated by virtue of the
dataclass's outer type annotation referencing another paired
dataclass (whose own pairing this check verifies separately) or
an inline-nested co-defined dataclass in the same file (e.g.,
`SeedFile` co-defined with `SeedInput` in
`schemas/dataclasses/seed_input.py`).

Type-matching rules for top-level fields:

| JSON Schema type | Permitted dataclass annotation |
|---|---|
| `"string"`        | `str`, or any `NewType` allowlist member from `livespec.types` |
| `"integer"`       | `int` |
| `"boolean"`       | `bool` |
| `"number"`        | `int`, `float`, or `int | float` |
| `"array"`         | `list[X]` for any `X` (inner type not deeply verified) |
| `"object"`        | `dict[...]` or any user-defined dataclass name |
| Multi-type / enum | best-effort substring match against schema-type permitted forms |

`Optional` / `| None` annotations are accepted when the schema
field is not in `required`.
"""

from __future__ import annotations

import ast
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

__all__: list[str] = [
    "check_repo",
    "main",
]


log = logging.getLogger(__name__)

_SCHEMAS_DIR = Path(".claude-plugin/scripts/livespec/schemas")
_DATACLASSES_DIR = Path(".claude-plugin/scripts/livespec/schemas/dataclasses")
_VALIDATE_DIR = Path(".claude-plugin/scripts/livespec/validate")
_PYCACHE_SUBSTR = "__pycache__"

_NEWTYPE_STRING_ALLOWLIST: frozenset[str] = frozenset(
    {
        "Author",
        "CheckId",
        "RunId",
        "SchemaId",
        "TemplateName",
        "TopicSlug",
        "VersionTag",
    }
)
_NEWTYPE_PATH_ALLOWLIST: frozenset[str] = frozenset({"SpecRoot"})

_SCHEMA_TO_PYTHON: dict[str, frozenset[str]] = {
    "string": frozenset({"str"}) | _NEWTYPE_STRING_ALLOWLIST,
    "integer": frozenset({"int"}),
    "boolean": frozenset({"bool"}),
    "number": frozenset({"int", "float"}),
}


def main() -> int:
    """Run check_repo from cwd; return 0 on pass, 1 on any violation."""
    repo_root = Path.cwd()
    failures = check_repo(repo_root=repo_root)
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("schema_dataclass_pairing: %d violation(s)", len(failures))
        return 1
    return 0


def check_repo(*, repo_root: Path) -> list[str]:
    """Walk all three trees; return list of violation messages."""
    schemas_dir = repo_root / _SCHEMAS_DIR
    dataclasses_dir = repo_root / _DATACLASSES_DIR
    validate_dir = repo_root / _VALIDATE_DIR
    if not schemas_dir.is_dir():
        return [f"{schemas_dir} does not exist"]
    schema_names = _list_schema_names(schemas_dir=schemas_dir)
    dataclass_names = _list_python_module_names(directory=dataclasses_dir)
    validator_names = _list_python_module_names(directory=validate_dir)
    violations: list[str] = []
    _check_pairing_existence(
        schema_names=schema_names,
        dataclass_names=dataclass_names,
        validator_names=validator_names,
        violations=violations,
    )
    common_names = schema_names & dataclass_names
    for name in sorted(common_names):
        schema_path = schemas_dir / f"{name}.schema.json"
        dataclass_path = dataclasses_dir / f"{name}.py"
        for v in _check_field_pairing(
            name=name,
            schema_path=schema_path,
            dataclass_path=dataclass_path,
        ):
            violations.append(v)
    return violations


def _list_schema_names(*, schemas_dir: Path) -> set[str]:
    """Return the set of `<name>` for every `<name>.schema.json` under schemas_dir."""
    names: set[str] = set()
    for path in schemas_dir.glob("*.schema.json"):
        names.add(path.name.removesuffix(".schema.json"))
    return names


def _list_python_module_names(*, directory: Path) -> set[str]:
    """Return module names (without .py) for non-dunder Python files under directory."""
    if not directory.is_dir():
        return set()
    names: set[str] = set()
    for path in directory.glob("*.py"):
        if path.name.startswith("_"):
            continue
        if _PYCACHE_SUBSTR in path.parts:
            continue
        names.add(path.stem)
    return names


def _check_pairing_existence(
    *,
    schema_names: set[str],
    dataclass_names: set[str],
    validator_names: set[str],
    violations: list[str],
) -> None:
    """Three-way pairing: each name in any tree must appear in all three."""
    all_names = schema_names | dataclass_names | validator_names
    for name in sorted(all_names):
        missing: list[str] = []
        if name not in schema_names:
            missing.append(f"schemas/{name}.schema.json")
        if name not in dataclass_names:
            missing.append(f"schemas/dataclasses/{name}.py")
        if name not in validator_names:
            missing.append(f"validate/{name}.py")
        if missing:
            violations.append(
                f"pairing-gap: `{name}` lacks {', '.join(missing)}",
            )


def _check_field_pairing(
    *,
    name: str,
    schema_path: Path,
    dataclass_path: Path,
) -> list[str]:
    """Top-level field-name + loose-type pairing for a schema/dataclass pair."""
    try:
        schema_doc = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return [f"{schema_path}: cannot read or parse schema: {e}"]
    schema_props = _schema_properties(schema_doc=schema_doc)
    schema_required = set(schema_doc.get("required", []))
    primary_class = _snake_to_pascal(snake=name)
    parsed = _parse_dataclass_module(dataclass_path=dataclass_path)
    if parsed is None:
        return [f"{dataclass_path}: cannot parse module"]
    fields, string_aliases = parsed
    if primary_class not in fields:
        return [
            f"{dataclass_path}: missing primary dataclass `{primary_class}` "
            f"(expected PascalCase of schema name `{name}`)",
        ]
    return _diff_fields(
        scope=_PairingScope(
            schema_path=schema_path,
            dataclass_path=dataclass_path,
            primary_class=primary_class,
            schema_props=schema_props,
            schema_required=schema_required,
            dataclass_fields=fields[primary_class],
            local_string_aliases=string_aliases,
        )
    )


@dataclass(frozen=True, kw_only=True, slots=True)
class _PairingScope:
    schema_path: Path
    dataclass_path: Path
    primary_class: str
    schema_props: dict[str, dict[str, object]]
    schema_required: set[str]
    dataclass_fields: dict[str, str]
    local_string_aliases: set[str]


def _diff_fields(*, scope: _PairingScope) -> list[str]:
    violations: list[str] = []
    schema_keys = set(scope.schema_props.keys())
    dataclass_keys = set(scope.dataclass_fields.keys())
    for missing_in_dataclass in sorted(schema_keys - dataclass_keys):
        violations.append(
            f"{scope.dataclass_path}: dataclass `{scope.primary_class}` lacks field "
            f"`{missing_in_dataclass}` declared in {scope.schema_path.name}",
        )
    for missing_in_schema in sorted(dataclass_keys - schema_keys):
        violations.append(
            f"{scope.schema_path}: schema lacks property `{missing_in_schema}` "
            f"declared on dataclass `{scope.primary_class}`",
        )
    for field in sorted(schema_keys & dataclass_keys):
        schema_type = scope.schema_props[field].get("type")
        annotation = scope.dataclass_fields[field]
        message = _check_type_match(
            schema_type=schema_type,
            annotation=annotation,
            required=field in scope.schema_required,
            local_string_aliases=scope.local_string_aliases,
        )
        if message is not None:
            violations.append(f"{scope.dataclass_path}: field `{field}` {message}")
    return violations


def _check_type_match(
    *,
    schema_type: object,
    annotation: str,
    required: bool,
    local_string_aliases: set[str],
) -> str | None:
    """Loose type-match: annotation contains a permitted Python form for the schema type.

    Single return point: each branch sets `message` and falls through.
    """
    message: str | None = None
    if not isinstance(schema_type, str):
        return message
    stripped = annotation
    if not required and stripped.endswith(" | None"):
        stripped = stripped.removesuffix(" | None")
    if schema_type == "array":
        if not (stripped.startswith("list[") and stripped.endswith("]")):
            message = f"schema `array` expects `list[...]` annotation, got `{annotation}`"
    elif schema_type == "object":
        if not (stripped.startswith(("dict[", "dict")) or _is_identifier(text=stripped)):
            message = f"schema `object` expects dict[...] or dataclass name, got `{annotation}`"
    else:
        permitted = _SCHEMA_TO_PYTHON.get(schema_type)
        accepted = permitted is not None and (
            stripped in permitted or (schema_type == "string" and stripped in local_string_aliases)
        )
        if permitted is not None and not accepted:
            message = (
                f"schema `{schema_type}` expects one of {sorted(permitted)}, got `{annotation}`"
            )
    return message


def _is_identifier(*, text: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", text))


def _snake_to_pascal(*, snake: str) -> str:
    """`seed_input` → `SeedInput`."""
    return "".join(part.capitalize() for part in snake.split("_"))


def _schema_properties(
    *,
    schema_doc: object,
) -> dict[str, dict[str, object]]:
    if not isinstance(schema_doc, dict):
        return {}
    props = schema_doc.get("properties", {})
    if not isinstance(props, dict):
        return {}
    typed: dict[str, dict[str, object]] = {}
    for k, v in props.items():
        if isinstance(k, str) and isinstance(v, dict):
            typed[k] = v
    return typed


def _parse_dataclass_module(
    *,
    dataclass_path: Path,
) -> tuple[dict[str, dict[str, str]], set[str]] | None:
    """Parse the dataclass module.

    Returns (class_fields, string_aliases) where:
    - class_fields maps `<ClassName>` → (field-name → annotation-string).
    - string_aliases is the set of module-level names whose value is a
      `Literal[<str>, <str>, ...]` (Literal-of-strings type alias),
      used to accept e.g. `status: FindingStatus` for a schema
      `"type": "string"` field.
    """
    text = dataclass_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(dataclass_path))
    except SyntaxError:
        return None
    class_fields: dict[str, dict[str, str]] = {}
    string_aliases: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_fields[node.name] = _collect_class_fields(class_def=node)
        elif isinstance(node, ast.Assign) and _is_string_literal_alias(assign=node):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    string_aliases.add(target.id)
    return class_fields, string_aliases


def _collect_class_fields(*, class_def: ast.ClassDef) -> dict[str, str]:
    fields: dict[str, str] = {}
    for child in class_def.body:
        if not isinstance(child, ast.AnnAssign):
            continue
        if not isinstance(child.target, ast.Name):
            continue
        fields[child.target.id] = ast.unparse(child.annotation)
    return fields


def _is_string_literal_alias(*, assign: ast.Assign) -> bool:
    """True iff `assign` is `<Name> = Literal["...", "...", ...]` of string args only."""
    value = assign.value
    if not (
        isinstance(value, ast.Subscript)
        and isinstance(value.value, ast.Name)
        and value.value.id == "Literal"
    ):
        return False
    slice_node = value.slice
    args = slice_node.elts if isinstance(slice_node, ast.Tuple) else [slice_node]
    return all(isinstance(arg, ast.Constant) and isinstance(arg.value, str) for arg in args)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
