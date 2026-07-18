"""Stale worktree detection for hygiene scanning."""

from __future__ import annotations

from pathlib import Path

from livespec_runtime.hygiene_scan_context import (
    DEFAULT_STALE_DAYS,
    build_context,
    git,
    quote_path,
    run_command,
    worktrees,
)
from livespec_runtime.hygiene_scan_types import CommandRunner, GitWorktree, ScanContext
from livespec_runtime.needs_attention import HygieneScanFinding

__all__: list[str] = [
    "detect_stale_worktrees",
    "head_is_merged",
    "stale_worktree_findings",
]


def stale_worktree_findings(*, context: ScanContext) -> list[HygieneScanFinding]:
    """Detect worktrees the reaper can prune/remove without force."""
    findings: list[HygieneScanFinding] = []
    for worktree in worktrees(context=context):
        if worktree.path in (context.primary_path, context.current_path):
            continue
        finding = stale_worktree_finding(context=context, worktree=worktree)
        if finding is not None:
            findings.append(finding)
    return findings


def detect_stale_worktrees(
    *,
    repo_path: Path,
    runner: CommandRunner | None = None,
) -> list[GitWorktree]:
    """Return the stale worktree CANDIDATE set for `repo_path`."""
    context = build_context(
        repo_path=repo_path,
        repo_name=None,
        now=None,
        stale_days=DEFAULT_STALE_DAYS,
        runner=runner or run_command,
    )
    candidates: list[GitWorktree] = []
    for worktree in worktrees(context=context):
        if worktree.path == context.primary_path:
            continue
        if stale_worktree_finding(context=context, worktree=worktree) is not None:
            candidates.append(worktree)
    return candidates


def stale_worktree_finding(
    *,
    context: ScanContext,
    worktree: GitWorktree,
) -> HygieneScanFinding | None:
    label = str(worktree.path)
    if is_default_branch_worktree(context=context, worktree=worktree):
        return None
    if worktree.prunable_reason is not None:
        return HygieneScanFinding(
            type="stale-worktree",
            resource=label,
            path=label,
            summary=f"Prune stale worktree metadata for {label} ({worktree.prunable_reason}).",
            command=f"git -C {quote_path(path=context.primary_path)} worktree prune -v",
        )
    if not worktree_is_clean(worktree=worktree, runner=context.runner):
        return None
    remove_command = (
        f"git -C {quote_path(path=context.primary_path)} "
        f"worktree remove {quote_path(path=worktree.path)}"
    )
    if head_is_merged(context=context, head=worktree.head):
        return HygieneScanFinding(
            type="stale-worktree",
            resource=label,
            path=label,
            summary=f"Remove clean worktree {label}; its HEAD is merged into {context.base_ref}.",
            command=remove_command,
        )
    if branch_was_rebase_merged(context=context, worktree=worktree):
        return HygieneScanFinding(
            type="stale-worktree",
            resource=label,
            path=label,
            summary=(
                f"Remove clean worktree {label}; its branch {worktree.branch} was pushed and "
                f"its origin branch is gone (rebase-merged, so its HEAD is not an ancestor of "
                f"{context.base_ref})."
            ),
            command=remove_command,
        )
    return None


def is_default_branch_worktree(*, context: ScanContext, worktree: GitWorktree) -> bool:
    """Return True if `worktree` is checked out on the repo's default branch."""
    return worktree.branch is not None and worktree.branch == context.default_branch


def branch_was_rebase_merged(*, context: ScanContext, worktree: GitWorktree) -> bool:
    """Return True if `worktree`'s branch shows the rebase-merge orphan signal."""
    branch = worktree.branch
    if branch is None:
        return False
    if not branch_was_pushed(context=context, branch=branch):
        return False
    return branch_is_done(context=context, branch=branch)


def branch_was_pushed(*, context: ScanContext, branch: str) -> bool:
    """Return True if `branch` carries local evidence of ever having been pushed."""
    upstream = git(
        repo_path=context.primary_path,
        argv=["config", "--get", f"branch.{branch}.merge"],
        runner=context.runner,
    )
    if upstream.returncode == 0 and upstream.stdout.strip() != "":
        return True
    tracking = git(
        repo_path=context.primary_path,
        argv=["rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
        runner=context.runner,
    )
    return tracking.returncode == 0


def branch_is_done(*, context: ScanContext, branch: str) -> bool:
    """Return True if `branch`'s remote head is absent on origin."""
    result = git(
        repo_path=context.primary_path,
        argv=["ls-remote", "--heads", "origin", branch],
        runner=context.runner,
    )
    if result.returncode != 0:
        return False
    return result.stdout.strip() == ""


def worktree_is_clean(*, worktree: GitWorktree, runner: CommandRunner) -> bool:
    result = git(repo_path=worktree.path, argv=["status", "--porcelain"], runner=runner)
    return result.returncode == 0 and result.stdout == ""


def head_is_merged(*, context: ScanContext, head: str | None) -> bool:
    if head is None:
        return False
    return (
        git(
            repo_path=context.primary_path,
            argv=["merge-base", "--is-ancestor", head, context.base_ref],
            runner=context.runner,
        ).returncode
        == 0
    )
