"""supervisor_discipline: enforce supervisor catch-all + sys.exit scope.

Per python-skill-script-style-requirements.md lines 469-471, 567-571,
581-596, 1803:

Rule 1 — `sys.exit` and `raise SystemExit`:
    Permitted ONLY in `.claude-plugin/scripts/bin/*.py` (including
    `_bootstrap.py`). Forbidden in `.claude-plugin/scripts/livespec/**`.

Rule 2 — supervisor catch-all bug-catcher:
    Supervisors are `def main(...)` at module top-level in
    `.claude-plugin/scripts/livespec/commands/<cmd>.py` and in
    `.claude-plugin/scripts/livespec/doctor/run_static.py`.
    Each supervisor MUST have EXACTLY ONE catch-all `try/except
    Exception` (or `BaseException`, or bare `except:`) in its body.
    No catch-all `except` outside supervisor scope is permitted.
    Each supervisor catch-all MUST log via structlog (any
    `log.<method>(...)` call where `<method>` is one of `error`,
    `exception`, `warning`, `critical`, or `info`) AND return an
    integer exit code (any `return <int-literal>` is acceptable;
    the convention is `return 1` for the bug-class exit code).
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
_BIN_DIR = Path(".claude-plugin/scripts/bin")
_COMMANDS_DIR = Path(".claude-plugin/scripts/livespec/commands")
_DOCTOR_RUN_STATIC = Path(".claude-plugin/scripts/livespec/doctor/run_static.py")
_VENDOR_SUBSTR = "_vendor"
_PYCACHE_SUBSTR = "__pycache__"

_LOG_METHODS: frozenset[str] = frozenset(
    {"error", "exception", "warning", "critical", "info"},
)


def main() -> int:
    """Walk livespec/**; return 0 on pass, 1 on any violation."""
    repo_root = Path.cwd()
    failures: list[str] = []
    livespec_dir = repo_root / _LIVESPEC_DIR
    if livespec_dir.is_dir():
        for path in sorted(livespec_dir.rglob("*.py")):
            if _VENDOR_SUBSTR in path.parts or _PYCACHE_SUBSTR in path.parts:
                continue
            relative = path.relative_to(repo_root)
            for v in check_file(path=path, relative=relative):
                failures.append(f"{path}: {v}")
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("supervisor_discipline: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path, relative: Path) -> list[str]:
    """Return violation messages for `path`. Empty = pass.

    Only files inside `.claude-plugin/scripts/livespec/**` are checked
    here; bin/* is permitted to use `sys.exit` / `raise SystemExit`
    and is not a supervisor scope under this check.
    """
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    violations: list[str] = []
    _check_no_sys_exit(tree=tree, violations=violations)
    _check_no_raise_system_exit(tree=tree, violations=violations)
    supervisor_main = _find_supervisor_main(tree=tree, relative=relative)
    inside_ids = _catchall_ids_inside(supervisor=supervisor_main)
    _check_catchalls_outside_supervisor(
        tree=tree,
        inside_ids=inside_ids,
        violations=violations,
    )
    if supervisor_main is not None:
        _check_supervisor_body(
            supervisor=supervisor_main,
            violations=violations,
        )
    return violations


def _check_no_sys_exit(*, tree: ast.Module, violations: list[str]) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_sys_exit_call(node=node):
            violations.append(
                f"line {node.lineno}: sys.exit() forbidden outside bin/",
            )


def _check_no_raise_system_exit(*, tree: ast.Module, violations: list[str]) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and _is_system_exit_raise(node=node):
            violations.append(
                f"line {node.lineno}: raise SystemExit forbidden outside bin/",
            )


def _check_catchalls_outside_supervisor(
    *,
    tree: ast.Module,
    inside_ids: set[int],
    violations: list[str],
) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if not _is_catchall_handler(handler=node):
            continue
        if id(node) in inside_ids:
            continue
        violations.append(
            f"line {node.lineno}: catch-all `except` outside supervisor scope",
        )


def _check_supervisor_body(
    *,
    supervisor: ast.FunctionDef | ast.AsyncFunctionDef,
    violations: list[str],
) -> None:
    catchalls = [
        n for n in ast.walk(supervisor)
        if isinstance(n, ast.ExceptHandler) and _is_catchall_handler(handler=n)
    ]
    if not catchalls:
        violations.append(
            f"line {supervisor.lineno}: supervisor `main` lacks the required "
            f"catch-all `try/except Exception` bug-catcher",
        )
        return
    if len(catchalls) > 1:
        violations.append(
            f"line {supervisor.lineno}: supervisor `main` has {len(catchalls)} "
            f"catch-alls; exactly one permitted",
        )
        return
    handler = catchalls[0]
    if not _has_logging_call(handler=handler):
        violations.append(
            f"line {handler.lineno}: supervisor catch-all lacks a "
            f"`log.<method>(...)` logging call",
        )
    if not _has_int_return(handler=handler):
        violations.append(
            f"line {handler.lineno}: supervisor catch-all lacks a "
            f"`return <int>` exit-code emission",
        )


def _find_supervisor_main(
    *,
    tree: ast.Module,
    relative: Path,
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """Return the top-level `main` def iff `relative` is a supervisor module."""
    is_command = _is_under(relative=relative, scope=_COMMANDS_DIR)
    is_doctor_run_static = relative == _DOCTOR_RUN_STATIC
    if not (is_command or is_doctor_run_static):
        return None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == "main":
            return node
    return None


def _catchall_ids_inside(
    *,
    supervisor: ast.FunctionDef | ast.AsyncFunctionDef | None,
) -> set[int]:
    if supervisor is None:
        return set()
    return {
        id(n) for n in ast.walk(supervisor)
        if isinstance(n, ast.ExceptHandler) and _is_catchall_handler(handler=n)
    }


def _is_catchall_handler(*, handler: ast.ExceptHandler) -> bool:
    """A catch-all is `except:` (no type), `except Exception:`, or `except BaseException:`."""
    if handler.type is None:
        return True
    if isinstance(handler.type, ast.Name) and handler.type.id in {"Exception", "BaseException"}:
        return True
    return False


def _has_logging_call(*, handler: ast.ExceptHandler) -> bool:
    for node in ast.walk(handler):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in _LOG_METHODS:
            return True
    return False


def _has_int_return(*, handler: ast.ExceptHandler) -> bool:
    for node in ast.walk(handler):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, int):
            return True
    return False


def _is_sys_exit_call(*, node: ast.Call) -> bool:
    """True iff `node` is `sys.exit(...)`."""
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr != "exit":
        return False
    return isinstance(func.value, ast.Name) and func.value.id == "sys"


def _is_system_exit_raise(*, node: ast.Raise) -> bool:
    """True iff `node` is `raise SystemExit` or `raise SystemExit(...)`."""
    exc = node.exc
    if exc is None:
        return False
    if isinstance(exc, ast.Name) and exc.id == "SystemExit":
        return True
    if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name) and exc.func.id == "SystemExit":
        return True
    return False


def _is_under(*, relative: Path, scope: Path) -> bool:
    return (
        len(relative.parts) >= len(scope.parts) + 1
        and Path(*relative.parts[: len(scope.parts)]) == scope
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
