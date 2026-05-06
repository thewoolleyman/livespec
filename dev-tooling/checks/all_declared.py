"""all_declared — every livespec module declares `__all__` and lists only defined names.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-all-declared` row), every module
under `.claude-plugin/scripts/livespec/**` MUST declare a
module-top `__all__: list[str]` (typed annotation, list
literal of string constants). Every name in `__all__` must
also be defined within the module — as a top-level `def`,
`class`, plain assignment, annotated assignment, or
`from <pkg> import <name>` statement.

The check walks every `.py` file under `.claude-plugin/
scripts/livespec/`, parses each via `ast`, and inspects every
module-top `AnnAssign` whose target is `__all__`. Two failure
modes:

- Missing `__all__` declaration (no module-top `__all__:
  list[str] = [...]` at all).
- Names in `__all__` that aren't defined as module-top
  symbols.

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


_LIVESPEC_TREE = Path(".claude-plugin") / "scripts" / "livespec"


def _names_from_def(
    *,
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
) -> set[str]:
    return {node.name}


def _names_from_assign(*, node: ast.Assign) -> set[str]:
    return {target.id for target in node.targets if isinstance(target, ast.Name)}


def _names_from_annassign(*, node: ast.AnnAssign) -> set[str]:
    if isinstance(node.target, ast.Name):
        return {node.target.id}
    return set()


def _names_from_import_from(*, node: ast.ImportFrom) -> set[str]:
    return {alias.asname or alias.name for alias in node.names}


def _names_from_import(*, node: ast.Import) -> set[str]:
    return {alias.asname or alias.name.split(".", maxsplit=1)[0] for alias in node.names}


def _module_top_defined_names(*, tree: ast.Module) -> set[str]:
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            out |= _names_from_def(node=node)
        elif isinstance(node, ast.Assign):
            out |= _names_from_assign(node=node)
        elif isinstance(node, ast.AnnAssign):
            out |= _names_from_annassign(node=node)
        elif isinstance(node, ast.ImportFrom):
            out |= _names_from_import_from(node=node)
        elif isinstance(node, ast.Import):
            out |= _names_from_import(node=node)
    return out


def _all_value_names(*, tree: ast.Module) -> list[str] | None:
    for node in tree.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "__all__"
            and isinstance(node.value, ast.List)
        ):
            return [
                elt.value
                for elt in node.value.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            ]
    return None


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
    livespec_root = cwd / _LIVESPEC_TREE
    missing: list[Path] = []
    undefined: list[tuple[Path, str]] = []
    if livespec_root.is_dir():
        for py_file in sorted(livespec_root.rglob("*.py")):
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
            names = _all_value_names(tree=tree)
            rel = py_file.relative_to(cwd)
            if names is None:
                missing.append(rel)
                continue
            defined = _module_top_defined_names(tree=tree)
            for name in names:
                if name not in defined:
                    undefined.append((rel, name))
    for path in missing:
        log.error("module missing `__all__: list[str]` declaration", file=str(path))
    for path, name in undefined:
        log.error(
            "name listed in `__all__` not defined in module",
            file=str(path),
            name=name,
        )
    return 1 if (missing or undefined) else 0


if __name__ == "__main__":
    raise SystemExit(main())
