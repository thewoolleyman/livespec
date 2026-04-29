"""supervisor_discipline — `sys.exit` / `raise SystemExit` only in `bin/*.py`.

Per `python-skill-script-style-requirements.md` line 2079:

    AST: `sys.exit` / `raise SystemExit` only in `bin/*.py`
    (incl. `_bootstrap.py`).

The supervisor pattern: `bin/*.py` wrappers raise SystemExit
with the integer return of `main()`; the livespec library code
never directly invokes `sys.exit` or raises `SystemExit`. Domain
errors flow through the Result railway and are converted to
exit codes by the supervisor.

Cycle 44 pins two violation patterns and one exemption:

1. `sys.exit(...)` inside `.claude-plugin/scripts/livespec/**`
   is rejected.
2. `raise SystemExit(...)` inside the same scope is rejected.
3. `raise SystemExit(main())` (and any sys.exit / raise
   SystemExit) inside `.claude-plugin/scripts/bin/*.py` is
   accepted.

Smallest impl: walk `.claude-plugin/scripts/livespec/**.py`,
parse each AST. Walk every `Call` (catches `sys.exit(...)` —
matched as `Call(Attribute(Name("sys"), "exit"))`) and every
`Raise` (catches `raise SystemExit(...)` — matched by the
exception target's name). One structlog diagnostic per
offender; exit 1 if any matched.
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


def _is_sys_exit_call(*, call: ast.Call) -> bool:
    func = call.func
    return (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id == "sys"
        and func.attr == "exit"
    )


def _raise_target_name(*, node: ast.Raise) -> str | None:
    if node.exc is None:
        return None
    target = node.exc
    if isinstance(target, ast.Call):
        target = target.func
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


def _find_violations(*, tree: ast.Module) -> list[tuple[int, str]]:
    offenders: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_sys_exit_call(call=node):
            offenders.append((node.lineno, "sys.exit"))
        elif isinstance(node, ast.Raise) and _raise_target_name(node=node) == "SystemExit":
            offenders.append((node.lineno, "raise SystemExit"))
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
    log = structlog.get_logger("supervisor_discipline")
    cwd = Path.cwd()
    livespec_root = cwd / _LIVESPEC_TREE
    if not livespec_root.is_dir():
        return 0
    found_any = False
    for py_file in _iter_python_files(root=livespec_root):
        source = py_file.read_text(encoding="utf-8")
        module_ast = ast.parse(source, filename=str(py_file))
        for lineno, offense in _find_violations(tree=module_ast):
            log.error(
                "supervisor exit outside bin/",
                path=str(py_file.relative_to(cwd)),
                line=lineno,
                kind=offense,
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
