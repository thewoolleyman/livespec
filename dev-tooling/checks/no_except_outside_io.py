"""no_except_outside_io — `try/except` confined to `io/` and supervisor bug-catchers.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-no-except-outside-io` row), catching
exceptions (`try/except`) outside `livespec/io/**` is
permitted only in supervisor bug-catchers — the top-level
`try/except Exception` block inside `main()` of
`livespec/commands/*.py` and `livespec/doctor/run_static.py`.
Anywhere else under `livespec/**`, `try/except` is banned —
pure layers handle expected failures via the ROP railway
(`Result.bind`, `Result.alt`).

The check walks every `.py` file under `.claude-plugin/
scripts/livespec/`, parses each via `ast`, and inspects every
`Try` node (the AST representation of a `try/except`
statement). Files under `io/` are wholesale exempt. For files
under `commands/` and `doctor/run_static.py`, only the
direct-child `Try` nodes inside the `main()` function body
are exempt — `try/except` in helper functions remains banned.

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
_IO_TREE = Path(".claude-plugin") / "scripts" / "livespec" / "io"
_COMMANDS_TREE = Path(".claude-plugin") / "scripts" / "livespec" / "commands"
_DOCTOR_RUN_STATIC = (
    Path(".claude-plugin") / "scripts" / "livespec" / "doctor" / "run_static.py"
)


def _is_supervisor_main_file(*, rel_path: Path) -> bool:
    if rel_path == _DOCTOR_RUN_STATIC:
        return True
    return _COMMANDS_TREE in rel_path.parents


def _supervisor_main_try_lines(*, tree: ast.Module) -> set[int]:
    """Return line numbers of `Try` nodes that are direct children of `main()`'s body."""
    out: set[int] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            for stmt in node.body:
                if isinstance(stmt, ast.Try):
                    out.add(stmt.lineno)
    return out


def _find_offending_try_lines(*, source: str, exempt_main_try: set[int]) -> list[int]:
    tree = ast.parse(source)
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Try) and node.lineno not in exempt_main_try
    ]


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
    offenders: list[tuple[Path, int]] = []
    if livespec_root.is_dir():
        for py_file in sorted(livespec_root.rglob("*.py")):
            rel = py_file.relative_to(cwd)
            if _IO_TREE in rel.parents:
                continue
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
            exempt = (
                _supervisor_main_try_lines(tree=tree)
                if _is_supervisor_main_file(rel_path=rel)
                else set()
            )
            for lineno in _find_offending_try_lines(
                source=source, exempt_main_try=exempt
            ):
                offenders.append((rel, lineno))
    if offenders:
        for path, lineno in offenders:
            log.error(
                "`try/except` outside io/ + supervisor bug-catcher is banned",
                file=str(path),
                line=lineno,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
