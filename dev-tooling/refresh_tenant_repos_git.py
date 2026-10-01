"""Git queries plus the one fast-forward mutation `refresh_tenant_repos` performs.

Every function here is scoped to a SINGLE destination directory and
answers one of three questions:

  - IDENTITY — may this directory be touched at all? A destination that
    is a symlink, is not a directory, is not its own primary checkout (a
    linked worktree, or a plain directory nested inside some other
    repository), or whose `origin` names a different repo is reported and
    left exactly as it was found.
  - CLEANLINESS — is there uncommitted work a refresh would destroy?
    Untracked `.DS_Store` droppings are swept, and only those: never a
    symlink, never a tracked file. Anything else preserves the repo.
  - CURRENCY — is the local default branch merely BEHIND origin, or has
    it moved on its own? Only "merely behind" is fast-forwarded.

The currency queries deliberately carry NO fetch of their own. The
caller fetches once and then asks, so every answer is read off
remote-tracking refs updated in the SAME run rather than off whatever a
previous session happened to leave behind — a stale `origin/<branch>`
otherwise makes already-pushed commits look unpushed and preserves a
repo that was perfectly safe to refresh.

Following the `dev-tooling/` house style this module is standalone: it
shells out to git through its own `subprocess.run` and imports nothing
from `.claude-plugin/scripts/livespec/`. No function raises on a failed
git invocation — each returns the failure as data so the caller can
preserve one repo and carry on to the next.
"""

from __future__ import annotations

import subprocess
from pathlib import Path, PurePosixPath

__all__: list[str] = [
    "default_branch_ahead",
    "fast_forward",
    "fetch_origin",
    "identity_problem",
    "in_progress_operation",
    "porcelain_status",
    "primary_checkout",
    "run_git",
    "sweep_ds_store",
    "unpushed_count",
]

_DS_STORE = ".DS_Store"
_UNTRACKED_PREFIX = "?? "
# An interrupted merge / rebase / cherry-pick / revert / bisect leaves
# one of these in the git directory. Any of them means the repo holds
# operator state that switching branches would strand.
_IN_PROGRESS_MARKERS = (
    "BISECT_LOG",
    "CHERRY_PICK_HEAD",
    "MERGE_HEAD",
    "REVERT_HEAD",
    "rebase-apply",
    "rebase-merge",
)
# gh's git credential helper, applied per-invocation so fetching a
# PRIVATE fleet repo authenticates with the same credential gh itself
# holds. The empty first value clears any inherited helper for the host,
# so gh's is the only one consulted.
_GH_CREDENTIAL_ARGS = (
    "-c",
    "credential.https://github.com.helper=",
    "-c",
    "credential.https://github.com.helper=!gh auth git-credential",
)


def run_git(*, repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run `git -C <repo> <args>`, capturing output and never raising."""
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def primary_checkout(*, project_root: Path) -> Path | None:
    """The PRIMARY checkout containing `project_root`, or None if it is not a repo.

    Resolved through `--git-common-dir`, which points at the primary
    checkout's git directory from a LINKED WORKTREE just as it does from
    the primary itself. The peer root the caller derives from this is
    therefore the same whichever vantage the refresher is run from.
    """
    result = run_git(
        repo=project_root,
        args=["rev-parse", "--path-format=absolute", "--git-common-dir"],
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).parent


def _origin_slug(*, url: str) -> str:
    """The `owner/repo` tail of a git remote URL, suffix- and case-normalized.

    Collapses the forms that name the same repository — an HTTPS URL, the
    same URL with a `.git` suffix or trailing slash, and an SSH
    `git@host:owner/repo` — onto one comparable value.
    """
    trimmed = url.strip().removesuffix("/").removesuffix(".git")
    return "/".join(trimmed.replace(":", "/").rsplit("/", 2)[-2:]).lower()


def _placement_problem(*, dest: Path) -> str | None:
    """Why `dest` is not a primary checkout of its own, or None when it is.

    Four ways a destination can occupy the expected path without being
    something the refresher may rewrite: it is a symlink or a
    non-directory it did not create, it is not a repository at all, or
    its repository ROOT is somewhere else — which covers both a linked
    worktree and a plain subdirectory of some other clone.
    """
    if dest.is_symlink():
        return "destination is a symlink"
    if not dest.is_dir():
        return "destination exists but is not a directory"
    toplevel = run_git(repo=dest, args=["rev-parse", "--show-toplevel"])
    if toplevel.returncode != 0:
        return "destination is not a git repository"
    if Path(toplevel.stdout.strip()).resolve() != dest.resolve():
        return f"destination is nested inside the repository at {toplevel.stdout.strip()}"
    dirs = run_git(repo=dest, args=["rev-parse", "--git-dir", "--git-common-dir"])
    git_dir, _, common_dir = dirs.stdout.strip().partition("\n")
    if git_dir.strip() != common_dir.strip():
        return "destination is a linked worktree, not a primary checkout"
    return None


def _remote_problem(*, dest: Path, github_url: str) -> str | None:
    """Why `dest`'s `origin` is not the declared repository, or None when it is."""
    origin = run_git(repo=dest, args=["remote", "get-url", "origin"])
    if origin.returncode != 0:
        return "destination has no `origin` remote"
    if _origin_slug(url=origin.stdout) != _origin_slug(url=github_url):
        return f"destination `origin` is {origin.stdout.strip()}, which is not {github_url}"
    return None


def identity_problem(*, dest: Path, github_url: str) -> str | None:
    """Why `dest` must not be touched, or None when it is this repo's own clone.

    Two questions, asked in increasing cost order and short-circuited:
    is this path a primary checkout of its own at all, and if so, is it a
    checkout of the repository the registry declared — rather than a
    different clone that merely occupies the expected name.
    """
    return _placement_problem(dest=dest) or _remote_problem(dest=dest, github_url=github_url)


def porcelain_status(*, repo: Path) -> list[str]:
    """Every `git status --porcelain` line: staged, modified, or untracked."""
    result = run_git(repo=repo, args=["status", "--porcelain", "--untracked-files=all"])
    return result.stdout.splitlines()


def sweep_ds_store(*, repo: Path) -> list[str]:
    """Delete UNTRACKED, non-symlink regular files named exactly `.DS_Store`.

    Scoped as narrowly as the name. An untracked SYMLINK called
    `.DS_Store` is left in place — deleting it would act on a pointer the
    operator put there deliberately — and a TRACKED `.DS_Store` never
    enters the untracked set at all, so it is never even a candidate.
    Returns the repo-relative paths actually deleted.
    """
    removed: list[str] = []
    for line in porcelain_status(repo=repo):
        if not line.startswith(_UNTRACKED_PREFIX):
            continue
        rel = line[len(_UNTRACKED_PREFIX) :]
        if PurePosixPath(rel).name != _DS_STORE:
            continue
        path = repo / rel
        if path.is_symlink() or not path.is_file():
            continue
        path.unlink()
        removed.append(rel)
    return removed


def in_progress_operation(*, repo: Path) -> str | None:
    """The marker file of an interrupted git operation in `repo`, or None."""
    result = run_git(repo=repo, args=["rev-parse", "--absolute-git-dir"])
    git_dir = Path(result.stdout.strip())
    for marker in _IN_PROGRESS_MARKERS:
        if (git_dir / marker).exists():
            return marker
    return None


def fetch_origin(*, repo: Path) -> str | None:
    """`git fetch --prune origin` through gh's credential helper; problem or None."""
    result = run_git(repo=repo, args=[*_GH_CREDENTIAL_ARGS, "fetch", "--prune", "origin"])
    if result.returncode != 0:
        return f"`git fetch --prune origin` failed: {result.stderr.strip()}"
    return None


def unpushed_count(*, repo: Path) -> int:
    """Commits reachable from HEAD that no `origin/*` remote-tracking ref holds.

    Counting against every `origin/*` ref rather than the checked-out
    branch's configured upstream answers the question that matters — is
    this work anywhere on the remote at all — for a branch that was
    pushed without `--set-upstream` as readily as for one that was not.
    """
    result = run_git(repo=repo, args=["rev-list", "--count", "HEAD", "--not", "--remotes=origin"])
    return int(result.stdout.strip() or "0")


def default_branch_ahead(*, repo: Path, default_branch: str) -> int:
    """Commits the LOCAL default branch holds that `origin/<default_branch>` lacks.

    Non-zero covers BOTH "ahead" and "diverged" — the two states no
    fast-forward can reconcile — because either way the local branch
    carries a commit the remote does not. A default branch that does not
    exist locally yet is ahead of nothing, so it answers 0 and the caller
    goes on to create it from origin.
    """
    local = f"refs/heads/{default_branch}"
    present = run_git(repo=repo, args=["rev-parse", "--verify", "--quiet", local])
    if present.returncode != 0:
        return 0
    counts = run_git(
        repo=repo,
        args=[
            "rev-list",
            "--count",
            "--left-right",
            f"{local}...refs/remotes/origin/{default_branch}",
        ],
    )
    ahead, _, _ = counts.stdout.strip().partition("\t")
    return int(ahead or "0")


def fast_forward(*, repo: Path, default_branch: str) -> str | None:
    """Switch `repo` to `default_branch` and fast-forward it onto origin.

    `git switch` is a no-op when the repo is already on that branch, and
    creates the branch from `origin/<default_branch>` when it does not
    exist locally. `--ff-only` is what makes the merge leg safe: it
    refuses rather than inventing a merge commit, so a divergence the
    caller's own guard somehow missed still cannot rewrite history.
    """
    switch = run_git(repo=repo, args=["switch", default_branch])
    if switch.returncode != 0:
        return f"`git switch {default_branch}` failed: {switch.stderr.strip()}"
    merge = run_git(repo=repo, args=["merge", "--ff-only", f"origin/{default_branch}"])
    if merge.returncode != 0:
        return f"`git merge --ff-only origin/{default_branch}` failed: {merge.stderr.strip()}"
    return None
