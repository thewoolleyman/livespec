"""refresh_tenant_repos — clone or refresh every registered fleet + adopter repo.

The fleet spans many sibling repositories, and most cross-repo work needs
all of them present, current, and on their default branch as PEERS of the
livespec primary checkout. Doing that by hand is a dozen `cd`s and a
dozen chances to clobber work in progress. This tool does it in one pass,
deterministically, with no LLM involved.

WHICH REPOS. The union of the four committed registries, resolved by
`refresh_tenant_repos_registry` — `.livespec.jsonc`'s
`cross_repo_targets` and `cross_repo_conformance_targets`, plus
`.livespec-fleet-manifest.jsonc`'s `fleet[]` and `adopters[]`.

WHERE THEY LAND. `<peer-root>/<repo>`, where the peer root is the
directory CONTAINING the primary checkout — derived through
`--git-common-dir`, so the answer is the same whether the tool runs from
the primary checkout or from a linked worktree. A registry's `local_clone`
path is deliberately not consulted.

THE SAFETY POSTURE IS PRESERVE-BY-DEFAULT, and the ordering is the whole
design. Two conditions refuse the run OUTRIGHT with exit 2, before any
clone or fetch: a `gh` that is missing or unauthenticated, and a registry
set that disagrees with itself or names a repo that is not a single safe
path segment. Past that, each repo is handled independently: a missing one
is cloned, and an existing one is refreshed only after it proves to be
this repo's own primary checkout with a clean tree and nothing unpushed.
Anything else is left EXACTLY as found and reported with the concrete
commands to clear it by hand. The fetch happens BEFORE the unpushed and
divergence decisions precisely so those decisions read refs updated in
the same run.

EXIT CODES. 0 every repo cloned or refreshed; 1 at least one preserved or
failed; 2 refused before touching anything.

This is a maintainer ACTION tool invoked via `just refresh-tenant-repos`,
not a member of `just check`. Output discipline per spec: `print` and
`sys.stderr.write` are banned in `dev-tooling/**`, so diagnostics flow
through structlog as JSON on stderr.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parent.parent / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

_DEV_TOOLING_DIR = Path(__file__).resolve().parent
if str(_DEV_TOOLING_DIR) not in sys.path:
    sys.path.insert(0, str(_DEV_TOOLING_DIR))

import jsoncomment  # noqa: E402  — path-aware import after sys.path insert.
import structlog  # noqa: E402  — path-aware import after sys.path insert.
from refresh_tenant_repos_git import (  # noqa: E402
    default_branch_ahead,
    fast_forward,
    fetch_origin,
    identity_problem,
    in_progress_operation,
    porcelain_status,
    primary_checkout,
    sweep_ds_store,
    unpushed_count,
)
from refresh_tenant_repos_registry import RepoTarget, resolve_targets  # noqa: E402

__all__: list[str] = ["main", "refresh_tenant_repos"]

_CONFIG_NAME = ".livespec.jsonc"
_MANIFEST_NAME = ".livespec-fleet-manifest.jsonc"


def _configure_logger() -> structlog.stdlib.BoundLogger:
    structlog.reset_defaults()
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    return structlog.get_logger("refresh_tenant_repos")


def _parse_jsonc(*, path: Path) -> object:
    return jsoncomment.loads(path.read_text(encoding="utf-8"))


def _gh(*, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=False)


def _gh_preflight() -> str | None:
    """Why gh cannot be used, or None. Runs BEFORE any clone or fetch.

    Both legs matter: a missing binary and an unauthenticated one fail
    the same operations, and finding out mid-run would leave some repos
    refreshed and the rest reported as clone failures.
    """
    if shutil.which("gh") is None:
        return "`gh` is not on PATH"
    status = _gh(args=["auth", "status"])
    if status.returncode != 0:
        return f"`gh auth status` failed: {(status.stderr or status.stdout).strip()}"
    return None


def _resolved_default_branch(*, target: RepoTarget) -> str | None:
    """A registry's declared default branch, else GitHub's `defaultBranchRef`."""
    if target.default_branch is not None:
        return target.default_branch
    view = _gh(
        args=[
            "repo",
            "view",
            f"{target.owner}/{target.repo}",
            "--json",
            "defaultBranchRef",
            "--jq",
            ".defaultBranchRef.name",
        ]
    )
    if view.returncode != 0:
        return None
    return view.stdout.strip() or None


def _clone(*, target: RepoTarget, dest: Path) -> str | None:
    """`gh repo clone` the target into `dest`; problem or None."""
    result = _gh(args=["repo", "clone", f"{target.owner}/{target.repo}", str(dest)])
    if result.returncode != 0:
        return f"`gh repo clone` failed: {(result.stderr or result.stdout).strip()}"
    return None


def _cleanup_commands(*, dest: Path, default_branch: str) -> list[str]:
    """Concrete, copy-pasteable commands that clear the way for a refresh.

    Reported WITH a preserved repo so the maintainer never has to work
    out the sequence: look, set the divergent work aside, land on the
    default branch, fast-forward.
    """
    return [
        f"git -C {dest} status --short --branch",
        f"git -C {dest} stash push --include-untracked",
        f"git -C {dest} switch {default_branch}",
        f"git -C {dest} merge --ff-only origin/{default_branch}",
    ]


def _blocking_state(
    *, dest: Path, target: RepoTarget, log: structlog.stdlib.BoundLogger
) -> str | None:
    """What makes `dest` untouchable BEFORE anything is fetched, or None.

    Identity and interrupted-operation state are settled before anything
    is written at all. The `.DS_Store` sweep then runs BEFORE the
    cleanliness verdict, so a Finder dropping is not mistaken for real
    uncommitted work and does not preserve a repo that was otherwise
    perfectly safe to refresh.
    """
    identity = identity_problem(dest=dest, github_url=target.github_url)
    if identity is not None:
        return identity
    marker = in_progress_operation(repo=dest)
    if marker is not None:
        return f"an interrupted git operation is in progress ({marker})"
    swept = sweep_ds_store(repo=dest)
    if swept:
        log.info("deleted untracked .DS_Store files", repo=target.repo, paths=swept)
    dirt = porcelain_status(repo=dest)
    if dirt:
        return f"working tree is not clean: {'; '.join(dirt)}"
    return None


def _currency_problem(*, dest: Path, default_branch: str) -> str | None:
    """Fetch, then judge unpushed work and divergence against what was fetched.

    The fetch comes FIRST and in this same function so the two verdicts
    below cannot be read off a stale `origin/<branch>` — which would make
    already-pushed commits look unpushed and preserve a current repo.
    Returning None means the repo was fast-forwarded.
    """
    fetch_problem = fetch_origin(repo=dest)
    if fetch_problem is not None:
        return fetch_problem
    if unpushed_count(repo=dest) > 0:
        return "the checked-out branch holds commits absent from every origin ref"
    if default_branch_ahead(repo=dest, default_branch=default_branch) > 0:
        return f"local {default_branch} is ahead of or diverged from origin/{default_branch}"
    return fast_forward(repo=dest, default_branch=default_branch)


def _refresh_existing(
    *,
    dest: Path,
    target: RepoTarget,
    default_branch: str,
    log: structlog.stdlib.BoundLogger,
) -> str | None:
    """Refresh an existing destination, or return why it was left untouched."""
    blocking = _blocking_state(dest=dest, target=target, log=log)
    if blocking is not None:
        return blocking
    return _currency_problem(dest=dest, default_branch=default_branch)


def _clone_missing(
    *, target: RepoTarget, dest: Path, log: structlog.stdlib.BoundLogger
) -> str | None:
    """Clone a target that is not present yet; return the failure, or None."""
    clone_problem = _clone(target=target, dest=dest)
    if clone_problem is None:
        log.info("cloned", repo=target.repo, path=str(dest))
        return None
    log.error("clone failed", repo=target.repo, path=str(dest), issue=clone_problem)
    return clone_problem


def _refresh_present(
    *, target: RepoTarget, dest: Path, log: structlog.stdlib.BoundLogger
) -> str | None:
    """Refresh a target that is already present; return the problem, or None."""
    default_branch = _resolved_default_branch(target=target)
    if default_branch is None:
        unresolved = "no registry declares a default branch and `gh repo view` could not supply one"
        log.error("preserved without modification", repo=target.repo, issue=unresolved)
        return unresolved
    problem = _refresh_existing(dest=dest, target=target, default_branch=default_branch, log=log)
    if problem is None:
        log.info("refreshed", repo=target.repo, path=str(dest), default_branch=default_branch)
        return None
    log.error(
        "preserved without modification",
        repo=target.repo,
        path=str(dest),
        issue=problem,
        manual_cleanup=_cleanup_commands(dest=dest, default_branch=default_branch),
    )
    return problem


def _process(
    *, target: RepoTarget, peer_root: Path, log: structlog.stdlib.BoundLogger
) -> str | None:
    """Clone or refresh one target; return the problem that preserved it, or None.

    A broken symlink counts as OCCUPIED rather than missing, so the
    refresher reports it instead of cloning onto whatever it points at.
    """
    dest = peer_root / target.repo
    if not dest.is_symlink() and not dest.exists():
        return _clone_missing(target=target, dest=dest, log=log)
    return _refresh_present(target=target, dest=dest, log=log)


def refresh_tenant_repos(*, project_root: Path) -> int:
    """Clone or refresh every registered repo as a peer of `project_root`'s primary.

    Returns 0 when every target was cloned or refreshed, 1 when at least
    one was preserved or failed, and 2 when the run refused before
    touching anything.
    """
    log = _configure_logger()
    resolution = resolve_targets(
        livespec_config=_parse_jsonc(path=project_root / _CONFIG_NAME),
        fleet_manifest=_parse_jsonc(path=project_root / _MANIFEST_NAME),
    )
    if resolution.conflicts:
        for conflict in resolution.conflicts:
            log.error("refusing to mutate anything: registry conflict", issue=conflict)
        return 2
    preflight = _gh_preflight()
    if preflight is not None:
        log.error("refusing to clone or fetch anything", issue=preflight)
        return 2
    primary = primary_checkout(project_root=project_root)
    if primary is None:
        log.error("project root is not inside a git repository", path=str(project_root))
        return 2
    peer_root = primary.parent
    preserved: list[str] = []
    for target in resolution.targets:
        if _process(target=target, peer_root=peer_root, log=log) is not None:
            preserved.append(target.repo)
    log.info(
        "refresh complete",
        peer_root=str(peer_root),
        targets=[target.repo for target in resolution.targets],
        preserved=preserved,
    )
    return 1 if preserved else 0


def main(*, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="refresh_tenant_repos", add_help=True)
    _ = parser.add_argument(
        "--project-root",
        default=str(Path.cwd()),
        help="the livespec checkout whose registries name the repo set (default: cwd)",
    )
    namespace = parser.parse_args(argv)
    return refresh_tenant_repos(project_root=Path(str(namespace.project_root)).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
