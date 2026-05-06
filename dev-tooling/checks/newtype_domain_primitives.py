"""newtype_domain_primitives — canonical field names use `livespec/types.py` NewType.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-newtype-domain-primitives` row),
walks `schemas/dataclasses/*.py` (cycle 171 minimum-viable
scope) and verifies field annotations matching canonical
field names use the corresponding `livespec/types.py` NewType:

| field name      | required type   |
|-----------------|-----------------|
| check_id        | CheckId         |
| run_id          | RunId           |
| topic           | TopicSlug       |
| spec_root       | SpecRoot        |
| schema_id       | SchemaId        |
| template        | TemplateName    |
| author          | Author          |
| author_human    | Author          |
| author_llm      | Author          |
| version_tag     | VersionTag      |

Note: `template_root` (resolved directory) is `Path`, NOT
`TemplateName` — the field-name lookup is exact, so the
mapping isn't keyed on substring.

Subsequent cycles widen scope to function signatures across
all of `livespec/**`.

Output discipline: per spec, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_DATACLASSES_TREE = Path(".claude-plugin") / "scripts" / "livespec" / "schemas" / "dataclasses"
_FIELD_TO_NEWTYPE: dict[str, str] = {
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


def _annotation_terminal_name(*, annotation: ast.expr) -> str:
    # Peel `X | None` to X (PEP 604 union shape). The `| None` only
    # marks the field as optional; whether the inner type is the
    # required NewType is the actual check.
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        left, right = annotation.left, annotation.right
        if isinstance(right, ast.Constant) and right.value is None:
            return _annotation_terminal_name(annotation=left)
        if isinstance(left, ast.Constant) and left.value is None:
            return _annotation_terminal_name(annotation=right)
    rendered = ast.unparse(annotation)
    head = rendered.split("[", maxsplit=1)[0]
    return head.rsplit(".", maxsplit=1)[-1]


def _find_offenders_in_class(*, cls: ast.ClassDef) -> list[tuple[int, str, str, str]]:
    """Return list of (lineno, field_name, actual_type, required_type)."""
    out: list[tuple[int, str, str, str]] = []
    for stmt in cls.body:
        if not (isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)):
            continue
        field_name = stmt.target.id
        if field_name not in _FIELD_TO_NEWTYPE:
            continue
        required = _FIELD_TO_NEWTYPE[field_name]
        actual = _annotation_terminal_name(annotation=stmt.annotation)
        if actual != required:
            out.append((stmt.lineno, field_name, actual, required))
    return out


def _find_offenders(*, source: str) -> list[tuple[int, str, str, str]]:
    tree = ast.parse(source)
    out: list[tuple[int, str, str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            out.extend(_find_offenders_in_class(cls=node))
    return out


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("newtype_domain_primitives")
    cwd = Path.cwd()
    dataclasses_root = cwd / _DATACLASSES_TREE
    if not dataclasses_root.is_dir():
        return 0
    offenders: list[tuple[Path, int, str, str, str]] = []
    for py_file in sorted(dataclasses_root.glob("*.py")):
        source = py_file.read_text(encoding="utf-8")
        for lineno, field, actual, required in _find_offenders(source=source):
            offenders.append((py_file.relative_to(cwd), lineno, field, actual, required))
    if offenders:
        for path, lineno, field, actual, required in offenders:
            log.error(
                "canonical field name not using required NewType",
                file=str(path),
                line=lineno,
                field=field,
                actual_type=actual,
                required_type=required,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
