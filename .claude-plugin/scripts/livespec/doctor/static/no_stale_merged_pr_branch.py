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
"""Static-phase doctor check: no_stale_merged_pr_branch.

Per `SPECIFICATION/contracts.md` §"Impl-side cleanup invariants
(cross-boundary)" → §"`no-stale-merged-pr-branch`":

For every GitHub branch in `gh api repos/<owner>/<name>/branches`
that is fronted by a `state == "MERGED"` PR (queried via
`gh pr list --state merged --json headRefName,state`), the
invariant fires `warn` with corrective action
`gh api -X DELETE repos/<owner>/<name>/git/refs/heads/<name>`.
The check runs against the CURRENT repo only; sibling-repo
cleanup is the sibling-repo project's responsibility. The
default branch is excluded.

The check fires `warn` (not `fail`) per the spec: the underlying
state is recoverable by user action; the invariant's role is to
surface the housekeeping item, not to block the build.

Skip conditions (Finding.status='skipped'):
  - `project_root` is not a git working tree
    (`io_git.is_git_repo` returns False).
  - `gh` CLI unavailable or unauthenticated (proc seam lifts to
    PreconditionError; the lash branch catches it).
  - The repo has no origin remote on GitHub (gh exits non-zero;
    same lash branch).
  - The local origin's default branch is undetermined
    (`io_git.get_default_branch_name` failure).
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import gh as io_gh
from livespec.io import git as io_git
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-no-stale-merged-pr-branch")


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
    name_with_owner: str,
    remote_branches: tuple[str, ...],
    merged_head_refs: tuple[str, ...],
) -> Finding:
    """Build the pass-or-warn Finding from the remote-branch + merged-PR sets.

    Stale = remote branches whose name appears in the merged-PR
    head-refs set AND is not the default branch. The corrective
    action is one `gh api -X DELETE` invocation per stale branch,
    templated with the resolved `<owner>/<name>` so the user can
    paste the narration directly. Empty stale-set is the clean
    case and surfaces as pass.
    """
    merged_set = set(merged_head_refs)
    stale = sorted(
        name for name in remote_branches if name != default_branch and name in merged_set
    )
    if not stale:
        return _pass(
            ctx=ctx,
            message=(
                f"no-stale-merged-pr-branch: no remote branches fronted by "
                f"merged PRs to clean up ({len(remote_branches)} remote "
                f"branch(es) scanned, {len(merged_head_refs)} merged PR(s); "
                f"default branch `{default_branch}` excluded)"
            ),
        )
    branches_joined = ", ".join(stale)
    corrective = "; ".join(
        f"gh api -X DELETE repos/{name_with_owner}/git/refs/heads/{name}" for name in stale
    )
    return _warn(
        ctx=ctx,
        message=(
            f"no-stale-merged-pr-branch: {len(stale)} remote branch(es) fronted "
            f"by merged PR(s) and ready to delete: {branches_joined}. "
            f"Corrective action: {corrective}"
        ),
    )


def _evaluate_intersection(
    *,
    ctx: DoctorContext,
    project_root: Path,
    default_branch: str,
) -> IOResult[Finding, LivespecError]:
    """Gather repo identity + remote branches + merged PR head refs, then evaluate.

    Factored out of `run` so the nested compose-bind chain stays
    readable; each gh-side primitive is called once and threaded
    through the next bind. The outer `run` retains the
    is_git_repo gate and the lash-to-skipped catch-all.
    """
    return io_gh.get_repo_name_with_owner(project_root=project_root).bind(
        lambda name_with_owner: io_gh.list_remote_branches(
            project_root=project_root,
        ).bind(
            lambda remote_branches: io_gh.list_merged_pull_request_head_refs(
                project_root=project_root,
            ).map(
                lambda merged_head_refs: _evaluate(
                    ctx=ctx,
                    default_branch=default_branch,
                    name_with_owner=name_with_owner,
                    remote_branches=remote_branches,
                    merged_head_refs=merged_head_refs,
                ),
            ),
        ),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run no-stale-merged-pr-branch against `ctx`.

    Composes is_git_repo → get_default_branch_name →
    (gh repo view + gh api repos/branches + gh pr list merged) →
    `_evaluate`. Any failure on the IO track lashes back into a
    skipped-status Finding so the orchestrator's stdout contract
    stays uniform; non-git project_roots surface a skipped finding
    rather than an IOFailure.
    """
    project_root = ctx.project_root
    return (
        io_git.is_git_repo(project_root=project_root)
        .bind(
            lambda is_repo: (
                io_git.get_default_branch_name(project_root=project_root).bind(
                    lambda default_branch: _evaluate_intersection(
                        ctx=ctx,
                        project_root=project_root,
                        default_branch=default_branch,
                    ),
                )
                if is_repo
                else IOResult.from_value(
                    _skipped(
                        ctx=ctx,
                        message=(
                            "no-stale-merged-pr-branch: project_root is not a git "
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
                        f"no-stale-merged-pr-branch: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                ),
            ),
        )
    )
