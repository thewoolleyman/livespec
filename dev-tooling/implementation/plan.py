"""plan — manage beads issues that mirror current implementation gaps.

Per `SPECIFICATION/non-functional-requirements.md` §Spec
§"Repo-local implementation workflow", `plan` reads
`implementation-gaps/current.json`, identifies gap ids that
lack a tracking beads issue (the "untracked" set), surfaces
them via stdout, and on demand calls `bd create` + `bd dep
add` to file each one.

Three modes (chosen via CLI flag — default is list-untracked):

- **default / list mode**: emit a JSON array of untracked gap
  entries to stdout. Read-only with respect to `bd`.
- **--create gap-NNNN [gap-NNNN ...]**: file one beads issue
  per named gap id. Honours each gap's `depends_on` field by
  calling `bd dep add` for every already-tracked predecessor.
- **--create-all**: equivalent to `--create` against every
  untracked gap in the report.

Already-tracked gaps are silently skipped in --create mode so
the workflow stays idempotent.

Output discipline: per spec, `print` and `sys.stderr.write`
are banned in dev-tooling/**. Diagnostics flow through
structlog (JSON to stderr); the sibling `_plan_bd` module owns
all subprocess calls to keep this file under the 250 LLOC
hard ceiling. The list-mode JSON is written to stdout via the
structlog `PrintLogger` factory to honour the no-print rule.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import _plan_bd  # noqa: E402  — sibling private module on script-dir path
import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_REPORT_PATH = Path("implementation-gaps") / "current.json"


# Re-export `_resolve_bd` and `shutil`/`subprocess` so tests that monkeypatch
# `plan_module.shutil` / `plan_module.subprocess` continue to interpose at
# the symbols the original single-file design exposed. Keeps the test fixture
# stable across the cycle 4c-style sibling-module split.
def _resolve_bd() -> list[str] | None:
    """Locate the bd invocation argv-prefix. See `_plan_bd.resolve_bd`."""
    return _plan_bd.resolve_bd()


def _load_current_report() -> dict[str, object] | None:
    """Load implementation-gaps/current.json. None when missing or malformed."""
    if not _REPORT_PATH.is_file():
        return None
    try:
        return json.loads(_REPORT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _untracked_gaps(*, gaps: list[object], bd_argv: list[str]) -> list[dict[str, object]]:
    """Filter gaps to only those without any tracking beads issue."""
    out: list[dict[str, object]] = []
    for entry in gaps:
        if not isinstance(entry, dict):
            continue
        gap_id = entry.get("id")
        if not isinstance(gap_id, str):
            continue
        if _plan_bd.existing_tracking_issue(gap_id=gap_id, bd_argv=bd_argv) is None:
            out.append(entry)
    return out


def _wire_dep_edges(
    *,
    new_id: str,
    depends_on: list[object],
    bd_argv: list[str],
    log: object,
    gap_id: str,
) -> bool:
    """For each predecessor gap-id in depends_on, file a `bd dep add` edge from new_id."""
    for predecessor_gap_id in depends_on:
        if not isinstance(predecessor_gap_id, str):
            continue
        predecessor = _plan_bd.existing_tracking_issue(
            gap_id=predecessor_gap_id,
            bd_argv=bd_argv,
        )
        if predecessor is None:
            log.warning(
                "depends_on predecessor has no tracking issue yet; skipping dep edge",
                gap_id=gap_id,
                predecessor_gap_id=predecessor_gap_id,
            )
            continue
        predecessor_id = predecessor.get("id")
        if not isinstance(predecessor_id, str):
            continue
        if not _plan_bd.add_dep_edge(
            blocked_id=new_id,
            blocker_id=predecessor_id,
            bd_argv=bd_argv,
        ):
            log.error("bd dep add failed", blocked_id=new_id, blocker_id=predecessor_id)
            return False
        log.info("added dep edge", blocked_id=new_id, blocker_id=predecessor_id)
    return True


def _process_create_target(
    *,
    gap: dict[str, object],
    bd_argv: list[str],
    log: object,
) -> bool:
    """Create one gap-tied issue; wire dep edges for already-tracked predecessors."""
    gap_id = str(gap["id"])
    if _plan_bd.existing_tracking_issue(gap_id=gap_id, bd_argv=bd_argv) is not None:
        log.info("gap already tracked; skipping", gap_id=gap_id)
        return True
    new_id = _plan_bd.create_gap_issue(gap=gap, bd_argv=bd_argv)
    if new_id is None:
        log.error("bd create failed", gap_id=gap_id)
        return False
    log.info("created tracking issue", gap_id=gap_id, issue_id=new_id)
    depends_on = gap.get("depends_on")
    if not isinstance(depends_on, list):
        return True
    return _wire_dep_edges(
        new_id=new_id,
        depends_on=depends_on,
        bd_argv=bd_argv,
        log=log,
        gap_id=gap_id,
    )


def _parse_args(*, argv: list[str]) -> argparse.Namespace:
    """Parse plan.py's CLI arguments into a Namespace."""
    parser = argparse.ArgumentParser(
        prog="plan",
        description="Manage beads issues that mirror current implementation gaps.",
    )
    group = parser.add_mutually_exclusive_group()
    _ = group.add_argument("--create", nargs="+", metavar="GAP_ID")
    _ = group.add_argument("--create-all", action="store_true")
    return parser.parse_args(argv)


def _resolve_create_targets(
    *,
    args: argparse.Namespace,
    gaps_field: list[object],
    bd_argv: list[str],
    log: object,
) -> list[dict[str, object]] | None:
    """Resolve gap entries for --create/--create-all. None signals failure (already logged)."""
    if args.create_all:
        return _untracked_gaps(gaps=gaps_field, bd_argv=bd_argv)
    by_id: dict[str, dict[str, object]] = {
        str(entry["id"]): entry
        for entry in gaps_field
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    targets: list[dict[str, object]] = []
    for gap_id in args.create:
        entry = by_id.get(gap_id)
        if entry is None:
            log.error("--create target not found in current.json", gap_id=gap_id)
            return None
        targets.append(entry)
    return targets


def _run_create_mode(
    *,
    args: argparse.Namespace,
    gaps_field: list[object],
    bd_argv: list[str],
    log: object,
) -> int:
    """Execute --create / --create-all, returning the process exit status."""
    targets = _resolve_create_targets(
        args=args,
        gaps_field=gaps_field,
        bd_argv=bd_argv,
        log=log,
    )
    if targets is None:
        return 1
    failures = sum(
        1 for gap in targets if not _process_create_target(gap=gap, bd_argv=bd_argv, log=log)
    )
    if failures > 0:
        log.error("plan completed with errors", failure_count=failures)
        return 1
    log.info("plan completed cleanly", processed=len(targets))
    return 0


def main(*, argv: list[str] | None = None) -> int:
    """Plan entry point: list-untracked / --create / --create-all."""
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("plan")
    stdout_logger = structlog.PrintLogger(file=sys.stdout)

    args = _parse_args(argv=argv if argv is not None else sys.argv[1:])

    bd_argv = _resolve_bd()
    if bd_argv is None:
        log.error("bd not on PATH (neither directly nor via mise)")
        return 1

    report = _load_current_report()
    if report is None:
        log.error(
            "implementation-gap report missing or malformed",
            path=str(_REPORT_PATH),
        )
        return 1

    gaps_field = report.get("gaps")
    if not isinstance(gaps_field, list):
        log.error("report's gaps field is not a list", path=str(_REPORT_PATH))
        return 1

    if args.create is None and not args.create_all:
        untracked = _untracked_gaps(gaps=gaps_field, bd_argv=bd_argv)
        stdout_logger.msg(json.dumps(untracked))
        return 0

    return _run_create_mode(args=args, gaps_field=gaps_field, bd_argv=bd_argv, log=log)


if __name__ == "__main__":
    raise SystemExit(main())
