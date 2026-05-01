"""global_writes — bans `global`/`nonlocal` statements in `livespec/**`.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-global-writes` row), no module-level
mutable state writes from functions are permitted in
`livespec/**`. The `global` keyword is the canonical
declarator for writing module state from a function body and
is banned. The `nonlocal` keyword (writing enclosing-scope
state from nested functions) is banned for the same reason —
state flows down via parameters, up via return values, never
through scoped mutation.

The check walks every `.py` file under `.claude-plugin/
scripts/livespec/`, parses each via `ast`, and inspects every
`Global` and `Nonlocal` node. Any occurrence emits a structlog
ERROR with file path and line number; the script exits 1.

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


def _find_offenders(*, source: str) -> list[tuple[int, str]]:
    tree = ast.parse(source)
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Global):
            out.append((node.lineno, "global"))
        elif isinstance(node, ast.Nonlocal):
            out.append((node.lineno, "nonlocal"))
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
    log = structlog.get_logger("global_writes")
    cwd = Path.cwd()
    livespec_root = cwd / _LIVESPEC_TREE
    offenders: list[tuple[Path, int, str]] = []
    if livespec_root.is_dir():
        for py_file in sorted(livespec_root.rglob("*.py")):
            source = py_file.read_text(encoding="utf-8")
            for lineno, keyword in _find_offenders(source=source):
                offenders.append((py_file.relative_to(cwd), lineno, keyword))
    if offenders:
        for path, lineno, keyword in offenders:
            log.error(
                "module-level mutable writes from functions are banned",
                file=str(path),
                line=lineno,
                keyword=keyword,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
