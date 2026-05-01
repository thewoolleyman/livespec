"""heading_coverage — every spec `##` heading has a coverage entry.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-heading-coverage` row), every `##`
heading in every spec tree (main `SPECIFICATION/` + each
sub-spec under `SPECIFICATION/templates/<name>/`) MUST have
a corresponding entry in `tests/heading-coverage.json` whose
`spec_root` field matches the heading's tree. Tolerates an
empty `[]` array pre-Phase-6, before any spec tree exists;
from Phase 6 onward emptiness is a failure if any spec tree
exists.

The check walks the `SPECIFICATION/` directory tree (if
present), reads every `.md` file, extracts every `##`
heading (stripped trailing whitespace), and verifies that
each (heading, spec_root) pair has a matching entry in
`tests/heading-coverage.json`. The `spec_root` for each
heading is the file's containing directory relative to the
repo cwd (e.g., `SPECIFICATION` for the main tree,
`SPECIFICATION/templates/minimal` for a sub-spec).

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


_SPEC_ROOT = Path("SPECIFICATION")
_COVERAGE_PATH = Path("tests") / "heading-coverage.json"


def _extract_h2_headings(*, source: str) -> list[str]:
    out: list[str] = []
    for raw in source.splitlines():
        stripped = raw.rstrip()
        if stripped.startswith("## ") and not stripped.startswith("### "):
            out.append(stripped)
    return out


def _coverage_index(*, entries: list[dict[str, object]]) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for entry in entries:
        heading = entry.get("heading")
        spec_root = entry.get("spec_root")
        if isinstance(heading, str) and isinstance(spec_root, str):
            out.add((heading, spec_root))
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
    log = structlog.get_logger("heading_coverage")
    cwd = Path.cwd()
    coverage_path = cwd / _COVERAGE_PATH
    coverage_entries: list[dict[str, object]] = []
    if coverage_path.is_file():
        text = coverage_path.read_text(encoding="utf-8")
        parsed = json.loads(text)
        if isinstance(parsed, list):
            coverage_entries = [e for e in parsed if isinstance(e, dict)]
    index = _coverage_index(entries=coverage_entries)
    spec_root = cwd / _SPEC_ROOT
    if not spec_root.is_dir():
        return 0
    offenders: list[tuple[str, str]] = []
    for md_file in sorted(spec_root.rglob("*.md")):
        rel_dir = md_file.parent.relative_to(cwd)
        source = md_file.read_text(encoding="utf-8")
        for heading in _extract_h2_headings(source=source):
            key = (heading, str(rel_dir))
            if key not in index:
                offenders.append(key)
    if offenders:
        for heading, spec_root_str in offenders:
            log.error(
                "spec heading missing coverage entry",
                heading=heading,
                spec_root=spec_root_str,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
