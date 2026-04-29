"""all_declared — every livespec module declares `__all__: list[str]`.

Per `python-skill-script-style-requirements.md` lines 943-960
every module under `.claude-plugin/scripts/livespec/**` MUST
declare a module-top `__all__: list[str]` listing the public API
names. The check walks the package, parses each AST, and
verifies that an annotated assignment of `__all__: list[str]` is
present at the module top level.

Scope is the `livespec` package only (`bin/*.py` wrappers and
dev-tooling scripts are NOT in scope; the rule applies to the
shipped library surface). Each cycle pins one specific failure
mode; cycle 36 pins the canonical "missing `__all__`" pattern.
Other failure modes (e.g., a name listed in `__all__` that is
not actually defined) are deferred per v032 D1
one-pattern-per-cycle.
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


def _is_all_declaration(*, node: ast.stmt) -> bool:
    if not isinstance(node, ast.AnnAssign):
        return False
    target = node.target
    if not isinstance(target, ast.Name) or target.id != "__all__":
        return False
    return _is_list_str_annotation(annotation=node.annotation)


def _is_list_str_annotation(*, annotation: ast.expr) -> bool:
    if not isinstance(annotation, ast.Subscript):
        return False
    if not isinstance(annotation.value, ast.Name) or annotation.value.id != "list":
        return False
    slice_node = annotation.slice
    return isinstance(slice_node, ast.Name) and slice_node.id == "str"


def _has_all_declaration(*, tree: ast.Module) -> bool:
    return any(_is_all_declaration(node=node) for node in tree.body)


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
    log = structlog.get_logger("all_declared")
    cwd = Path.cwd()
    tree_root = cwd / _LIVESPEC_TREE
    if not tree_root.is_dir():
        return 0
    found_any = False
    for py_file in _iter_python_files(root=tree_root):
        source = py_file.read_text(encoding="utf-8")
        module_ast = ast.parse(source, filename=str(py_file))
        if not _has_all_declaration(tree=module_ast):
            log.error(
                "module missing `__all__: list[str]` declaration",
                path=str(py_file.relative_to(cwd)),
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
