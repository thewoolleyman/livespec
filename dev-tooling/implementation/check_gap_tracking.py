"""check_gap_tracking — every current gap has exactly one beads issue.

Per `SPECIFICATION/non-functional-requirements.md` §Constraints
§"Beads invariants" #2 ("Gap-id ↔ beads-label exactly-once
invariant"): every gap id appearing in
`implementation-gaps/current.json` MUST correspond to exactly one
beads issue across all statuses. Closed beads issues MAY retain
labels for retired gap ids that no longer appear in current.json
(the invariant is one-way from current gaps to tracked issues).
Zero matching issues fails; two-or-more matching issues fail.

Implementation: load current.json, list every gap.id, then ask bd
for the count of issues carrying the corresponding
`gap-id:gap-NNNN` label across all statuses. Surface every
violation through structlog. Exit 0 when every current gap has
exactly one issue; exit 1 otherwise (or when the report or bd
itself is unavailable).

Output discipline: per spec, `print` and `sys.stderr.write` are
banned in dev-tooling/**. Diagnostics flow through structlog
(JSON to stderr); the vendored copy under
`.claude-plugin/scripts/_vendor/structlog` is added to `sys.path`
at module import time.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_REPORT_PATH = Path("implementation-gaps") / "current.json"
_GAP_LABEL_PREFIX = "gap-id:"


def _resolve_bd() -> list[str] | None:
    """Locate the `bd` invocation prefix.

    Prefer `mise exec -- bd ...` over plain `bd` so the call works
    in the same shells where the bd binary is mise-pinned (the
    livespec convention; see .mise.toml). Returns None if neither
    is available.

    The return type is `list[str] | None` — when present, the list is
    the argv-prefix to feed `subprocess.run` (e.g.
    `["mise", "exec", "--", "bd"]` or `["bd"]`).
    """
    mise = shutil.which("mise")
    if mise is not None:
        return [mise, "exec", "--", "bd"]
    bd = shutil.which("bd")
    if bd is not None:
        return [bd]
    return None


def _load_current_report() -> dict[str, object] | None:
    """Load implementation-gaps/current.json. Returns None if missing or malformed."""
    if not _REPORT_PATH.is_file():
        return None
    try:
        return json.loads(_REPORT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _bd_issues_with_label(*, bd_argv: list[str], label: str) -> list[dict[str, object]] | None:
    """Query bd for ALL issues (every status) carrying the given label.

    `--all` opts in to closed issues alongside open / in-progress /
    blocked / deferred — required by the invariant ("across all
    statuses"). `--label` filters AND-style; passing one label is
    therefore an exact-match-on-that-label query.

    Returns the parsed JSON array or None on failure (subprocess
    error, malformed JSON, etc.). The caller distinguishes "found 0
    issues" (a real result, returned as `[]`) from "could not query"
    (returned as None).
    """
    cmd = [*bd_argv, "list", "--all", "--label", label, "--json"]
    try:
        result = subprocess.run(  # noqa: S603 — argv list, no shell.
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    stdout = result.stdout.strip()
    if stdout == "":
        return []
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, list):
        return None
    return parsed


def _gap_entry_satisfies_invariant(
    *,
    entry: object,
    bd_argv: list[str],
    log: object,
) -> bool:
    """Check that one gaps[] entry has exactly one tracking beads issue.

    Returns True when the entry has exactly one matching beads issue
    across all statuses; False on any violation (malformed entry,
    bd query failure, zero matches, two-or-more matches). Each
    violation is logged via the structlog logger passed in.

    The `log` parameter is typed as `object` because structlog's
    BoundLogger isn't formally typed in the vendored copy; calling
    .error / .warning on it works at runtime but pyright cannot
    verify the call signatures (matches the rest of dev-tooling/).
    """
    if not isinstance(entry, dict):
        log.error("gaps[] entry is not an object; run check-gaps first")
        return False
    gap_id = entry.get("id")
    if not isinstance(gap_id, str):
        log.error("gaps[] entry missing or non-string id field; run check-gaps first")
        return False
    label = f"{_GAP_LABEL_PREFIX}{gap_id}"
    issues = _bd_issues_with_label(bd_argv=bd_argv, label=label)
    if issues is None:
        log.error("bd query failed", gap_id=gap_id, label=label)
        return False
    match_count = len(issues)
    if match_count == 0:
        log.error(
            "current gap has no tracking beads issue (run /livespec-implementation:plan)",
            gap_id=gap_id,
            label=label,
        )
        return False
    if match_count > 1:
        ids = [issue.get("id") for issue in issues if isinstance(issue, dict)]
        log.error(
            "current gap has multiple tracking beads issues (close duplicates)",
            gap_id=gap_id,
            label=label,
            issue_count=match_count,
            issue_ids=ids,
        )
        return False
    return True


def main() -> int:
    """Enforce the gap-id ↔ beads-label exactly-once invariant.

    Steps:
    1. Configure structlog for JSON-on-stderr.
    2. Resolve the bd invocation prefix.
    3. Load implementation-gaps/current.json (no report = nothing
       to enforce; treat as a clean pass with a warning, since the
       invariant is one-way from current gaps and an empty report
       has no current gaps).
    4. For each gap, query bd for the issue-count carrying the
       matching gap-id label. Track violations.
    5. Exit 0 when every gap.id has exactly one matching issue;
       exit 1 on any zero-match or duplicate-match.
    """
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("check_gap_tracking")

    bd_argv = _resolve_bd()
    if bd_argv is None:
        log.error(
            "bd not on PATH (neither directly nor via mise)",
            hint="run `mise install` (.mise.toml pins github:gastownhall/beads@1.0.3)",
        )
        return 1

    report = _load_current_report()
    if report is None:
        log.warning(
            "implementation-gap report missing or malformed; nothing to enforce",
            path=str(_REPORT_PATH),
            hint="run `just implementation::refresh-gaps` to (re)generate",
        )
        return 0

    gaps_field = report.get("gaps")
    if not isinstance(gaps_field, list):
        log.error(
            "report's gaps field is not a list; run check-gaps first",
            path=str(_REPORT_PATH),
        )
        return 1

    violations = sum(
        1
        for entry in gaps_field
        if not _gap_entry_satisfies_invariant(
            entry=entry,
            bd_argv=bd_argv,
            log=log,
        )
    )

    if violations > 0:
        log.error("gap-tracking invariant violated", violation_count=violations)
        return 1
    log.info(
        "gap-tracking invariant holds",
        gap_count=len(gaps_field),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
