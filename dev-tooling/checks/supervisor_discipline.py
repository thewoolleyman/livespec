"""supervisor_discipline — `sys.exit`/`raise SystemExit` confined to `bin/*.py`.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-supervisor-discipline` row),
`sys.exit(...)` calls and `raise SystemExit(...)` statements
are permitted only in `.claude-plugin/scripts/bin/*.py`
(including `_bootstrap.py`). Anywhere else under
`.claude-plugin/scripts/livespec/**`, both forms are banned —
process termination flows through the supervisor-at-the-edge
surface only; livespec modules return `Result`/`IOResult`
values that the supervisor unpacks into an exit code.

The check walks every `.py` file under `.claude-plugin/
scripts/livespec/`, parses each via `ast`, and inspects:

- Every `Call` node whose function unparses to `sys.exit`.
- Every `Raise` node whose exception is `SystemExit(...)` or
  `SystemExit` (bare).

Any match emits a structlog ERROR carrying the file path,
line number, and termination form; the script exits 1. With
no violations, exits 0.

Output discipline: per spec lines 1738-1762, `print` (T20) and
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


def _find_termination_sites(*, source: str) -> list[tuple[int, str]]:
    tree = ast.parse(source)
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and ast.unparse(node.func) == "sys.exit":
            out.append((node.lineno, "sys.exit"))
        elif (
            isinstance(node, ast.Raise)
            and node.exc is not None
            and ast.unparse(node.exc).split("(", maxsplit=1)[0] == "SystemExit"
        ):
            out.append((node.lineno, "raise SystemExit"))
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
    log = structlog.get_logger("supervisor_discipline")
    cwd = Path.cwd()
    livespec_root = cwd / _LIVESPEC_TREE
    offenders: list[tuple[Path, int, str]] = []
    if livespec_root.is_dir():
        for py_file in sorted(livespec_root.rglob("*.py")):
            source = py_file.read_text(encoding="utf-8")
            for lineno, form in _find_termination_sites(source=source):
                offenders.append((py_file.relative_to(cwd), lineno, form))
    if offenders:
        for path, lineno, form in offenders:
            log.error(
                "process termination outside `bin/` is banned",
                file=str(path),
                line=lineno,
                form=form,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
