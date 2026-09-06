"""What a worktree's working tree holds, split by who put it there.

`git status --porcelain` answers "is there anything here?", and the
stale-worktree gate used to read any answer at all as "leave it alone".
That conflated two populations with opposite dispositions. AUTHORED
work — tracked modifications — must never be proposed for removal.
MACHINE-GENERATED content — the vendored `.livespec-core/` checkout a
janitor clones inside its own checkout, a self-provisioned `.venv` — is
untracked, and it is exactly what abandoned worktrees accumulate, so
suppressing on it hid the very worktrees the gate exists to surface.

Keeping the two apart preserves the safety property and ends the
blindness: untracked dirt is reportable, and the report names it,
because a plain `git worktree remove` refuses it and `--force` is what
clears it.
"""

from __future__ import annotations

from dataclasses import dataclass

from returns.io import IOResult

from livespec_runtime.hygiene_scan_context import git
from livespec_runtime.hygiene_scan_types import (
    CommandResult,
    CommandRunner,
    CommandUnavailable,
    GitWorktree,
)

__all__: list[str] = [
    "WorktreeDirt",
    "removal_caveat",
    "worktree_dirt",
    "worktree_subject",
]

# Enough entries to recognize WHAT the dirt is (a vendored checkout, a
# virtualenv) without pasting a whole untracked tree into an attention
# item's one-line summary.
_MAX_NAMED_ENTRIES = 3
_UNTRACKED_STATUS_PREFIX = "??"


@dataclass(frozen=True, slots=True, kw_only=True)
class WorktreeDirt:
    """A worktree's working-tree contents, split by authorship."""

    tracked_changes: tuple[str, ...] = ()
    untracked_entries: tuple[str, ...] = ()


def worktree_dirt(
    *, worktree: GitWorktree, runner: CommandRunner
) -> IOResult[WorktreeDirt | None, CommandUnavailable]:
    """Classify `worktree`'s working tree, or None if git did not ANSWER.

    A non-zero `git status` is not an empty working tree — it is no
    reading at all (the path is not a worktree any more, the index is
    unreadable). Nothing may be concluded from it, so it returns None
    and the caller leaves the worktree alone, which is what the former
    cleanliness test did with the same non-answer.
    """
    return git(repo_path=worktree.path, argv=["status", "--porcelain"], runner=runner).map(
        lambda result: classify_status(result=result)
    )


def classify_status(*, result: CommandResult) -> WorktreeDirt | None:
    """Split `git status --porcelain` lines into tracked vs untracked."""
    if result.returncode != 0:
        return None
    tracked: list[str] = []
    untracked: list[str] = []
    for line in result.stdout.splitlines():
        entry = line[3:].strip()
        if line.startswith(_UNTRACKED_STATUS_PREFIX):
            untracked.append(entry)
        else:
            tracked.append(entry)
    return WorktreeDirt(tracked_changes=tuple(tracked), untracked_entries=tuple(untracked))


def worktree_subject(*, dirt: WorktreeDirt) -> str:
    """How to name the worktree in a finding.

    "clean" is a claim about REMOVABILITY, not a pleasantry, so only a
    worktree a plain `git worktree remove` would accept may carry it.
    """
    if dirt.untracked_entries == ():
        return "clean worktree"
    return "worktree"


def removal_caveat(*, dirt: WorktreeDirt) -> str:
    """The clause naming the dirt a plain `git worktree remove` refuses."""
    if dirt.untracked_entries == ():
        return ""
    return (
        " Untracked content blocks a plain removal, so --force is required: "
        f"{describe_entries(entries=dirt.untracked_entries)}."
    )


def describe_entries(*, entries: tuple[str, ...]) -> str:
    """Name the first few entries, counting whatever is left over."""
    named = ", ".join(entries[:_MAX_NAMED_ENTRIES])
    hidden = len(entries) - _MAX_NAMED_ENTRIES
    if hidden > 0:
        return f"{named} (+{hidden} more)"
    return named
