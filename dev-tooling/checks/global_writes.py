"""global_writes — no module-level mutable state writes from functions.

Per `python-skill-script-style-requirements.md` line 2077:

    AST: no module-level mutable state writes from functions.

Mutating module-level state from inside a function body
introduces hidden coupling: callers can't reason about a
function's effect from its arguments alone.

Cycle 45 pins the canonical violation: a function body
declaring `global x` (Python's syntactic marker for intent to
mutate a module-level binding) is rejected. The `global`
declaration in Python is, by language design, the explicit
signal that the function intends to write to a module-level
name.

Recognized exemptions per spec lines 1772-1781 (NOT yet
implemented; deferred per v032 D1 one-pattern-per-cycle):

- `structlog.configure(...)` and `bind_contextvars(...)` in
  `livespec/__init__.py`.
- The `_COMPILED` cache mutation in
  `livespec/io/fastjsonschema_facade.py`.

Currently the check has no exemption table; it flags every
`global` declaration. The exemption table will land once the
exempt module surface materializes and the check would
otherwise refuse legitimate code.
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


def _find_globals_in_functions(*, tree: ast.Module) -> list[tuple[int, str]]:
    offenders: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Global):
                names = ", ".join(inner.names)
                offenders.append((inner.lineno, names))
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
    log = structlog.get_logger("global_writes")
    cwd = Path.cwd()
    livespec_root = cwd / _LIVESPEC_TREE
    if not livespec_root.is_dir():
        return 0
    found_any = False
    for py_file in _iter_python_files(root=livespec_root):
        source = py_file.read_text(encoding="utf-8")
        module_ast = ast.parse(source, filename=str(py_file))
        for lineno, names in _find_globals_in_functions(tree=module_ast):
            log.error(
                "function declares `global` (mutates module-level state)",
                path=str(py_file.relative_to(cwd)),
                line=lineno,
                names=names,
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
