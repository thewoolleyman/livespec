"""Static-phase doctor check: out_of_band_edits.

Per Plan Phase 7 sub-step 7.a + PROPOSAL.md §"`doctor` →
Static-phase checks": the `out-of-band-edits` check detects
working-tree spec files whose contents have diverged from their
HEAD blob (i.e., edits made directly to the working tree without
the propose-change → revise pipeline). It is the only doctor
check whose `run()` has a narrow auto-backfill write path (per
`static/CLAUDE.md`); divergence detection + auto-backfill land
in cycles 7.a.iii / 7.a.iv.

Cycle 7.a.ii lands the smallest viable skeleton: it discriminates
on whether `ctx.spec_root` is inside a git working tree. The
behavior:

  - Non-git project (no surrounding git repo) → skipped-Finding.
    Per PROPOSAL §"Static-phase checks": "skip the out-of-band
    check, the project isn't versioned." Non-git is an EXPECTED
    business outcome — it MUST NOT lift to IOFailure.

  - Git-versioned project → placeholder pass-Finding. The actual
    divergence-detection logic (composing on top of the
    `show_at_head` primitive landed in 7.a.i) lands in 7.a.iv.
    The placeholder keeps the project's own aggregate `just
    check` gate green: the project IS a git repo, so the check
    runs against itself and the placeholder yields pass.

Per v018 Q1: applies to all spec-text-bearing trees (main +
each sub-spec).
"""

from __future__ import annotations

from returns.io import IOResult

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io.git import is_git_repo
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "doctor-out-of-band-edits"


def _skipped_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical skipped-status Finding for this check.

    Emitted when `ctx.spec_root` is not inside a git working
    tree. The non-versioned outcome is expected (PROPOSAL
    §"Static-phase checks": "skip the out-of-band check, the
    project isn't versioned") so it stays on the success rail
    with `status="skipped"`.
    """
    return Finding(
        check_id=SLUG,
        status="skipped",
        message="spec_root is not inside a git working tree",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the placeholder pass-status Finding for this check.

    Cycle 7.a.ii placeholder: keeps the aggregate `just check`
    gate green for git-versioned projects until 7.a.iv replaces
    this with real divergence detection. Documenting WHY (not
    WHAT) per the project's docstring discipline: this is a
    deliberate incremental-TDD seam, not the final behavior.
    """
    return Finding(
        check_id=SLUG,
        status="pass",
        message=(
            "no out-of-band edits detected (placeholder; divergence " "detection lands in 7.a.iv)"
        ),
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _select_finding(*, ctx: DoctorContext, in_git_repo: bool) -> Finding:
    """Select the skipped- or pass-Finding based on the git-repo discriminator.

    Pure helper: receives the `is_git_repo` boolean (already
    unwrapped from the IO track by the caller's `.map`) and
    returns the canonical Finding for this cycle's two pinned
    behaviors. Cycle 7.a.iv replaces the True branch with the
    real divergence-detection ROP composition.
    """
    if in_git_repo:
        return _pass_finding(ctx=ctx)
    return _skipped_finding(ctx=ctx)


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the out-of-band-edits check against `ctx`.

    Composes `is_git_repo(project_root=ctx.spec_root)` with a
    pure finding-selector. The non-repo case yields
    IOSuccess(Finding(status="skipped")); the repo case yields
    IOSuccess(Finding(status="pass")) as a deliberate placeholder
    until 7.a.iv lands the real divergence detection.

    `ctx.spec_root` is passed to `is_git_repo` rather than
    `ctx.project_root` because `git rev-parse
    --is-inside-work-tree` resolves against any path inside the
    working tree — using `spec_root` lets the check work
    uniformly for the main spec tree AND each sub-spec tree
    (the sub-spec tree's `spec_root` may be a subdirectory of
    the main tree but is still inside the same git repo).
    """
    return is_git_repo(project_root=ctx.spec_root).map(
        lambda in_git_repo: _select_finding(ctx=ctx, in_git_repo=in_git_repo),
    )
