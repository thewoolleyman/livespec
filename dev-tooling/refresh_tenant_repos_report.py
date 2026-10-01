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
# each get their own cleanup commands, and INTERRUPTED gets the labelled
# choice between finishing and abandoning the operation it was found in;
# the rest describe a repo nothing local can clear, so they get an
# inspection pair instead.
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

# The git operation each in-progress marker belongs to. The two rebase
# backends leave different markers and are the same operation, and the
# operation NAME is what every recovery command and every line of the
# accompanying instructions is built from.
_OPERATIONS: dict[str, str] = {
    "BISECT_LOG": "bisect",
    "CHERRY_PICK_HEAD": "cherry-pick",
    "MERGE_HEAD": "merge",
    "REVERT_HEAD": "revert",
    "rebase-apply": "rebase",
    "rebase-merge": "rebase",
}
# The one interrupted operation with no `--continue`: a bisect cannot be
# finished, so `bisect reset` is its only way out and the report offers it
# as a single command rather than as a choice between two.
_NO_CONTINUE = "bisect"
# The instructions are emitted as `#`-prefixed lines so the whole list
# stays pasteable into a shell — a label a reader skips is a comment, not
# a command that runs. They are part of the OUTPUT and not merely of this
# module's docstrings, because a docstring never reaches the operator:
# two adjacent commands with nothing between them read as a sequence to
# run in order, and running `--continue` then `--abort` destroys exactly
# the work `--continue` just preserved.
_CHOOSE = "# CHOOSE ONE of the next two commands for the interrupted {operation}."
_NOT_BOTH = " Do NOT run both:"
_FINISH = "#   (1) finish it, keeping the conflict resolution already done:"
_ABANDON = "#   (2) OR abandon it, discarding that work:"
_ONLY_WAY_OUT = "# the interrupted {operation} cannot be finished. Ending it is the only way out:"


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
    """Both ways out of every operation `markers` names, LABELLED as a choice.

    BOTH are offered, and the refresher runs NEITHER. Continuing keeps the
    conflict resolution already done; aborting throws it away — a tool
    that picked one for the operator would be wrong half the time, and a
    tool that ran it would be wrong irrecoverably. So the decision is
    handed over, and handing it over means SAYING it is a decision: an
    unlabelled pair reads as a sequence, and running the second after the
    first discards the very work the first preserved.

    A marker this module does not recognize contributes nothing rather
    than raising. The markers come from one fixed set the git helper owns,
    so an unknown one means those two sets have drifted apart — which is a
    reason to report the repo with fewer instructions, never a reason to
    crash the report that was explaining why the repo was preserved.
    """
    lines: list[str] = []
    for marker in markers:
        operation = _OPERATIONS.get(marker)
        if operation is None:
            continue
        if operation == _NO_CONTINUE:
            lines.append(_ONLY_WAY_OUT.format(operation=operation))
            lines.append(f"git -C {at} {operation} reset")
            continue
        lines.append(_CHOOSE.format(operation=operation) + _NOT_BOTH)
        lines.append(_FINISH)
        lines.append(f"git -C {at} {operation} --continue")
        lines.append(_ABANDON)
        lines.append(f"git -C {at} {operation} --abort")
    return lines


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
