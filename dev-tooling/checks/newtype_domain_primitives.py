"""newtype_domain_primitives: enforce v012 L8 NewType discipline.

Per python-skill-script-style-requirements.md §"Domain primitives
via `NewType`" lines 932-981 + canonical target list line 1892:

Walks `livespec/schemas/dataclasses/*.py` and `livespec/**.py`
function signatures; verifies that any field annotation OR
parameter annotation matching one of the canonical role field
names uses the corresponding `livespec.types.<NewType>` rather
than the bare underlying primitive. Partial mismatches (right
NewType wrong field name; or right field name wrong NewType)
both fail.

Field-name → NewType mapping (per L8 table):

| Field name      | NewType       | Underlying |
|-----------------|---------------|------------|
| `check_id`      | `CheckId`     | `str`      |
| `run_id`        | `RunId`       | `str`      |
| `topic`         | `TopicSlug`   | `str`      |
| `spec_root`     | `SpecRoot`    | `Path`     |
| `schema_id`     | `SchemaId`    | `str`      |
| `template`      | `TemplateName`| `str`      |
| `author`        | `Author`      | `str`      |
| `author_human`  | `Author`      | `str`      |
| `author_llm`    | `Author`      | `str`      |
| `version_tag`   | `VersionTag`  | `str`      |

Special exemption: `template_root: Path` field is the resolved
directory and uses raw `Path`, NOT `TemplateName` — the L8
mapping is field-name keyed and `template_root` does not match
`template`.

Annotations may include `| None` for Optional fields.
"""

from __future__ import annotations

import ast
import logging
import sys
from pathlib import Path

__all__: list[str] = [
    "check_file",
    "main",
]


log = logging.getLogger(__name__)

_LIVESPEC_DIR = Path(".claude-plugin/scripts/livespec")
_VENDOR_SUBSTR = "_vendor"
_PYCACHE_SUBSTR = "__pycache__"

_CANONICAL_FIELD_TO_NEWTYPE: dict[str, str] = {
    "check_id": "CheckId",
    "run_id": "RunId",
    "topic": "TopicSlug",
    "spec_root": "SpecRoot",
    "schema_id": "SchemaId",
    "template": "TemplateName",
    "author": "Author",
    "author_human": "Author",
    "author_llm": "Author",
    "version_tag": "VersionTag",
}


def main() -> int:
    """Walk livespec/**.py; return 0 on pass, 1 on any violation."""
    repo_root = Path.cwd()
    livespec_dir = repo_root / _LIVESPEC_DIR
    if not livespec_dir.is_dir():
        log.error("%s does not exist; cannot check newtype_domain_primitives", livespec_dir)
        return 1
    failures: list[str] = []
    for path in sorted(livespec_dir.rglob("*.py")):
        if _VENDOR_SUBSTR in path.parts or _PYCACHE_SUBSTR in path.parts:
            continue
        for v in check_file(path=path):
            failures.append(f"{path}: {v}")
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("newtype_domain_primitives: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path) -> list[str]:
    """Return violation messages for `path`. Empty = pass."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            _check_annotation(
                field_name=node.target.id,
                annotation=node.annotation,
                lineno=node.lineno,
                violations=violations,
            )
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for arg in (
                list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs)
            ):
                if arg.arg in {"self", "cls"} or arg.annotation is None:
                    continue
                _check_annotation(
                    field_name=arg.arg,
                    annotation=arg.annotation,
                    lineno=arg.lineno,
                    violations=violations,
                )
    return violations


def _check_annotation(
    *,
    field_name: str,
    annotation: ast.expr,
    lineno: int,
    violations: list[str],
) -> None:
    expected_newtype = _CANONICAL_FIELD_TO_NEWTYPE.get(field_name)
    if expected_newtype is None:
        return  # field name is not in the canonical L8 table — out of scope
    rendered = ast.unparse(annotation)
    stripped = rendered.removesuffix(" | None")
    if stripped == expected_newtype:
        return
    violations.append(
        f"line {lineno}: field/param `{field_name}` annotated as `{rendered}`; "
        f"expected `{expected_newtype}` per v012 L8 mapping",
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
