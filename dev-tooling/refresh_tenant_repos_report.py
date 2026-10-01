"""How a preserved repo is classified, and the cleanup commands it is reported with.

A repo the refresher leaves alone is only useful to a maintainer if the
report says what to RUN. One generic sequence cannot say it: telling
someone whose default branch has diverged to stash nothing, or someone
holding unpushed commits to discard them, is worse than silence. So every
refusal carries a machine-readable STATE alongside its sentence, and the
commands are selected from that state.

The three LANDING states are the ones a maintainer can clear locally and
each gets its own sequence. Every other state describes a repo nothing
local would fix — a foreign `origin`, a failed inspection, an identity
GitHub would not resolve — so those get the pair that shows what the repo
IS instead.

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


@dataclass(frozen=True, kw_only=True)
class RepoProblem:
    """Why one repo was left untouched: its detected STATE plus the detail.

    `state` is machine-readable and selects the manual cleanup commands;
    `detail` is the sentence the maintainer reads. Keeping them apart is
    what lets a preserved repo be reported with instructions for the
    state it is actually in.
    """

    state: str
    detail: str


def cleanup_commands(*, dest: Path, default_branch: str | None, state: str) -> list[str]:
    """Copy-pasteable commands that clear exactly the state detected at `dest`.

    One generic sequence cannot serve every refusal: it would tell a
    maintainer whose default branch has diverged to stash nothing, and
    one holding unpushed commits to discard them. So the three states a
    maintainer can actually clear locally each get their own sequence,
    and everything else — a foreign `origin`, a failed inspection, an
    unresolved identity — gets the pair that shows what the repo IS,
    since no stash or push would help.

    Every path and every branch name is shell-quoted, so a peer root or a
    branch containing a space still yields a line that can be pasted into
    a shell unchanged.
    """
    at = shlex.quote(str(dest))
    look = f"git -C {at} status --short --branch"
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
