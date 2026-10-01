"""Git queries plus the one fast-forward mutation `refresh_tenant_repos` performs.

Every function here is scoped to a SINGLE destination directory and
answers one of three questions:

  - IDENTITY — may this directory be touched at all? A destination that
    is a symlink, is not a directory, is not its own primary checkout (a
    linked worktree, or a plain directory nested inside some other
    repository), or whose `origin` names a repository on another host or
    under neither the registered nor the canonical `owner/repo` is
    reported and left exactly as it was found.
  - CLEANLINESS — is there uncommitted work a refresh would destroy?
    Untracked `.DS_Store` droppings are swept, and only those: never a
    symlink, never a tracked file. Anything else preserves the repo.
  - CURRENCY — is the local default branch merely BEHIND origin, or has
    it moved on its own? Only "merely behind" is fast-forwarded.

EVERY INSPECTION IS FAIL-CLOSED. A git query that exits non-zero answers
with a `problem` rather than with whatever its empty stdout would have
parsed to, because those empty parses are not neutral: they spell "the
tree is clean", "nothing is in progress", and "nothing is unpushed" —
the three answers that let a refresh run over a repository nobody could
actually inspect. So the probe dataclasses below carry the failure
alongside the value instead of returning the value alone.

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
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from refresh_tenant_repos_identity import GITHUB_HOST, github_slug

__all__: list[str] = [
    "GH_CREDENTIAL_ARGS",
    "CountFacts",
    "SweepOutcome",
    "TextFacts",
    "clone_https",
    "default_branch_ahead",
    "fast_forward",
    "fetch_https",
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
#
# PUBLIC because the only way to prove these options do anything is to
# hand them to git directly — `git credential fill` for this host, with a
# `gh` that records being asked — and every clone and fetch this module
# issues resolves to a repository that never requests a credential.
GH_CREDENTIAL_ARGS = (
    "-c",
    f"credential.https://{GITHUB_HOST}.helper=",
    "-c",
    f"credential.https://{GITHUB_HOST}.helper=!gh auth git-credential",
)
# The refspec that makes a URL-addressed fetch update remote-tracking
# refs. Without it `git fetch <url>` writes FETCH_HEAD only, and every
# currency verdict below reads `refs/remotes/origin/*`.
_FETCH_REFSPEC = "+refs/heads/*:refs/remotes/origin/*"


@dataclass(frozen=True, kw_only=True)
class TextFacts:
    """Text a git inspection reported, or why its exit status made it untrustworthy.

    `values` is EMPTY whenever `problem` is set — which is exactly the
    value a failed command's empty stdout would have parsed to, hence the
    separate field rather than a sentinel inside the list.
    """

    problem: str | None
    values: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class CountFacts:
    """A commit count a git inspection reported, or why it is untrustworthy."""

    problem: str | None
    count: int


@dataclass(frozen=True, kw_only=True)
class SweepOutcome:
    """The `.DS_Store` droppings deleted, and the status lines that survived them.

    Reporting the survivors is what lets the caller reach a cleanliness
    verdict with NO second `git status` — and therefore with no second
    inspection failure to interpret.
    """

    removed: tuple[str, ...]
    remaining: tuple[str, ...]


def run_git(*, repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run `git -C <repo> <args>`, capturing output and never raising."""
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _inspection_failure(*, args: list[str], result: subprocess.CompletedProcess[str]) -> str:
    """The message for a git inspection that exited non-zero."""
    detail = (result.stderr or result.stdout).strip()
    return f"git inspection `git {' '.join(args)}` failed: {detail}"


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


def _placement_problem(*, dest: Path) -> str | None:
    """Why `dest` is not a primary checkout of its own, or None when it is.

    Four ways a destination can occupy the expected path without being
    something the refresher may rewrite: it is a symlink or a
    non-directory it did not create, it is not a repository at all, or
    its repository ROOT is somewhere else — which covers both a linked
    worktree and a plain subdirectory of some other clone.

    All three paths come from ONE `rev-parse`, so its exit status is the
    single fail-closed gate: a non-zero exit cannot be mistaken for a
    primary checkout whose git directory happens to compare equal to the
    empty string the failure would otherwise have left behind.
    """
    if dest.is_symlink():
        return "destination is a symlink"
    if not dest.is_dir():
        return "destination exists but is not a directory"
    args = ["rev-parse", "--show-toplevel", "--git-dir", "--git-common-dir"]
    probe = run_git(repo=dest, args=args)
    if probe.returncode != 0:
        return "destination is not a git repository"
    toplevel, git_dir, common_dir, *_ = [*probe.stdout.splitlines(), "", "", ""]
    if Path(toplevel).resolve() != dest.resolve():
        return f"destination is nested inside the repository at {toplevel}"
    if git_dir != common_dir:
        return "destination is a linked worktree, not a primary checkout"
    return None


def _remote_problem(*, dest: Path, accepted_urls: tuple[str, ...]) -> str | None:
    """Why `dest`'s `origin` is not one of the ACCEPTED repositories, or None.

    Two independent disqualifications. The first is RECOGNITION, and it
    is an allowlist: a remote on another forge, on a filesystem path, or
    merely carrying an extra path segment is not this repository however
    well its last two segments match. Past that, EITHER the registered
    identity or
    the canonical one it redirects to is accepted — which is what lets a
    clone already carrying a post-transfer URL be refreshed instead of
    preserved on every host forever.
    """
    # `git config --get` reads the CONFIGURED value. `git remote get-url`
    # applies any `url.<base>.insteadOf` rewrite first, which would hand
    # the identity check a URL the repository does not actually record.
    origin = run_git(repo=dest, args=["config", "--get", "remote.origin.url"])
    if origin.returncode != 0:
        return "destination has no `origin` remote"
    url = origin.stdout.strip()
    slug = github_slug(url=url)
    if slug is None:
        return (
            f"destination `origin` is {url}, which is not a "
            f"https://{GITHUB_HOST}/<owner>/<repo> remote"
        )
    accepted = {github_slug(url=candidate) for candidate in accepted_urls}
    if slug not in accepted:
        named = ", ".join(dict.fromkeys(accepted_urls))
        return f"destination `origin` is {url}, which names none of: {named}"
    return None


def identity_problem(*, dest: Path, accepted_urls: tuple[str, ...]) -> str | None:
    """Why `dest` must not be touched, or None when it is one of `accepted_urls`.

    Two questions, asked in increasing cost order and short-circuited:
    is this path a primary checkout of its own at all, and if so, is it a
    checkout of a repository the run is entitled to refresh — rather than
    a different clone that merely occupies the expected name.
    """
    return _placement_problem(dest=dest) or _remote_problem(dest=dest, accepted_urls=accepted_urls)


def porcelain_status(*, repo: Path) -> TextFacts:
    """Every `git status --porcelain` line: staged, modified, or untracked.

    Fail-closed: a non-zero `git status` — a repository whose index
    cannot be read, say — answers with a problem, because an empty line
    list is indistinguishable from a clean tree and would refresh a repo
    whose state nobody could see.
    """
    args = ["status", "--porcelain", "--untracked-files=all"]
    result = run_git(repo=repo, args=args)
    if result.returncode != 0:
        return TextFacts(problem=_inspection_failure(args=args, result=result), values=())
    return TextFacts(problem=None, values=tuple(result.stdout.splitlines()))


def _ds_store_dropping(*, repo: Path, line: str) -> str | None:
    """The repo-relative path a status line names, when it is a deletable dropping.

    Scoped as narrowly as the name. An untracked SYMLINK called
    `.DS_Store` is left in place — deleting it would act on a pointer the
    operator put there deliberately — and a TRACKED `.DS_Store` never
    enters the untracked set at all, so it is never even a candidate.
    """
    if not line.startswith(_UNTRACKED_PREFIX):
        return None
    relative = line[len(_UNTRACKED_PREFIX) :]
    if PurePosixPath(relative).name != _DS_STORE:
        return None
    path = repo / relative
    if path.is_symlink() or not path.is_file():
        return None
    return relative


def sweep_ds_store(*, repo: Path, status_lines: tuple[str, ...]) -> SweepOutcome:
    """Delete UNTRACKED, non-symlink regular files named exactly `.DS_Store`.

    Takes the status lines the caller already read and reports the ones
    that survived, so the sweep adds no inspection of its own.
    """
    removed: list[str] = []
    remaining: list[str] = []
    for line in status_lines:
        relative = _ds_store_dropping(repo=repo, line=line)
        if relative is None:
            remaining.append(line)
            continue
        (repo / relative).unlink()
        removed.append(relative)
    return SweepOutcome(removed=tuple(removed), remaining=tuple(remaining))


def in_progress_operation(*, repo: Path) -> TextFacts:
    """The marker files of interrupted git operations in `repo`.

    Fail-closed on the `rev-parse` probe: without the git directory the
    markers cannot be looked for at all, and an empty answer reads as
    "nothing in progress" — the one answer that lets a refresh strand an
    interrupted merge.
    """
    args = ["rev-parse", "--absolute-git-dir"]
    result = run_git(repo=repo, args=args)
    if result.returncode != 0:
        return TextFacts(problem=_inspection_failure(args=args, result=result), values=())
    git_dir = Path(result.stdout.strip())
    found = tuple(marker for marker in _IN_PROGRESS_MARKERS if (git_dir / marker).exists())
    return TextFacts(problem=None, values=found)


def fetch_https(*, repo: Path, url: str) -> str | None:
    """Fetch `url` into `refs/remotes/origin/*` through gh's credential helper.

    The URL is passed on the COMMAND LINE with an explicit refspec rather
    than read out of `remote.origin.url`. That is what makes the fetch
    reach GitHub over HTTPS — at the validated canonical URL — even when
    the clone's own `origin` is an SSH URL, while leaving the
    repository's git config byte-identical because nothing is written to
    it. A `-c remote.origin.url=` override will NOT do: `remote.<name>.url`
    is multi-valued, so a `-c` value is APPENDED behind the configured
    one and the configured URL still wins.
    """
    args = [*GH_CREDENTIAL_ARGS, "fetch", "--prune", url, _FETCH_REFSPEC]
    result = run_git(repo=repo, args=args)
    if result.returncode != 0:
        return f"`git fetch --prune {url}` failed: {result.stderr.strip()}"
    return None


def clone_https(*, url: str, dest: Path) -> str | None:
    """Clone `url` into `dest` over HTTPS through gh's credential helper.

    Addressing the canonical HTTPS URL — rather than handing `gh repo
    clone` an `owner/repo` slug — makes the protocol THIS tool's decision.
    gh would pick it from its own `git_protocol` setting, which is `ssh`
    on the maintainer's Mac, so a slug clone needs separate SSH auth and
    leaves the new clone's `origin` as an SSH URL every later run has to
    fetch around. Cloning the HTTPS URL instead means `origin` is already
    the URL the next fetch wants.

    The credential options are passed to GIT ITSELF, BEFORE the `clone`
    subcommand. `git clone -c <key>=<value>` writes the setting into the
    NEW repository's config, which would leave a credential helper
    persisted in a governed checkout; `git -c <key>=<value> clone` applies
    it to this invocation only and writes nothing.
    """
    args = [*GH_CREDENTIAL_ARGS, "clone", url, str(dest)]
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return f"`git clone {url}` failed: {(result.stderr or result.stdout).strip()}"
    return None


def unpushed_count(*, repo: Path) -> CountFacts:
    """Commits reachable from HEAD that no `origin/*` remote-tracking ref holds.

    Counting against every `origin/*` ref rather than the checked-out
    branch's configured upstream answers the question that matters — is
    this work anywhere on the remote at all — for a branch that was
    pushed without `--set-upstream` as readily as for one that was not.

    Fail-closed: an unborn HEAD, or any other repository state that makes
    the walk impossible, answers with a problem rather than with the zero
    an empty stdout would have parsed to.
    """
    args = ["rev-list", "--count", "HEAD", "--not", "--remotes=origin"]
    result = run_git(repo=repo, args=args)
    if result.returncode != 0:
        return CountFacts(problem=_inspection_failure(args=args, result=result), count=0)
    return CountFacts(problem=None, count=int(result.stdout.strip() or "0"))


def default_branch_ahead(*, repo: Path, default_branch: str) -> CountFacts:
    """Commits the LOCAL default branch holds that `origin/<default_branch>` lacks.

    Non-zero covers BOTH "ahead" and "diverged" — the two states no
    fast-forward can reconcile — because either way the local branch
    carries a commit the remote does not. A default branch that does not
    exist locally yet is ahead of nothing, so it answers 0 and the caller
    goes on to create it from origin — but ONLY exit 1 means "absent".
    `rev-parse --verify --quiet` exits 1 for a ref it looked for and did
    not find, and 128 when it could not look at all; reading every
    non-zero exit as absence turns that second case into "ahead of
    nothing", which is the answer that refreshes a repository the probe
    never managed to inspect.
    """
    local = f"refs/heads/{default_branch}"
    verify = ["rev-parse", "--verify", "--quiet", local]
    present = run_git(repo=repo, args=verify)
    if present.returncode == 1:
        return CountFacts(problem=None, count=0)
    if present.returncode != 0:
        return CountFacts(problem=_inspection_failure(args=verify, result=present), count=0)
    args = [
        "rev-list",
        "--count",
        "--left-right",
        f"{local}...refs/remotes/origin/{default_branch}",
    ]
    counts = run_git(repo=repo, args=args)
    if counts.returncode != 0:
        return CountFacts(problem=_inspection_failure(args=args, result=counts), count=0)
    ahead, _, _ = counts.stdout.strip().partition("\t")
    return CountFacts(problem=None, count=int(ahead or "0"))


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
