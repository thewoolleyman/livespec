"""Static-phase doctor check: no_stale_worktree.

Per `SPECIFICATION/contracts.md` §"Impl-side cleanup invariants
(cross-boundary)" → §"`no-stale-worktree`":

  For every git worktree (per `git worktree list --porcelain`)
  whose underlying branch is either (a) merged into default and
  locally deleted, or (b) absent from the remote, the invariant
  fires `warn` with corrective action `git worktree remove <path>`.
  Excludes the primary worktree.

  v1 implementation: surface case (a) only — worktrees whose
  branch is merged into the default branch. Case (b) (remote
  absence) is deferred to the gh-CLI integration of
  `no-stale-merged-pr-branch`; the two checks share the same
  "remote branch missing" signal but address different cleanup
  artifacts (`gh api -X DELETE refs/heads/<name>` vs
  `git worktree remove <path>`). A future cycle MAY widen this
  check to also surface case (b) once the gh facade lands.

  The check fires `warn` (v074) when stale worktrees exist;
  fires `pass` when the only worktree is primary OR all
  secondary worktrees are on unmerged branches; fires `skipped`
  when the project is not a git repo OR when `origin/HEAD` is
  unset (default branch undetermined).
"""

from __future__ import annotations

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import git as io_git
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-no-stale-worktree")


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
    """Build a warn-status Finding (v074 status enum)."""
    return Finding(
        check_id=SLUG,
        status="warn",
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _evaluate(
    *,
    ctx: DoctorContext,
    default_branch: str,
    merged: tuple[str, ...],
    worktrees: tuple[io_git.Worktree, ...],
) -> Finding:
    """Build the pass-or-warn Finding from the worktree + merged-branch sets.

    Secondary worktrees whose branch is in the merged-into-default
    set (excluding the default branch itself; the primary worktree
    is typically on the default branch) are flagged as stale. The
    primary worktree is always excluded per the contract.
    """
    stale_paths = sorted(
        str(wt.path)
        for wt in worktrees
        if not wt.is_primary
        and wt.branch is not None
        and wt.branch != default_branch
        and wt.branch in merged
    )
    if not stale_paths:
        return _pass(
            ctx=ctx,
            message=(
                f"no-stale-worktree: no secondary worktrees on branches merged "
                f"into `{default_branch}` ({len(worktrees)} worktree(s) scanned)"
            ),
        )
    paths_joined = ", ".join(stale_paths)
    corrective = "; ".join(f"git worktree remove {path}" for path in stale_paths)
    return _warn(
        ctx=ctx,
        message=(
            f"no-stale-worktree: {len(stale_paths)} secondary worktree(s) on "
            f"branches merged into `{default_branch}` and ready to clean up: "
            f"{paths_joined}. Corrective action: {corrective}"
        ),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run no-stale-worktree against `ctx`.

    Composes is_git_repo → get_default_branch_name →
    list_merged_branches + list_worktrees → _evaluate. Any
    failure on the IO track is lashed into a skipped-status
    Finding so the orchestrator's stdout contract stays uniform.
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
                    ).bind(
                        lambda merged: io_git.list_worktrees(
                            project_root=project_root,
                        ).map(
                            lambda worktrees: _evaluate(
                                ctx=ctx,
                                default_branch=default_branch,
                                merged=merged,
                                worktrees=worktrees,
                            ),
                        ),
                    ),
                )
                if is_repo
                else IOResult.from_value(
                    _skipped(
                        ctx=ctx,
                        message=(
                            "no-stale-worktree: project_root is not a git "
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
                        f"no-stale-worktree: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                ),
            ),
        )
    )
