"""Stale worktree detection for hygiene scanning."""

from __future__ import annotations

from pathlib import Path

from returns.io import IOFailure, IOResult, IOSuccess
from returns.unsafe import unsafe_perform_io

from livespec_runtime.hygiene_scan_context import (
    DEFAULT_STALE_DAYS,
    build_context,
    quote_path,
    run_command,
    worktrees,
)
from livespec_runtime.hygiene_scan_types import (
    CommandRunner,
    CommandUnavailable,
    GitWorktree,
    ScanContext,
)
from livespec_runtime.hygiene_scan_worktree_dirt import (
    WorktreeDirt,
    removal_caveat,
    worktree_dirt,
    worktree_subject,
)
from livespec_runtime.hygiene_scan_worktree_merge import (
    branch_was_rebase_merged,
    head_is_merged,
    head_is_patch_equivalent,
)
from livespec_runtime.needs_attention import HygieneScanFinding

__all__: list[str] = [
    "detect_stale_worktrees",
    "stale_worktree_findings",
]


def stale_worktree_findings(
    *, context: ScanContext
) -> IOResult[list[HygieneScanFinding], CommandUnavailable]:
    """Detect worktrees the reaper can prune/remove without force."""
    listed = worktrees(context=context)
    if isinstance(listed, IOFailure):
        return listed
    findings: list[HygieneScanFinding] = []
    for worktree in unsafe_perform_io(listed.unwrap()):
        if worktree.path in (context.primary_path, context.current_path):
            continue
        probed = stale_worktree_finding(context=context, worktree=worktree)
        if isinstance(probed, IOFailure):
            return probed
        finding = unsafe_perform_io(probed.unwrap())
        if finding is not None:
            findings.append(finding)
    return IOSuccess(findings)


def detect_stale_worktrees(
    *,
    repo_path: Path,
    runner: CommandRunner | None = None,
) -> list[GitWorktree]:
    """Return the stale worktree CANDIDATE set for `repo_path`.

    ⛔ THE RAILWAY TERMINATES HERE, AND THE SIGNATURE IS HELD ON PURPOSE.
    This is one of exactly two functions in this subsystem consumed ACROSS
    REPOS by source copy — `livespec` and `livespec-overseer` call it from
    their `dev-tooling/reap_stale_worktrees.py` and index the list it
    returns. Widening the return type to `IOResult` is a coordinated
    multi-repo change, not a side effect of putting the leaf on the
    railway, so it is filed rather than taken here.

    `unwrap()` is the deliberate terminal: an unspawnable command raises
    out of this call, which is EXACTLY what it did before the railway
    existed (an uncaught `FileNotFoundError` from `subprocess.run`). This
    boundary is therefore behaviour-preserving, not a swallow — nothing
    is discarded and no failure is converted into an empty list.

    ⚠️ THE CANDIDATE SET NOW INCLUDES WORKTREES A PLAIN REMOVE REFUSES.
    A worktree whose only dirt is UNTRACKED is a candidate (that is the
    population that accumulates, and hiding it was the bug), but
    `GitWorktree` carries no dirt, so a reaper indexing this list cannot
    tell which entries need `git worktree remove --force`. An unforced
    remove fails loudly on those rather than doing anything destructive.
    Teaching the reapers to force is a coordinated multi-repo change, the
    same class as widening the return type; `stale_worktree_findings`
    already names the dirt and emits the forced command for the operator
    path.
    """
    context = unsafe_perform_io(
        build_context(
            repo_path=repo_path,
            repo_name=None,
            now=None,
            stale_days=DEFAULT_STALE_DAYS,
            runner=runner or run_command,
        ).unwrap()
    )
    candidates: list[GitWorktree] = []
    for worktree in unsafe_perform_io(worktrees(context=context).unwrap()):
        if worktree.path == context.primary_path:
            continue
        finding = unsafe_perform_io(
            stale_worktree_finding(context=context, worktree=worktree).unwrap()
        )
        if finding is not None:
            candidates.append(worktree)
    return candidates


def stale_worktree_finding(
    *,
    context: ScanContext,
    worktree: GitWorktree,
) -> IOResult[HygieneScanFinding | None, CommandUnavailable]:
    label = str(worktree.path)
    if is_default_branch_worktree(context=context, worktree=worktree):
        return IOSuccess(None)
    if worktree.prunable_reason is not None:
        return IOSuccess(prunable_worktree_finding(context=context, worktree=worktree, label=label))
    probed = worktree_dirt(worktree=worktree, runner=context.runner)
    if isinstance(probed, IOFailure):
        return probed
    dirt = unsafe_perform_io(probed.unwrap())
    # Two dispositions, one skip: git gave no reading, so nothing can be
    # concluded; or the worktree holds AUTHORED work, which is never
    # proposed for removal. Untracked dirt is neither, and falls through.
    if dirt is None or dirt.tracked_changes != ():
        return IOSuccess(None)
    return landed_worktree_finding(context=context, worktree=worktree, label=label, dirt=dirt)


def prunable_worktree_finding(
    *, context: ScanContext, worktree: GitWorktree, label: str
) -> HygieneScanFinding:
    """The finding for a worktree whose metadata git itself reports prunable."""
    return HygieneScanFinding(
        type="stale-worktree",
        resource=label,
        path=label,
        summary=f"Prune stale worktree metadata for {label} ({worktree.prunable_reason}).",
        command=f"git -C {quote_path(path=context.primary_path)} worktree prune -v",
    )


def landed_worktree_finding(
    *, context: ScanContext, worktree: GitWorktree, label: str, dirt: WorktreeDirt
) -> IOResult[HygieneScanFinding | None, CommandUnavailable]:
    """The finding for a worktree whose work has already landed, if any.

    The dirt does not decide WHETHER to report — `stale_worktree_finding`
    already held back the authored work. It decides how the report reads,
    because untracked content changes the removal command an operator
    has to run.
    """
    reason = landed_reason(context=context, worktree=worktree)
    if isinstance(reason, IOFailure):
        return reason
    landed = unsafe_perform_io(reason.unwrap())
    if landed is None:
        return IOSuccess(None)
    return IOSuccess(
        HygieneScanFinding(
            type="stale-worktree",
            resource=label,
            path=label,
            summary=(
                f"Remove {worktree_subject(dirt=dirt)} {label}; {landed}."
                f"{removal_caveat(dirt=dirt)}"
            ),
            command=removal_command(context=context, worktree=worktree, dirt=dirt),
        )
    )


def landed_reason(
    *, context: ScanContext, worktree: GitWorktree
) -> IOResult[str | None, CommandUnavailable]:
    """Why `worktree`'s work has already landed, or None if it has not.

    The evidence comes from two levels and they are asked in that order:
    what the HEAD's own commits say, and — only if they say nothing —
    what became of the branch on origin. Each rung carries its own prose
    because an operator acts on the reason, not on the verdict.
    """
    from_head = head_landed_reason(context=context, worktree=worktree)
    if isinstance(from_head, IOFailure):
        return from_head
    reason = unsafe_perform_io(from_head.unwrap())
    if reason is not None:
        return IOSuccess(reason)
    return branch_landed_reason(context=context, worktree=worktree)


def head_landed_reason(
    *, context: ScanContext, worktree: GitWorktree
) -> IOResult[str | None, CommandUnavailable]:
    """Why the HEAD's commits are already in the base ref, or None.

    Two readings of one question, because a rebase or squash merge
    rewrites SHAs: literal ancestry first, then patch equivalence, which
    is the reading that survives the rewrite.
    """
    merged = head_is_merged(context=context, head=worktree.head)
    if isinstance(merged, IOFailure):
        return merged
    if unsafe_perform_io(merged.unwrap()):
        return IOSuccess(f"its HEAD is merged into {context.base_ref}")
    equivalent = head_is_patch_equivalent(context=context, head=worktree.head)
    if isinstance(equivalent, IOFailure):
        return equivalent
    if unsafe_perform_io(equivalent.unwrap()):
        landed = (
            f"every commit on its HEAD is already in {context.base_ref} by patch equivalence "
            f"(git cherry), so a rebase or squash merge landed it"
        )
        return IOSuccess(landed)
    return IOSuccess(None)


def branch_landed_reason(
    *, context: ScanContext, worktree: GitWorktree
) -> IOResult[str | None, CommandUnavailable]:
    """Why the branch shows its work landed, or None if it does not."""
    rebase_merged = branch_was_rebase_merged(context=context, worktree=worktree)
    if isinstance(rebase_merged, IOFailure):
        return rebase_merged
    if unsafe_perform_io(rebase_merged.unwrap()):
        landed = (
            f"its branch {worktree.branch} was pushed and its origin branch is gone "
            f"(rebase-merged, so its HEAD is not an ancestor of {context.base_ref})"
        )
        return IOSuccess(landed)
    return IOSuccess(None)


def removal_command(*, context: ScanContext, worktree: GitWorktree, dirt: WorktreeDirt) -> str:
    """The removal command, forced when a plain one would be refused."""
    forced = "" if dirt.untracked_entries == () else " --force"
    return (
        f"git -C {quote_path(path=context.primary_path)} "
        f"worktree remove{forced} {quote_path(path=worktree.path)}"
    )


def is_default_branch_worktree(*, context: ScanContext, worktree: GitWorktree) -> bool:
    """Return True if `worktree` is checked out on the repo's default branch."""
    return worktree.branch is not None and worktree.branch == context.default_branch
