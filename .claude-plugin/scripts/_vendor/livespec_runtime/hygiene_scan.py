"""Git-level hygiene scanner normalized to attention items."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from livespec_runtime.attention_item import AttentionItem
from livespec_runtime.hygiene_scan_cli import main, run
from livespec_runtime.hygiene_scan_context import DEFAULT_STALE_DAYS, build_context, run_command
from livespec_runtime.hygiene_scan_findings import (
    primary_health_findings,
    stale_branch_findings,
    stale_pr_findings,
)
from livespec_runtime.hygiene_scan_types import CommandResult, CommandRunner, GitWorktree
from livespec_runtime.hygiene_scan_worktrees import (
    detect_stale_worktrees,
    stale_worktree_findings,
)
from livespec_runtime.needs_attention import compose_needs_attention

__all__: list[str] = [
    "CommandResult",
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
    """Return current repo hygiene findings as normalized attention items."""
    context = build_context(
        repo_path=repo_path,
        repo_name=repo_name,
        now=now,
        stale_days=stale_days,
        runner=runner or run_command,
    )
    findings = [
        *stale_worktree_findings(context=context),
        *primary_health_findings(context=context),
        *stale_branch_findings(context=context),
    ]
    if include_prs:
        findings.extend(stale_pr_findings(context=context))
    return compose_needs_attention(repo=context.repo_name, hygiene_scan=findings)


if __name__ == "__main__":
    raise SystemExit(run())
