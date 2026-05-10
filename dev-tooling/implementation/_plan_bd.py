"""bd interaction helpers for plan.py.

Extracted out of plan.py to keep the orchestration module under the
250 LLOC hard ceiling. Every function here performs (or sets up) a
subprocess call to the `bd` (beads) CLI; nothing here knows about
the gap-report shape or argparse plumbing.

Output discipline note: this module imports nothing that emits to
stdout/stderr directly. All diagnostics flow through the structlog
logger that plan.py passes in.
"""

from __future__ import annotations

import json
import shutil
import subprocess

__all__: list[str] = []


_GAP_LABEL_PREFIX = "gap-id:"


def resolve_bd() -> list[str] | None:
    """Locate the bd invocation argv-prefix. Prefers `mise exec -- bd ...`."""
    mise = shutil.which("mise")
    if mise is not None:
        return [mise, "exec", "--", "bd"]
    bd = shutil.which("bd")
    if bd is not None:
        return [bd]
    return None


def _run_bd(*, bd_argv: list[str], extra: list[str]) -> subprocess.CompletedProcess[str] | None:
    """Run `bd <extra...>`; returns the CompletedProcess or None on subprocess failure."""
    cmd = [*bd_argv, *extra]
    try:
        return subprocess.run(  # noqa: S603 — argv list, no shell.
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def issues_with_label(*, bd_argv: list[str], label: str) -> list[dict[str, object]] | None:
    """Query bd for ALL issues (every status) carrying the given label."""
    result = _run_bd(bd_argv=bd_argv, extra=["list", "--all", "--label", label, "--json"])
    if result is None or result.returncode != 0:
        return None
    stdout = result.stdout.strip()
    if stdout == "":
        return []
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, list) else None


def existing_tracking_issue(
    *,
    gap_id: str,
    bd_argv: list[str],
) -> dict[str, object] | None:
    """First issue tracking gap_id, or None when no tracking issue exists."""
    matches = issues_with_label(bd_argv=bd_argv, label=f"{_GAP_LABEL_PREFIX}{gap_id}")
    if matches is None or len(matches) == 0:
        return None
    return matches[0]


def create_gap_issue(*, gap: dict[str, object], bd_argv: list[str]) -> str | None:
    """Run `bd create` for a gap. Returns the new issue id (or None on failure)."""
    gap_id = str(gap["id"])
    title = str(gap.get("title", f"Implement {gap_id}"))
    fix_hint = str(gap.get("fix_hint", ""))
    description = f"See implementation-gaps/current.json {gap_id}.\n\n{fix_hint}".strip()
    result = _run_bd(
        bd_argv=bd_argv,
        extra=[
            "create",
            title,
            "-t",
            "task",
            "-p",
            "2",
            "-d",
            description,
            "-l",
            f"{_GAP_LABEL_PREFIX}{gap_id}",
            "--json",
        ],
    )
    if result is None or result.returncode != 0:
        return None
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    new_id = parsed.get("id")
    return new_id if isinstance(new_id, str) else None


def add_dep_edge(*, blocked_id: str, blocker_id: str, bd_argv: list[str]) -> bool:
    """Run `bd dep add <blocked> <blocker>`; returns True on success."""
    result = _run_bd(bd_argv=bd_argv, extra=["dep", "add", blocked_id, blocker_id])
    return result is not None and result.returncode == 0
