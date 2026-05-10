"""implement — verify-and-close half of the gap-tied issue lifecycle.

Per `SPECIFICATION/non-functional-requirements.md` §Spec
§"Repo-local implementation workflow", `implement` orchestrates
the verify-and-close flow for issues whose gap-id has just been
removed by an authoring round of code edits. The actual code
edits (Red→Green test+impl, refactor, doc/config tweaks) are
NOT this script's responsibility — the agent or human author
makes those, then invokes this script to verify the gap is
gone and atomically close the bd issue with audit fields.

Two modes:

- **default**: emit `bd ready --json` to stdout (the queue of
  issues currently ready to be picked up). The agent uses this
  to choose the next leaf-level issue to work on.
- **--close LI-ID --gap GAP-NNNN --evidence "..."**:
    1. Run `dev-tooling/implementation/refresh_gaps.py` to
       regenerate `implementation-gaps/current.json`.
    2. Re-read current.json. Hard-refuse if the named gap-id
       still appears in `gaps[].id` (close MUST NOT happen
       until the gap is verifiably resolved per the
       close-with-audit-fields constraint).
    3. Compose the four-field audit notes string (gap id,
       evidence, run_id from `inspection.run_id`, timestamp
       from `generated_at`).
    4. `bd update LI-ID --notes <audit> --add-label resolution:fix`
    5. `bd close LI-ID --reason "<one-liner referencing run_id>"`.

The audit fields land in the issue's `notes` and a
`resolution:fix` label is attached. bd's auto-export then
mirrors the change into `.beads/issues.jsonl` for git tracking
in the next chore(beads) commit.

Output discipline: per spec, `print` and `sys.stderr.write`
are banned in dev-tooling/**. Diagnostics flow through
structlog (JSON to stderr); the vendored copy under
`.claude-plugin/scripts/_vendor/structlog` is added to
`sys.path` at module import time. The default-mode JSON is
written via a structlog `PrintLogger` to stdout to honour the
same rule.
"""

from __future__ import annotations

import argparse
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
_REFRESH_GAPS_REL = Path("dev-tooling") / "implementation" / "refresh_gaps.py"


def _resolve_bd() -> list[str] | None:
    """Locate the bd invocation argv-prefix. Prefers `mise exec -- bd ...`."""
    mise = shutil.which("mise")
    if mise is not None:
        return [mise, "exec", "--", "bd"]
    bd = shutil.which("bd")
    if bd is not None:
        return [bd]
    return None


def _run_refresh_gaps(*, cwd: Path) -> bool:
    """Invoke `dev-tooling/implementation/refresh_gaps.py`. True iff exit 0."""
    cmd = [sys.executable, str(cwd / _REFRESH_GAPS_REL)]
    try:
        result = subprocess.run(  # noqa: S603 — argv list, no shell.
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _bd_ready_issues(*, bd_argv: list[str]) -> list[object] | None:
    """Run `bd ready --json`; return the parsed list or None on failure."""
    cmd = [*bd_argv, "ready", "--json"]
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
    return parsed if isinstance(parsed, list) else None


def _bd_update_with_audit(*, bd_argv: list[str], li_id: str, notes: str) -> bool:
    """Run `bd update LI-ID --notes <audit> --add-label resolution:fix`."""
    cmd = [*bd_argv, "update", li_id, "--notes", notes, "--add-label", "resolution:fix"]
    try:
        result = subprocess.run(  # noqa: S603 — argv list, no shell.
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _bd_close_issue(*, bd_argv: list[str], li_id: str, reason: str) -> bool:
    """Run `bd close LI-ID --reason "..."`."""
    cmd = [*bd_argv, "close", li_id, "--reason", reason]
    try:
        result = subprocess.run(  # noqa: S603 — argv list, no shell.
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _load_current_report(*, cwd: Path) -> dict[str, object] | None:
    """Load implementation-gaps/current.json relative to cwd. None on missing/malformed."""
    report_path = cwd / _REPORT_PATH
    if not report_path.is_file():
        return None
    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _format_audit_notes(
    *,
    gap_id: str,
    evidence: str,
    run_id: str,
    generated_at: str,
) -> str:
    """Compose the four-field audit-notes string mandated by §Constraints."""
    return (
        f"Gap id: {gap_id}\n"
        f"Evidence: {evidence}\n"
        f"Verification run_id: {run_id}\n"
        f"Verification timestamp: {generated_at}"
    )


def _verify_gap_absent(
    *,
    gap_id: str,
    report: dict[str, object],
    log: object,
) -> bool:
    """Hard-refuse iff the gap-id still appears in report.gaps[].id."""
    gaps_field = report.get("gaps")
    if not isinstance(gaps_field, list):
        log.error("report's gaps field is not a list", path=str(_REPORT_PATH))
        return False
    for entry in gaps_field:
        if isinstance(entry, dict) and entry.get("id") == gap_id:
            log.error(
                "hard refusal: gap-id still present in current.json after refresh",
                gap_id=gap_id,
            )
            return False
    return True


def _run_close_mode(
    *,
    args: argparse.Namespace,
    bd_argv: list[str],
    log: object,
) -> int:
    """Execute --close: refresh, verify, compose audit, update + close. Returns process rc."""
    cwd = Path.cwd()
    if not _run_refresh_gaps(cwd=cwd):
        log.error("refresh-gaps subprocess failed; refusing to close", li_id=args.close)
        return 1
    report = _load_current_report(cwd=cwd)
    if report is None:
        log.error(
            "implementation-gap report missing or malformed after refresh",
            path=str(_REPORT_PATH),
        )
        return 1
    if not _verify_gap_absent(gap_id=args.gap, report=report, log=log):
        return 1
    inspection = report.get("inspection")
    run_id = inspection.get("run_id") if isinstance(inspection, dict) else None
    generated_at = report.get("generated_at")
    notes = _format_audit_notes(
        gap_id=args.gap,
        evidence=args.evidence,
        run_id=str(run_id) if isinstance(run_id, str) else "(missing)",
        generated_at=str(generated_at) if isinstance(generated_at, str) else "(missing)",
    )
    if not _bd_update_with_audit(bd_argv=bd_argv, li_id=args.close, notes=notes):
        log.error("bd update with audit notes failed", li_id=args.close)
        return 1
    reason = f"{args.gap} closed; refresh-gaps confirms (run_id {run_id})"
    if not _bd_close_issue(bd_argv=bd_argv, li_id=args.close, reason=reason):
        log.error("bd close failed", li_id=args.close)
        return 1
    log.info("issue closed with resolution:fix audit", li_id=args.close, gap_id=args.gap)
    return 0


def _parse_args(*, argv: list[str]) -> argparse.Namespace:
    """Parse implement.py's CLI arguments into a Namespace."""
    parser = argparse.ArgumentParser(
        prog="implement",
        description="List ready issues, or verify-and-close a completed gap-tied issue.",
    )
    _ = parser.add_argument(
        "--close",
        metavar="LI_ID",
        help="Close LI_ID after verifying the gap is gone. Requires --gap and --evidence.",
    )
    _ = parser.add_argument(
        "--gap",
        metavar="GAP_NNNN",
        help="The gap-id the close attests to having resolved.",
    )
    _ = parser.add_argument(
        "--evidence",
        metavar="STRING",
        help="Evidence-of-fix string for the audit notes (typically PR # + spec ref).",
    )
    return parser.parse_args(argv)


def main(*, argv: list[str] | None = None) -> int:
    """Implement entry point: list-ready (default) / --close (verify+close)."""
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("implement")
    stdout_logger = structlog.PrintLogger(file=sys.stdout)

    args = _parse_args(argv=argv if argv is not None else sys.argv[1:])

    bd_argv = _resolve_bd()
    if bd_argv is None:
        log.error("bd not on PATH (neither directly nor via mise)")
        return 1

    if args.close is None:
        ready = _bd_ready_issues(bd_argv=bd_argv)
        if ready is None:
            log.error("bd ready --json failed")
            return 1
        stdout_logger.msg(json.dumps(ready))
        return 0

    if args.gap is None or args.evidence is None:
        log.error("--close requires both --gap and --evidence", li_id=args.close)
        return 1

    return _run_close_mode(args=args, bd_argv=bd_argv, log=log)


if __name__ == "__main__":
    raise SystemExit(main())
