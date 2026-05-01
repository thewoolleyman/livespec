"""no_todo_registry — `tests/heading-coverage.json` rejects any `test: "TODO"` entry.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-no-todo-registry` row), no entry in
`tests/heading-coverage.json` may have `test: "TODO"`.
Release-gate only — paired with `check-mutation` on the
release-tag CI workflow. Ensures every release ships with
full rule-test coverage.

The check loads the JSON file (strict JSON, not JSONC) and
walks the array. Any entry whose `test` field equals the
literal string `"TODO"` surfaces. If the file is missing or
contains only non-TODO entries, the check exits 0.

Output discipline: per spec lines 1738-1762, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_COVERAGE_PATH = Path("tests") / "heading-coverage.json"


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("no_todo_registry")
    cwd = Path.cwd()
    coverage_path = cwd / _COVERAGE_PATH
    if not coverage_path.is_file():
        return 0
    text = coverage_path.read_text(encoding="utf-8")
    parsed = json.loads(text)
    offenders: list[dict[str, object]] = []
    if isinstance(parsed, list):
        for entry in parsed:
            if isinstance(entry, dict) and entry.get("test") == "TODO":
                offenders.append(entry)
    if offenders:
        for entry in offenders:
            log.error(
                "heading-coverage.json entry has `test: \"TODO\"` (release-gate violation)",
                heading=entry.get("heading"),
                spec_root=entry.get("spec_root"),
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
