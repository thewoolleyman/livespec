"""no_except_outside_io — `try/except` only in `io/**` and supervisor `main()`.

Per `python-skill-script-style-requirements.md` line 2081:

    AST: catching exceptions outside `io/**` permitted only in
    supervisor bug-catchers (top-level `try/except Exception`
    in `main()` of `commands/*.py` and `doctor/run_static.py`).

The intent: domain-meaningful exceptions are wrapped at the IO
boundary into the Result railway; pure layers (parse, validate)
NEVER catch exceptions because there's nothing to catch (no
raise sites in those layers). Supervisors carry the one
permitted catch-all `except Exception` for bug-class crashes.

Cycle 40 pins the canonical violation: a `Try` AST node in any
livespec module that is NOT under `livespec/io/**` AND not
inside a supervisor `main()` body is rejected.

Permitted call-sites (recognized by the impl):

- Any `Try` node anywhere in `livespec/io/**`.
- Any `Try` node whose immediate enclosing `FunctionDef` is
  `def main(...)` AND the function is at module top level AND
  the module is one of `livespec/commands/<cmd>.py` or
  `livespec/doctor/run_static.py`.

The check walks the livespec tree, identifies each `Try` node,
and rejects every occurrence not in the permitted set.
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
_COMMANDS_DEPTH = 2  # `commands/<cmd>.py` is two path components below livespec root.


def _is_io_path(*, py_file: Path, livespec_root: Path) -> bool:
    relative = py_file.relative_to(livespec_root)
    return relative.parts[:1] == ("io",)


def _is_supervisor_path(*, py_file: Path, livespec_root: Path) -> bool:
    relative = py_file.relative_to(livespec_root)
    parts = relative.parts
    if parts[:1] == ("commands",) and len(parts) == _COMMANDS_DEPTH and parts[1].endswith(".py"):
        return True
    return parts == ("doctor", "run_static.py")


def _try_nodes_inside_main(*, tree: ast.Module) -> set[int]:
    inside: set[int] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == "main":
            for inner in ast.walk(node):
                if isinstance(inner, ast.Try):
                    inside.add(id(inner))
    return inside


def _find_violations(*, tree: ast.Module, supervisor: bool) -> list[int]:
    permitted = _try_nodes_inside_main(tree=tree) if supervisor else set()
    offenders: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Try) and id(node) not in permitted:
            offenders.append(node.lineno)
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
    log = structlog.get_logger("no_except_outside_io")
    cwd = Path.cwd()
    livespec_root = cwd / _LIVESPEC_TREE
    if not livespec_root.is_dir():
        return 0
    found_any = False
    for py_file in _iter_python_files(root=livespec_root):
        if _is_io_path(py_file=py_file, livespec_root=livespec_root):
            continue
        is_supervisor = _is_supervisor_path(py_file=py_file, livespec_root=livespec_root)
        source = py_file.read_text(encoding="utf-8")
        module_ast = ast.parse(source, filename=str(py_file))
        for lineno in _find_violations(tree=module_ast, supervisor=is_supervisor):
            log.error(
                "try/except outside io/** and supervisor main()",
                path=str(py_file.relative_to(cwd)),
                line=lineno,
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
