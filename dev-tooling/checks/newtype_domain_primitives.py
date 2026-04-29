"""newtype_domain_primitives — canonical field-name → NewType mapping.

Per `python-skill-script-style-requirements.md` §"Domain primitives via
`NewType`" (lines 962-1010) and the canonical-target table line 2090:

    AST: walks `schemas/dataclasses/*.py` and function signatures;
    verifies field annotations matching canonical field names use
    the corresponding `livespec/types.py` NewType. Field-name keyed
    mapping table (lines 975-984): `check_id`→`CheckId`,
    `run_id`→`RunId`, `topic`→`TopicSlug`, `spec_root`→`SpecRoot`,
    `schema_id`→`SchemaId`, `template`→`TemplateName`,
    `author`/`author_human`/`author_llm`→`Author`,
    `version_tag`→`VersionTag`. Note that `template_root` is the
    resolved-directory `Path` and uses raw `Path`, NOT
    `TemplateName` — the L8 mapping is field-name keyed, and
    `template_root` doesn't match `template`.

Cycle 49 pins ONE narrow violation pattern per v032 D1
one-pattern-per-cycle:

    A function-signature parameter named `run_id` annotated
    with anything other than `RunId`.

The other seven canonical mappings (`check_id`, `topic`,
`spec_root`, `schema_id`, `template`, `author*`, `version_tag`)
and the dataclass-field walk are deferred to subsequent cycles.
The current source tree has zero `run_id`-annotated parameters,
so the check passes vacuously today; the check exists to catch
the next agent who introduces `run_id: str` (or anything other
than `run_id: RunId`).
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


_LIVESPEC_TREE = Path(".claude-plugin") / "scripts" / "livespec"
_FIELD_NAME = "run_id"
_EXPECTED_NEWTYPE = "RunId"


def _annotation_name(*, annotation: ast.expr | None) -> str | None:
    if isinstance(annotation, ast.Name):
        return annotation.id
    if isinstance(annotation, ast.Attribute):
        return annotation.attr
    return None


def _iter_params(*, args: ast.arguments) -> list[ast.arg]:
    return [*args.posonlyargs, *args.args, *args.kwonlyargs]


def _find_violations(*, tree: ast.Module) -> list[tuple[int, str, str | None]]:
    offenders: list[tuple[int, str, str | None]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for arg in _iter_params(args=node.args):
            if arg.arg != _FIELD_NAME:
                continue
            ann_name = _annotation_name(annotation=arg.annotation)
            if ann_name == _EXPECTED_NEWTYPE:
                continue
            offenders.append((arg.lineno, node.name, ann_name))
    return offenders


def _iter_python_files(*, root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


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
    tree_root = cwd / _LIVESPEC_TREE
    if not tree_root.is_dir():
        return 0
    found_any = False
    for py_file in _iter_python_files(root=tree_root):
        source = py_file.read_text(encoding="utf-8")
        module_ast = ast.parse(source, filename=str(py_file))
        for lineno, fn_name, observed in _find_violations(tree=module_ast):
            log.error(
                "parameter `run_id` not annotated as `RunId`",
                path=str(py_file.relative_to(cwd)),
                line=lineno,
                function=fn_name,
                observed_annotation=observed or "<missing-or-complex>",
                expected_annotation=_EXPECTED_NEWTYPE,
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
