"""private_calls — no cross-module calls to `_`-prefixed functions.

Per `python-skill-script-style-requirements.md` line 2076:

    AST: no cross-module calls to `_`-prefixed functions defined
    elsewhere.

The leading-underscore prefix marks a function private to its
defining module. Any cross-module reference (whether via
`from module import _name` import or via `module._name`
attribute access on an imported module) is a violation. The rule
pairs with ruff `SLF` (which catches `_`-prefixed *attribute*
access on instances) — this AST check covers the function-call
import surface that `SLF` does not.

The script walks the same in-scope trees as `file_lloc.py`
(`.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, `<repo-root>/dev-tooling/**`,
plus `<repo-root>/tests/**` per spec line 67-69) and exits 0 if
no cross-module private call is found, exits 1 otherwise (one
structlog diagnostic per offender).

Dunder names (e.g., `__future__`, `__all__`, `__name__`) are
NOT considered private under this rule — they are Python-mandated
double-underscore identifiers, distinct from the
single-leading-underscore convention.
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


_IN_SCOPE_TREES: tuple[Path, ...] = (
    Path(".claude-plugin") / "scripts" / "livespec",
    Path(".claude-plugin") / "scripts" / "bin",
    Path("dev-tooling"),
    Path("tests"),
)


def _is_private_name(*, name: str) -> bool:
    return name.startswith("_") and not name.startswith("__")


def _find_private_imports(*, tree: ast.Module) -> list[tuple[int, str]]:
    offenders: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if _is_private_name(name=alias.name):
                    offenders.append((node.lineno, alias.name))
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
    log = structlog.get_logger("private_calls")
    cwd = Path.cwd()
    found_any = False
    for tree_path in _IN_SCOPE_TREES:
        tree_root = cwd / tree_path
        if not tree_root.is_dir():
            continue
        for py_file in _iter_python_files(root=tree_root):
            source = py_file.read_text(encoding="utf-8")
            module_ast = ast.parse(source, filename=str(py_file))
            for lineno, name in _find_private_imports(tree=module_ast):
                log.error(
                    "cross-module private import",
                    path=str(py_file.relative_to(cwd)),
                    line=lineno,
                    imported_name=name,
                )
                found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
