"""Static-phase doctor check: no_stale_merged_branch.

Per `SPECIFICATION/contracts.md` §"Impl-side cleanup invariants
(cross-boundary)" → §"`no-stale-merged-branch`":

  For every local branch whose tip is reachable from the default
  branch (i.e., merged), the invariant fires `warn` with
  corrective action `git branch -d <name>`. Excludes the default
  branch itself. Excludes any branch the user has explicitly
  tagged via project-local config to skip (deferred to a future
  refinement; v1 has no skip-list config key).

  The check fires `warn` (not `fail`) per v074: the underlying
  state is recoverable by user action, so the invariant's role is
  to surface the housekeeping item to the user, not to block the
  build.

  Skip conditions (Finding.status='skipped'):
    - `project_root` is not a git working tree (`is_git_repo`
      returns False).
    - `git symbolic-ref refs/remotes/origin/HEAD` is unset (no
      remote tracking or no clone), so the default branch is
      undetermined.
    - `git for-each-ref --merged refs/heads/<default>` fails for
      any other reason (lifted via the io.git seam).
"""

from __future__ import annotations

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import git as io_git
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-no-stale-merged-branch")


def _pass(*, ctx: DoctorContext, message: str) -> Finding:
    """Build a pass-status Finding."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _skipped(*, ctx: DoctorContext, message: str) -> Finding:
    """Build a skipped-status Finding."""
    return Finding(
        check_id=SLUG,
        status="skipped",
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _warn(*, ctx: DoctorContext, message: str) -> Finding:
    """Build a warn-status Finding (v074: warn added for housekeeping nudges)."""
    return Finding(
        check_id=SLUG,
        status="warn",
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _evaluate_merged(
    *,
    ctx: DoctorContext,
    default_branch: str,
    merged: tuple[str, ...],
) -> Finding:
    """Build the pass-or-warn Finding from the merged-branches enumeration.

    The for-each-ref result INCLUDES `default_branch` itself; the
    branch-deletion narration in the warn message excludes it.
    Empty stale-set (no branches merged into default other than
    default itself) is the clean case and surfaces as pass.
    """
    stale = sorted(branch for branch in merged if branch != default_branch)
    if not stale:
        return _pass(
            ctx=ctx,
            message=(
                f"no-stale-merged-branch: no local branches merged into "
                f"`{default_branch}` (default branch itself excluded)"
            ),
        )
    branches_joined = ", ".join(stale)
    corrective = "; ".join(f"git branch -d {name}" for name in stale)
    return _warn(
        ctx=ctx,
        message=(
            f"no-stale-merged-branch: {len(stale)} local branch(es) merged "
            f"into `{default_branch}` and ready to delete: {branches_joined}. "
            f"Corrective action: {corrective}"
        ),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run no-stale-merged-branch against `ctx`.

    Composes is_git_repo → get_default_branch_name →
    list_merged_branches → _evaluate_merged. Any failure on the
    IO track is lashed into a skipped-status Finding so the
    orchestrator's stdout contract stays uniform; non-git
    project_roots surface a skipped finding rather than an
    IOFailure.
    """
    project_root = ctx.project_root
    return (
        io_git.is_git_repo(project_root=project_root)
        .bind(
            lambda is_repo: (
                io_git.get_default_branch_name(project_root=project_root).bind(
                    lambda default_branch: io_git.list_merged_branches(
                        project_root=project_root,
                        into_ref=default_branch,
                    ).map(
                        lambda merged: _evaluate_merged(
                            ctx=ctx,
                            default_branch=default_branch,
                            merged=merged,
                        ),
                    ),
                )
                if is_repo
                else IOResult.from_value(
                    _skipped(
                        ctx=ctx,
                        message=(
                            "no-stale-merged-branch: project_root is not a git "
                            "working tree; check skipped"
                        ),
                    ),
                )
            ),
        )
        .lash(
            lambda err: IOSuccess(
                _skipped(
                    ctx=ctx,
                    message=(
                        f"no-stale-merged-branch: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                ),
            ),
        )
    )
