"""How a preserved repo is classified, and the cleanup commands it is reported with.

A repo the refresher leaves alone is only useful to a maintainer if the
report says what to RUN. One generic sequence cannot say it: telling
someone whose default branch has diverged to stash nothing, or someone
holding unpushed commits to discard them, is worse than silence. So every
refusal carries a machine-readable STATE alongside its sentence, and the
commands are selected from that state.

The three LANDING states are the ones a maintainer can clear locally and
each gets its own sequence. An INTERRUPTED operation is clearable locally
too, but not by landing anything: it gets the continue-or-abort pair for
whichever operation its marker names, so the choice between keeping the
half-finished work and discarding it stays the maintainer's. Every other
state describes a repo nothing local would fix — a foreign `origin`, a
failed inspection, an identity GitHub would not resolve — so those get
the pair that shows what the repo IS instead.

This module is PURE: it builds strings and performs no I/O, so the whole
reporting surface is exercisable without a filesystem.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path

__all__: list[str] = [
    "CLONE_FAILED",
    "DIVERGED",
    "FETCH_FAILED",
    "IDENTITY_MISMATCH",
    "INSPECTION_FAILED",
    "INTERRUPTED",
    "UNCOMMITTED",
    "UNPUSHED",
    "UNRESOLVED_BRANCH",
    "RepoProblem",
    "cleanup_commands",
]

# The states a refusal is classified by. The three LANDING states below
# each get their own cleanup commands; the rest describe a repo nothing
# local can clear, so they get an inspection pair instead.
CLONE_FAILED = "clone-failed"
DIVERGED = "diverged-default-branch"
FETCH_FAILED = "fetch-failed"
IDENTITY_MISMATCH = "identity-mismatch"
INSPECTION_FAILED = "inspection-failed"
INTERRUPTED = "interrupted-operation"
UNCOMMITTED = "uncommitted-changes"
UNPUSHED = "unpushed-commits"
UNRESOLVED_BRANCH = "default-branch-unresolved"
_LANDING_STATES = (UNCOMMITTED, UNPUSHED, DIVERGED)

# The way out of each interrupted operation, CONTINUE before ABORT: the
# command that keeps the work already done comes before the one that
# discards it. `bisect` is the one operation with no continue — `bisect
# reset` is the only way out of it — so its entry carries a single
# command rather than a pair. The two rebase backends leave different
# markers and take the same commands.
_RECOVERY_VERBS: dict[str, tuple[str, ...]] = {
    "BISECT_LOG": ("bisect reset",),
    "CHERRY_PICK_HEAD": ("cherry-pick --continue", "cherry-pick --abort"),
    "MERGE_HEAD": ("merge --continue", "merge --abort"),
    "REVERT_HEAD": ("revert --continue", "revert --abort"),
    "rebase-apply": ("rebase --continue", "rebase --abort"),
    "rebase-merge": ("rebase --continue", "rebase --abort"),
}


@dataclass(frozen=True, kw_only=True)
class RepoProblem:
    """Why one repo was left untouched: its detected STATE plus the detail.

    `state` is machine-readable and selects the manual cleanup commands;
    `detail` is the sentence the maintainer reads. Keeping them apart is
    what lets a preserved repo be reported with instructions for the
    state it is actually in.

    `markers` carries the in-progress marker files an INTERRUPTED repo was
    found holding, because the state alone cannot say WHICH operation to
    continue or abort — a `merge --abort` does nothing for a half-finished
    cherry-pick. Every other state leaves it empty.
    """

    state: str
    detail: str
    markers: tuple[str, ...] = ()


def _recovery_commands(*, at: str, markers: tuple[str, ...]) -> list[str]:
    """The continue-and-abort commands for every operation `markers` names.

    BOTH are offered, and the refresher runs NEITHER. Continuing keeps the
    conflict resolution already done; aborting throws it away — a tool
    that picked one for the operator would be wrong half the time, and a
    tool that ran it would be wrong irrecoverably. So the decision is
    handed over as two pasteable lines.
    """
    return [f"git -C {at} {verb}" for marker in markers for verb in _RECOVERY_VERBS.get(marker, ())]


def cleanup_commands(
    *, dest: Path, default_branch: str | None, state: str, markers: tuple[str, ...] = ()
) -> list[str]:
    """Copy-pasteable commands that clear exactly the state detected at `dest`.

    One generic sequence cannot serve every refusal: it would tell a
    maintainer whose default branch has diverged to stash nothing, and
    one holding unpushed commits to discard them. So the three states a
    maintainer can actually clear locally each get their own sequence, an
    INTERRUPTED operation gets the continue-or-abort pair for the
    operation its `markers` name, and everything else — a foreign
    `origin`, a failed inspection, an unresolved identity — gets the pair
    that shows what the repo IS, since no stash or push would help.

    Every path and every branch name is shell-quoted, so a peer root or a
    branch containing a space still yields a line that can be pasted into
    a shell unchanged.
    """
    at = shlex.quote(str(dest))
    look = f"git -C {at} status --short --branch"
    if state == INTERRUPTED:
        return [look, *_recovery_commands(at=at, markers=markers)]
    if default_branch is None or state not in _LANDING_STATES:
        return [look, f"git -C {at} remote --verbose"]
    branch = shlex.quote(default_branch)
    upstream = shlex.quote(f"origin/{default_branch}")
    land = [f"git -C {at} switch {branch}", f"git -C {at} merge --ff-only {upstream}"]
    if state == UNCOMMITTED:
        return [look, f"git -C {at} stash push --include-untracked", *land]
    if state == UNPUSHED:
        return [
            look,
            f"git -C {at} log --oneline HEAD --not --remotes=origin",
            f"git -C {at} push origin HEAD",
            *land,
        ]
    return [
        look,
        f"git -C {at} log --oneline --left-right {branch}...{upstream}",
        f"git -C {at} switch {branch}",
        f"git -C {at} rebase {upstream}",
    ]
