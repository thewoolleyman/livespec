"""One repo's pass: resolve its identity, then clone it or refresh it safely.

This is where the refresher's whole safety ORDER lives, and the order is
the design. The canonical identity is resolved FIRST, from GitHub, before
a clone URL is built or an existing `origin` is judged — a registry
records the pair a repo was adopted under, and a rename or transfer
leaves that pair as a redirect. Then, for a repo already present:
identity, interrupted-operation state, the `.DS_Store` sweep, the
cleanliness verdict, the fetch, and only then the unpushed and divergence
verdicts the fetch makes trustworthy. Every refusal short-circuits before
the next step can write anything.

The orchestrator above this (`refresh_tenant_repos`) owns the registry,
the preflight, and the loop; this module owns what happens to ONE repo,
and `process_target` is the single entry point between them.
"""

# livespec-lloc-soft-band-owner: livespec-odb6me
# This file sat at EXACTLY the 200-LLOC soft ceiling before the
# in-progress markers were threaded through it, so carrying them crossed
# the band by one line rather than by any growth worth that warning. The
# refactor the band is asking for is a cohesion split of this module's
# three concerns — identity resolution, the blocking-state order, and the
# post-fetch landing verdicts — which is a structural change the narrow
# follow-up that crossed the line deliberately did not take on.
# The named backlog item owns that remaining refactor, not the completed
# marker-reporting follow-up; its extraction boundaries still need grooming.

from __future__ import annotations

import sys
from pathlib import Path

_DEV_TOOLING_DIR = Path(__file__).resolve().parent
if str(_DEV_TOOLING_DIR) not in sys.path:
    sys.path.insert(0, str(_DEV_TOOLING_DIR))

import structlog  # noqa: E402  — path-aware import after sys.path insert.
from refresh_tenant_repos_git import (  # noqa: E402
    clone_https,
    default_branch_ahead,
    fast_forward,
    fetch_https,
    identity_problem,
    in_progress_operation,
    porcelain_status,
    sweep_ds_store,
    unpushed_count,
)
from refresh_tenant_repos_identity import canonical_identity, https_url  # noqa: E402
from refresh_tenant_repos_registry import RepoTarget  # noqa: E402
from refresh_tenant_repos_report import (  # noqa: E402
    CLONE_FAILED,
    DIVERGED,
    FETCH_FAILED,
    IDENTITY_MISMATCH,
    INSPECTION_FAILED,
    INTERRUPTED,
    UNCOMMITTED,
    UNPUSHED,
    UNRESOLVED_BRANCH,
    RepoProblem,
    cleanup_commands,
)

__all__: list[str] = ["process_target"]

_NO_BRANCH = "no registry declares a default branch and GitHub reports none either"


def _preserved(
    *,
    dest: Path,
    target: RepoTarget,
    problem: RepoProblem,
    default_branch: str | None,
    log: structlog.stdlib.BoundLogger,
) -> RepoProblem:
    """Report one preserved repo with the cleanup commands its state calls for."""
    log.error(
        "preserved without modification",
        repo=target.repo,
        path=str(dest),
        state=problem.state,
        issue=problem.detail,
        manual_cleanup=cleanup_commands(
            dest=dest, default_branch=default_branch, state=problem.state, markers=problem.markers
        ),
    )
    return problem


def _cleanliness_problem(
    *, dest: Path, target: RepoTarget, log: structlog.stdlib.BoundLogger
) -> RepoProblem | None:
    """Uncommitted work at `dest`, a failed status inspection, or None when clean.

    The `.DS_Store` sweep runs BEFORE the cleanliness verdict, so a
    Finder dropping is not mistaken for real uncommitted work and does
    not preserve a repo that was otherwise perfectly safe to refresh.
    """
    status = porcelain_status(repo=dest)
    if status.problem is not None:
        return RepoProblem(state=INSPECTION_FAILED, detail=status.problem)
    swept = sweep_ds_store(repo=dest, status_lines=status.values)
    if swept.removed:
        log.info("deleted untracked .DS_Store files", repo=target.repo, paths=list(swept.removed))
    if swept.remaining:
        return RepoProblem(
            state=UNCOMMITTED,
            detail=f"working tree is not clean: {'; '.join(swept.remaining)}",
        )
    return None


def _blocking_state(
    *,
    dest: Path,
    target: RepoTarget,
    accepted_urls: tuple[str, ...],
    log: structlog.stdlib.BoundLogger,
) -> RepoProblem | None:
    """What makes `dest` untouchable BEFORE anything is fetched or deleted, or None.

    Order is the safety design. Identity settles FIRST, so a destination
    on another host — or naming neither the registered nor the canonical
    repository — is reported before a fetch or a `.DS_Store` deletion
    could reach it. Interrupted-operation state settles next, and only
    then does the sweep run and the cleanliness verdict follow.
    """
    identity = identity_problem(dest=dest, accepted_urls=accepted_urls)
    if identity is not None:
        return RepoProblem(state=IDENTITY_MISMATCH, detail=identity)
    progress = in_progress_operation(repo=dest)
    if progress.problem is not None:
        return RepoProblem(state=INSPECTION_FAILED, detail=progress.problem)
    if progress.values:
        # The MARKERS travel with the problem, not just the sentence: they
        # are what lets the report name the operation to finish or abandon,
        # and the state alone cannot — a `merge --abort` is no use to a
        # half-finished cherry-pick.
        return RepoProblem(
            state=INTERRUPTED,
            detail=f"an interrupted git operation is in progress ({', '.join(progress.values)})",
            markers=progress.values,
        )
    return _cleanliness_problem(dest=dest, target=target, log=log)


def _landing_problem(*, dest: Path, default_branch: str) -> RepoProblem | None:
    """Unpushed work, divergence, or a refused fast-forward — all judged post-fetch.

    Returning None means the repo was landed on `default_branch` and
    fast-forwarded.
    """
    unpushed = unpushed_count(repo=dest)
    if unpushed.problem is not None:
        return RepoProblem(state=INSPECTION_FAILED, detail=unpushed.problem)
    if unpushed.count > 0:
        return RepoProblem(
            state=UNPUSHED,
            detail="the checked-out branch holds commits absent from every origin ref",
        )
    ahead = default_branch_ahead(repo=dest, default_branch=default_branch)
    if ahead.problem is not None:
        return RepoProblem(state=INSPECTION_FAILED, detail=ahead.problem)
    if ahead.count > 0:
        return RepoProblem(
            state=DIVERGED,
            detail=f"local {default_branch} is ahead of or diverged from origin/{default_branch}",
        )
    landed = fast_forward(repo=dest, default_branch=default_branch)
    if landed is None:
        return None
    return RepoProblem(state=UNRESOLVED_BRANCH, detail=landed)


def _currency_problem(*, dest: Path, url: str, default_branch: str) -> RepoProblem | None:
    """Fetch over HTTPS, then judge unpushed work and divergence against it.

    The fetch comes FIRST so the verdicts below cannot be read off a
    stale `origin/<branch>` — which would make already-pushed commits
    look unpushed and preserve a current repo.
    """
    fetch_problem = fetch_https(repo=dest, url=url)
    if fetch_problem is not None:
        return RepoProblem(state=FETCH_FAILED, detail=fetch_problem)
    return _landing_problem(dest=dest, default_branch=default_branch)


def _clone_missing(
    *,
    target: RepoTarget,
    url: str,
    dest: Path,
    default_branch: str,
    log: structlog.stdlib.BoundLogger,
) -> RepoProblem | None:
    """Clone a target that is not present yet and prove the result is usable.

    A clone is not reported as done until it is ON the configured default
    branch with a clean tree: a clone checks out whatever GitHub calls
    default, which is not necessarily the branch a registry declared, and
    a clone left on the wrong branch is exactly the state the refresher
    exists to prevent.
    """
    clone_problem = clone_https(url=url, dest=dest)
    if clone_problem is not None:
        log.error("clone failed", repo=target.repo, path=str(dest), issue=clone_problem)
        return RepoProblem(state=CLONE_FAILED, detail=clone_problem)
    landed = fast_forward(repo=dest, default_branch=default_branch)
    if landed is not None:
        return _preserved(
            dest=dest,
            target=target,
            problem=RepoProblem(state=UNRESOLVED_BRANCH, detail=landed),
            default_branch=default_branch,
            log=log,
        )
    unclean = _cleanliness_problem(dest=dest, target=target, log=log)
    if unclean is not None:
        return _preserved(
            dest=dest, target=target, problem=unclean, default_branch=default_branch, log=log
        )
    log.info("cloned", repo=target.repo, path=str(dest), default_branch=default_branch)
    return None


def _refresh_present(
    *,
    target: RepoTarget,
    dest: Path,
    accepted_urls: tuple[str, ...],
    url: str,
    default_branch: str,
    log: structlog.stdlib.BoundLogger,
) -> RepoProblem | None:
    """Refresh a target that is already present; report why it was left untouched."""
    problem = _blocking_state(
        dest=dest, target=target, accepted_urls=accepted_urls, log=log
    ) or _currency_problem(dest=dest, url=url, default_branch=default_branch)
    if problem is not None:
        return _preserved(
            dest=dest, target=target, problem=problem, default_branch=default_branch, log=log
        )
    log.info("refreshed", repo=target.repo, path=str(dest), default_branch=default_branch)
    return None


def process_target(
    *, target: RepoTarget, peer_root: Path, log: structlog.stdlib.BoundLogger
) -> RepoProblem | None:
    """Clone or refresh one target; return the problem that preserved it, or None.

    A broken symlink counts as OCCUPIED rather than missing, so the
    refresher reports it instead of cloning onto whatever it points at.
    """
    dest = peer_root / target.repo
    resolution = canonical_identity(owner=target.owner, repo=target.repo)
    identity = resolution.identity
    if identity is None:
        return _preserved(
            dest=dest,
            target=target,
            problem=RepoProblem(
                state=IDENTITY_MISMATCH,
                detail=resolution.problem or "GitHub reported no canonical identity",
            ),
            default_branch=None,
            log=log,
        )
    default_branch = target.default_branch or identity.default_branch
    if default_branch is None:
        return _preserved(
            dest=dest,
            target=target,
            problem=RepoProblem(state=UNRESOLVED_BRANCH, detail=_NO_BRANCH),
            default_branch=None,
            log=log,
        )
    # Every fetch addresses the CANONICAL URL, while a clone still
    # carrying the registered URL stays acceptable to validate against.
    url = https_url(name_with_owner=identity.name_with_owner)
    accepted_urls = (target.github_url, url)
    if not dest.is_symlink() and not dest.exists():
        return _clone_missing(
            target=target, url=url, dest=dest, default_branch=default_branch, log=log
        )
    return _refresh_present(
        target=target,
        dest=dest,
        accepted_urls=accepted_urls,
        url=url,
        default_branch=default_branch,
        log=log,
    )
