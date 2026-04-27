"""no_except_outside_io: restrict `try/except` clauses outside io/**.

Per python-skill-script-style-requirements.md line 1805 and lines
561-566:

"Catching exceptions outside `io/**` is restricted to ONE call
site: the outermost supervisor's top-level `try/except Exception`
bug-catcher."

Concretely:

- Files under `.claude-plugin/scripts/livespec/io/**` are exempt
  (every `try/except` there is permitted; io/** is the impure
  layer that wraps domain-meaningful third-party exceptions via
  `@impure_safe(exceptions=(...))` plus narrow per-call
  `try/except` for typed conversions).
- Outside io/**, the only permitted `except` is the catch-all
  `except Exception` (or `BaseException`, or bare `except:`)
  inside the top-level `def main(...)` of:
  - `.claude-plugin/scripts/livespec/commands/*.py`, and
  - `.claude-plugin/scripts/livespec/doctor/run_static.py`.
- Specific catches (e.g., `except FileNotFoundError:`) outside
  io/** are forbidden — third-party domain exceptions are
  converted via `@safe(exceptions=(ExcType,))` /
  `@impure_safe(exceptions=(ExcType,))` per §"Error Handling
  Discipline" lines 545-560, not via raw `try/except`.

The check enumerates supervisor `main()` definitions per file and
matches each `ExceptHandler` against the supervisor scope + catch-all
shape.
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
_IO_DIR = Path(".claude-plugin/scripts/livespec/io")
_COMMANDS_DIR = Path(".claude-plugin/scripts/livespec/commands")
_DOCTOR_RUN_STATIC = Path(".claude-plugin/scripts/livespec/doctor/run_static.py")
_VENDOR_SUBSTR = "_vendor"
_PYCACHE_SUBSTR = "__pycache__"


def main() -> int:
    """Walk livespec/** outside io/**; return 0 on pass, 1 on any violation."""
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
        log.error("no_except_outside_io: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path, relative: Path) -> list[str]:
    """Return violation messages for `path`. Empty = pass."""
    if _is_under_io(relative=relative):
        return []
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    supervisor_main = _find_supervisor_main(tree=tree, relative=relative)
    permitted_ids = _permitted_handler_ids(supervisor=supervisor_main)
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if id(node) in permitted_ids:
            continue
        violations.append(
            f"line {node.lineno}: `except {_handler_type_repr(handler=node)}` "
            f"outside io/** and outside the supervisor catch-all is forbidden",
        )
    return violations


def _find_supervisor_main(
    *,
    tree: ast.Module,
    relative: Path,
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    is_command = (
        len(relative.parts) >= len(_COMMANDS_DIR.parts) + 1
        and Path(*relative.parts[: len(_COMMANDS_DIR.parts)]) == _COMMANDS_DIR
    )
    is_doctor = relative == _DOCTOR_RUN_STATIC
    if not (is_command or is_doctor):
        return None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == "main":
            return node
    return None


def _permitted_handler_ids(
    *,
    supervisor: ast.FunctionDef | ast.AsyncFunctionDef | None,
) -> set[int]:
    """Catch-all handlers inside the supervisor main are permitted."""
    if supervisor is None:
        return set()
    return {
        id(n)
        for n in ast.walk(supervisor)
        if isinstance(n, ast.ExceptHandler) and _is_catchall_handler(handler=n)
    }


def _is_catchall_handler(*, handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return True
    return isinstance(handler.type, ast.Name) and handler.type.id in {
        "Exception",
        "BaseException",
    }


def _is_under_io(*, relative: Path) -> bool:
    return (
        len(relative.parts) >= len(_IO_DIR.parts) + 1
        and Path(*relative.parts[: len(_IO_DIR.parts)]) == _IO_DIR
    )


def _handler_type_repr(*, handler: ast.ExceptHandler) -> str:
    if handler.type is None:
        return ""
    return ast.unparse(handler.type)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
