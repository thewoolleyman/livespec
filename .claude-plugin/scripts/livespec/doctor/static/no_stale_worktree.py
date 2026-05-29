# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. Per-call cast
# or refactor to named typed functions is the canonical fix; this file's
# railway composition pattern means roughly half of all lines are bind
# targets, so file-level silencing keeps the source readable. Non-railway
# code in this tree retains full enforcement (other modules do not carry
# this pragma). reportArgumentType is left ON so non-HKT firings still
# surface; HKT-related reportArgumentType call sites carry per-line
# ignore markers attached to the offending argument's line below.
"""Static-phase doctor check: no_stale_worktree.

Per `SPECIFICATION/contracts.md` §"Impl-side cleanup invariants
(cross-boundary)" → §"`no-stale-worktree`":

  For every git worktree (per `git worktree list --porcelain`)
  whose underlying branch is either (a) merged into default and
  locally deleted, or (b) absent from the remote, the invariant
  fires `warn` with corrective action `git worktree remove <path>`.
  Excludes the primary worktree.

  The check surfaces the UNION of both cases. A secondary
  worktree is stale when its branch is either (a) in the
  `git branch --merged <default>` set (reachable from default)
  OR (b) absent from the remote head set
  (`git ls-remote --heads origin`). Case (b) is load-bearing for
  the family's `gh pr merge --rebase` flow: a rebase-merge lands a
  DISTINCT SHA on default, so the merged branch is NOT an ancestor
  and never lists under `--merged` — case (a) is blind to it. Its
  only durable cleanup signal is remote absence (the branch was
  deleted on the remote after its PR merged). This case-(b)
  coverage is the regression the uncaught orphan worktrees
  exposed; the sibling `no-stale-merged-pr-branch` check addresses
  the DIFFERENT cleanup artifact (`gh api -X DELETE
  refs/heads/<name>`) and is unaffected.

  The check fires `warn` (v074) when stale worktrees exist;
  fires `pass` when the only worktree is primary OR all
  secondary worktrees are on branches that are both unmerged AND
  still present on the remote; fires `skipped` when the project
  is not a git repo, when `origin/HEAD` is unset (default branch
  undetermined), or when the remote head query fails (no reachable
  origin).
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
    remote_branches: tuple[str, ...],
    worktrees: tuple[io_git.Worktree, ...],
) -> Finding:
    """Build the pass-or-warn Finding from the worktree, merged, and remote sets.

    A secondary worktree is flagged stale when its branch is
    either (a) in the `merged`-into-default set OR (b) absent from
    the `remote_branches` head set. The default branch itself is
    excluded from case (a) (a branch is trivially reachable from
    itself; the primary worktree is typically on the default
    branch). Case (b) is the rebase-merged-then-deleted signal —
    the merged branch is not a default-ancestor, so it never lists
    under `--merged`, but the remote head is gone. The primary
    worktree is always excluded per the contract.
    """
    stale_paths = sorted(
        str(wt.path)
        for wt in worktrees
        if not wt.is_primary
        and wt.branch is not None
        and wt.branch != default_branch
        and (wt.branch in merged or wt.branch not in remote_branches)
    )
    if not stale_paths:
        return _pass(
            ctx=ctx,
            message=(
                f"no-stale-worktree: no secondary worktrees on branches merged "
                f"into `{default_branch}` or absent from the remote "
                f"({len(worktrees)} worktree(s) scanned)"
            ),
        )
    paths_joined = ", ".join(stale_paths)
    corrective = "; ".join(f"git worktree remove {path}" for path in stale_paths)
    return _warn(
        ctx=ctx,
        message=(
            f"no-stale-worktree: {len(stale_paths)} secondary worktree(s) on "
            f"branches merged into `{default_branch}` or absent from the remote "
            f"and ready to clean up: {paths_joined}. Corrective action: {corrective}"
        ),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run no-stale-worktree against `ctx`.

    Composes is_git_repo → get_default_branch_name →
    list_merged_branches → list_remote_branches → list_worktrees →
    _evaluate. The merged set drives case (a); the remote head set
    drives case (b) (a worktree branch absent from the remote is
    stale). Any failure on the IO track — including a failed
    `ls-remote` (no reachable origin) — is lashed into a
    skipped-status Finding so the orchestrator's stdout contract
    stays uniform.
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
                        lambda merged: io_git.list_remote_branches(
                            project_root=project_root,
                        ).bind(
                            lambda remote_branches: io_git.list_worktrees(
                                project_root=project_root,
                            ).map(
                                lambda worktrees: _evaluate(
                                    ctx=ctx,
                                    default_branch=default_branch,
                                    merged=merged,
                                    remote_branches=remote_branches,
                                    worktrees=worktrees,
                                ),
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
