"""no_raise_outside_io — domain-error raises confined to `io/**` and `errors.py`.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-no-raise-outside-io` row), raising
of `LivespecError` subclasses (domain errors) at runtime is
restricted to `livespec/io/**` and `livespec/errors.py`.
Pure layers (parse/, validate/, commands/, doctor/, schemas/)
return `Failure(LivespecError(...))` on the ROP railway
instead. Bug-class exceptions (TypeError, ValueError,
NotImplementedError, AssertionError, etc.) are permitted
anywhere — they propagate to the supervisor's bug-catcher.

The known domain-error class names that count as
`LivespecError` subclasses (the closed hierarchy enumerated
by `errors.py`'s `__all__`): `LivespecError`, `UsageError`,
`PreconditionError`, `ValidationError`. Subsequent additions
to the hierarchy widen this set as consumer pressure surfaces
new failure categories.

The check walks every `.py` file under `.claude-plugin/
scripts/livespec/`, parses each via `ast`, and inspects every
`Raise` node whose exception unparses to one of the
domain-error names (or a parameterized call thereof). Files
under `io/` and the single `errors.py` file are exempt.

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
_DOMAIN_ERROR_NAMES = frozenset(
    {"LivespecError", "UsageError", "PreconditionError", "ValidationError"}
)
_IO_TREE = Path(".claude-plugin") / "scripts" / "livespec" / "io"
_ERRORS_FILE = Path(".claude-plugin") / "scripts" / "livespec" / "errors.py"


def _is_exempt(*, rel_path: Path) -> bool:
    if rel_path == _ERRORS_FILE:
        return True
    return _IO_TREE in rel_path.parents


def _find_domain_raises(*, source: str) -> list[tuple[int, str]]:
    tree = ast.parse(source)
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise) or node.exc is None:
            continue
        rendered = ast.unparse(node.exc)
        head = rendered.split("(", maxsplit=1)[0]
        if head in _DOMAIN_ERROR_NAMES:
            out.append((node.lineno, head))
    return out


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
    offenders: list[tuple[Path, int, str]] = []
    if livespec_root.is_dir():
        for py_file in sorted(livespec_root.rglob("*.py")):
            rel = py_file.relative_to(cwd)
            if _is_exempt(rel_path=rel):
                continue
            source = py_file.read_text(encoding="utf-8")
            for lineno, error_name in _find_domain_raises(source=source):
                offenders.append((rel, lineno, error_name))
    if offenders:
        for path, lineno, error_name in offenders:
            log.error(
                "domain-error raise outside `io/`/`errors.py` is banned",
                file=str(path),
                line=lineno,
                error=error_name,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
