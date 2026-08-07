"""Git-query helpers for the worktree reaper, extracted from `reap_stale_worktrees`.

The read-only side of the reaper: one `git -C` runner and the three
queries built on it that answer whether a candidate may be reaped at all
-- has this branch ever been pushed, what is the repo's default branch,
and is this candidate sitting on it.

They are separated from the mutating side deliberately. Everything here
only READS; the removal path that runs `worktree remove` and `branch -D`
stays in the parent. `reap_stale_worktrees` imports from here and nothing
here imports from it, so the dependency is one-way and the two cannot
form a cycle.

Imported flat (`from reap_stale_worktrees_git import ...`) because
`dev-tooling/` is a script directory on `sys.path` rather than a package
-- the same shape as the existing `reap_stale_worktrees_locks` sibling.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[1] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

from livespec_runtime.hygiene_scan import GitWorktree  # noqa: E402  — path-aware import.

__all__: list[str] = [
    "_branch_was_pushed",
    "_candidate_on_default_branch",
    "_resolve_default_branch",
    "_run_git",
]


def _run_git(*, repo: Path, args: list[str], check: bool) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def _branch_was_pushed(*, repo: Path, branch: str) -> bool:
    """Return True if `branch` carries local evidence of ever having been pushed.

    Two signals, either sufficient:

      - upstream config (`branch.<name>.merge`), written by
        `git push -u` / `--set-upstream`; it persists after the
        remote branch is deleted and after `fetch --prune`;
      - a remote-tracking ref (`refs/remotes/origin/<name>`),
        written by a plain `git push origin <name>` (and by fetch)
        and lingering until `fetch --prune` removes it.

    This is the reaper's ACTION-layer never-pushed guard: a branch with
    NEITHER signal is local-only never-pushed work, so even when the
    detection seam flags its worktree (a fresh worktree at `origin/HEAD`
    is a trivial ancestor of `origin/HEAD`), the action layer treats it
    as a dispatched agent's in-progress work and SKIPS it.
    """
    upstream = _run_git(repo=repo, args=["config", "--get", f"branch.{branch}.merge"], check=False)
    if upstream.returncode == 0 and upstream.stdout.strip() != "":
        return True
    tracking = _run_git(
        repo=repo,
        args=["rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
        check=False,
    )
    return tracking.returncode == 0


def _resolve_default_branch(*, repo: Path) -> str | None:
    """Resolve `repo`'s default branch name from `refs/remotes/origin/HEAD`.

    Reads `git symbolic-ref refs/remotes/origin/HEAD` (e.g.
    `refs/remotes/origin/master`) and strips the `refs/remotes/origin/`
    prefix, yielding the short default-branch name (`master`/`main`).
    Returns None when `origin/HEAD` is unset (no origin, or a fresh clone
    that never resolved it), so the action-layer guard applies NO
    default-branch skip rather than guarding on a bogus name.
    """
    result = _run_git(
        repo=repo,
        args=["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"],
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip().removeprefix("refs/remotes/origin/")


def _candidate_on_default_branch(*, candidate: GitWorktree, default_branch: str | None) -> bool:
    """Return True if `candidate` is checked out ON the repo's default branch.

    A secondary worktree whose CURRENT BRANCH is the default branch
    (`master`/`main`) is MAINLINE, never a stale/merged feature branch, so
    it must NEVER be reaped — removing it runs `git worktree remove` +
    `branch -D <default>`, destroying a mainline worktree and its default
    branch. This is the action-layer belt-and-suspenders counterpart to the
    detection seam's own default-branch guard: even if detection ever
    regressed and surfaced such a worktree as a candidate, this skip stops
    the destructive removal. A detached worktree (`branch is None`) does not
    match — it holds no named branch to `branch -D`, so removing it is
    `git worktree remove` only. When the default branch is UNRESOLVED
    (`default_branch is None`) no candidate matches.
    """
    return (
        candidate.branch is not None
        and default_branch is not None
        and candidate.branch == default_branch
    )
