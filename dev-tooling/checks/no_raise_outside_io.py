"""no_raise_outside_io — `raise LivespecError(...)` only in `io/**` and `errors.py`.

Per `python-skill-script-style-requirements.md` line 2080:

    AST: raising of `LivespecError` subclasses (domain errors)
    at runtime restricted to `io/**` and `errors.py`. Raising
    bug-class exceptions (TypeError, NotImplementedError,
    AssertionError, etc.) permitted anywhere. **Raise-site
    enforcement is the sole enforcement point for the
    raise-discipline (v017 Q3 retraction of the v012 L15a
    import-surface delegation).**

Cycle 39 pins the canonical violation: a literal
`raise LivespecError(...)` (the base class name) inside any
livespec module that is NOT under `livespec/io/**` and NOT
`livespec/errors.py` is rejected.

Bug-class exceptions are distinguished by name. Python builtins
that are NOT `LivespecError` (TypeError, NotImplementedError,
AssertionError, RuntimeError, ValueError, etc.) are bug
markers; the check accepts them anywhere.

Future cycles will extend the check to recognize specific
`LivespecError` SUBclass names (UsageError, PreconditionError,
ValidationError, RateLimitError, etc.) once those land in
livespec/errors.py. The simplest possible cycle-39 impl
matches the literal name `LivespecError`; a subsequent cycle
will broaden the name set as the LivespecError hierarchy
materializes.
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
_IO_SUBTREE = _LIVESPEC_TREE / "io"
_ERRORS_FILE = _LIVESPEC_TREE / "errors.py"
_LIVESPEC_ERROR_NAMES = frozenset({"LivespecError"})


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
        if not isinstance(node, ast.Raise):
            continue
        name = _raise_target_name(node=node)
        if name is not None and name in _LIVESPEC_ERROR_NAMES:
            offenders.append((node.lineno, name))
    return offenders


def _is_exempt_path(*, py_file: Path, livespec_root: Path) -> bool:
    relative = py_file.relative_to(livespec_root)
    if relative == Path("errors.py"):
        return True
    return relative.parts[:1] == ("io",)


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
    log = structlog.get_logger("no_raise_outside_io")
    cwd = Path.cwd()
    livespec_root = cwd / _LIVESPEC_TREE
    if not livespec_root.is_dir():
        return 0
    found_any = False
    for py_file in _iter_python_files(root=livespec_root):
        if _is_exempt_path(py_file=py_file, livespec_root=livespec_root):
            continue
        source = py_file.read_text(encoding="utf-8")
        module_ast = ast.parse(source, filename=str(py_file))
        for lineno, exc_name in _find_violations(tree=module_ast):
            log.error(
                "LivespecError raise outside io/**",
                path=str(py_file.relative_to(cwd)),
                line=lineno,
                exception=exc_name,
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
