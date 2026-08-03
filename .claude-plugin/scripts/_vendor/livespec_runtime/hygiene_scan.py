"""Git-level hygiene scanner normalized to attention items."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from returns.unsafe import unsafe_perform_io

from livespec_runtime.attention_item import AttentionItem
from livespec_runtime.hygiene_scan_cli import main, run
from livespec_runtime.hygiene_scan_context import DEFAULT_STALE_DAYS, build_context, run_command
from livespec_runtime.hygiene_scan_findings import (
    primary_health_findings,
    stale_branch_findings,
    stale_pr_findings,
)
from livespec_runtime.hygiene_scan_types import (
    CommandResult,
    CommandRunner,
    CommandUnavailable,
    GitWorktree,
)
from livespec_runtime.hygiene_scan_worktrees import (
    detect_stale_worktrees,
    stale_worktree_findings,
)
from livespec_runtime.needs_attention import compose_needs_attention

__all__: list[str] = [
    "CommandResult",
    "CommandUnavailable",
    "GitWorktree",
    "detect_stale_worktrees",
    "main",
    "run",
    "scan_hygiene",
    "stale_worktree_findings",
]


def scan_hygiene(
    *,
    repo_path: Path,
    repo_name: str | None = None,
    now: datetime | None = None,
    stale_days: int = DEFAULT_STALE_DAYS,
    include_prs: bool = True,
    runner: CommandRunner | None = None,
) -> list[AttentionItem]:
    """Return current repo hygiene findings as normalized attention items.

    ⛔ THE RAILWAY TERMINATES HERE, AND THE SIGNATURE IS HELD ON PURPOSE.
    This is one of exactly two functions in this subsystem consumed ACROSS
    REPOS by source copy — `livespec-orchestrator-beads-fabro` and
    `livespec-orchestrator-git-jsonl` call it from their
    `commands/needs_attention.py` and splice the list it returns straight
    into `compose_needs_attention`. Widening the return type to `IOResult`
    is a coordinated multi-repo change, not a side effect of putting the
    leaf on the railway, so it is filed rather than taken here. See
    `detect_stale_worktrees` for the sibling terminal.

    `unwrap()` is the deliberate terminal: an unspawnable command raises
    out of this call, which is EXACTLY what it did before the railway
    existed. Nothing is discarded and no failure becomes an empty list.
    """
    context = unsafe_perform_io(
        build_context(
            repo_path=repo_path,
            repo_name=repo_name,
            now=now,
            stale_days=stale_days,
            runner=runner or run_command,
        ).unwrap()
    )
    findings = [
        *unsafe_perform_io(stale_worktree_findings(context=context).unwrap()),
        *unsafe_perform_io(primary_health_findings(context=context).unwrap()),
        *unsafe_perform_io(stale_branch_findings(context=context).unwrap()),
    ]
    if include_prs:
        findings.extend(unsafe_perform_io(stale_pr_findings(context=context).unwrap()))
    return compose_needs_attention(repo=context.repo_name, hygiene_scan=findings)


if __name__ == "__main__":
    raise SystemExit(run())
