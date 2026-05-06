"""per_file_coverage — every covered file at 100% line+branch coverage (v033 D2).

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-coverage` row, rewritten at v033) and
the v033 D2 revision file at `brainstorming/approach-2-nlspec-
based/history/v033/proposed_changes/critique-fix-v032-revision.md`,
the authoritative coverage gate is **per-file** at 100% line
AND 100% branch — not just total. The existing
`[tool.coverage.report].fail_under = 100` setting in
pyproject.toml is preserved as a belt-and-braces total guard,
but the per-file gate is what fails first when any single
covered file slips below threshold.

Invocation context: this script runs AFTER `pytest --cov
--cov-branch` has produced a combined `.coverage` data file in
the repo's cwd. The justfile's `check-coverage` recipe
sequences pytest then this script. The script reads the
`.coverage` file via the `coverage` Python API (a uv-managed
dependency, NOT a vendored lib — `coverage` itself isn't part
of the shipped livespec runtime, only the dev-tooling test
infrastructure).

Cycle 1 implements the missing-line-coverage rejection: walks
all measured files, generates a JSON report via
`Coverage.json_report(outfile="-")` redirected to an in-memory
buffer, parses the JSON, and fails the first time any file's
`summary.percent_covered` is below 100%. Subsequent cycles
will tighten to also cover `summary.percent_covered_branches`
and to handle the no-data case explicitly.

Output discipline: per spec, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import
time.
"""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.
from coverage import Coverage  # noqa: E402  — uv-managed dep, available post-vendor-path-insert.

__all__: list[str] = []


# Per v033 D2: every covered file must be at 100% line coverage.
# The threshold is policy-set at 100.0 (no carveout); this constant
# names the policy threshold for use in the offender-detection loop.
_FULL_COVERAGE_PCT: float = 100.0


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("per_file_coverage")
    cwd = Path.cwd()
    coverage_file = cwd / ".coverage"
    if not coverage_file.is_file():
        log.error("no coverage data found", expected_path=str(coverage_file))
        return 1

    cov = Coverage(data_file=str(coverage_file))
    cov.load()

    buf = io.StringIO()
    with redirect_stdout(buf):
        cov.json_report(outfile="-")
    report = json.loads(buf.getvalue())

    offenders: list[tuple[str, dict[str, object]]] = []
    for fname, file_info in sorted(report["files"].items()):
        summary = file_info["summary"]
        line_pct = summary.get("percent_covered", _FULL_COVERAGE_PCT)
        if line_pct < _FULL_COVERAGE_PCT:
            offenders.append((fname, summary))

    if offenders:
        for fname, summary in offenders:
            log.error(
                "file below 100% coverage",
                file=fname,
                line_percent=summary.get("percent_covered"),
                missing_lines=summary.get("missing_lines"),
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
