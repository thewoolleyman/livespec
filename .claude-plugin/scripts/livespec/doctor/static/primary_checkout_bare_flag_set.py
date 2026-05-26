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
"""Static-phase doctor check: primary_checkout_bare_flag_set.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary
invariants" → §"`primary-checkout-bare-flag-set`":

Every livespec-governed primary checkout MUST have
`core.bare = true` set in its `.git/config`. The check reads the
primary checkout's `core.bare` value via `git config --get`,
which by git's design resolves to the common config (the primary
checkout's `.git/config` even when invoked from a secondary
worktree, since `core.bare` is not in the worktree-config-allowed
key set). The check fires `fail` when the value is absent OR
explicitly set to `false`; the invariant MUST NOT distinguish
between the two — both are corrected by the same bootstrap
invocation.

The narration directs the user to the documented bootstrap step
in `SPECIFICATION/non-functional-requirements.md` §"Bare-flag
bootstrap procedure" and includes the literal corrective command
`git config core.bare true` so the resolution is one terminal
invocation away.

Skip conditions (Finding.status='skipped'):
  - `project_root` is not a git working tree (`is_git_repo`
    returns False), OR
  - `get_core_bare` lifts a precondition failure (lashed into a
    skipped finding so the orchestrator's stdout contract stays
    uniform).

The check applies to the PRIMARY checkout only; secondary
worktrees carry a standalone `.git` FILE pointing back to the
bare repo and are not inspected.
"""

from __future__ import annotations

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import git as io_git
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-primary-checkout-bare-flag-set")


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


def _fail(*, ctx: DoctorContext, message: str) -> Finding:
    """Build a fail-status Finding."""
    return Finding(
        check_id=SLUG,
        status="fail",
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


def _evaluate(*, ctx: DoctorContext, core_bare: bool) -> Finding:
    """Build the pass-or-fail Finding from the resolved `core.bare` value.

    Per contract, absent and explicit-`false` are not
    distinguished — both fire `fail` with the same corrective
    narration pointing at the bootstrap step.
    """
    if core_bare:
        return _pass(
            ctx=ctx,
            message=(
                "primary-checkout-bare-flag-set: `core.bare = true` is set on "
                "the primary checkout's `.git/config`"
            ),
        )
    return _fail(
        ctx=ctx,
        message=(
            "primary-checkout-bare-flag-set: `core.bare` is absent or `false` "
            "on the primary checkout's `.git/config`. Corrective action: run "
            "the documented bootstrap step (see "
            '`non-functional-requirements.md` §"Bare-flag bootstrap '
            'procedure"), which idempotently invokes `git config core.bare '
            "true` against the primary checkout."
        ),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run primary-checkout-bare-flag-set against `ctx`.

    Composes is_git_repo → get_core_bare → _evaluate. Any failure
    on the IO track is lashed into a skipped-status Finding so the
    orchestrator's stdout contract stays uniform; non-git
    project_roots surface a skipped finding rather than an
    IOFailure.
    """
    project_root = ctx.project_root
    return (
        io_git.is_git_repo(project_root=project_root)
        .bind(
            lambda is_repo: (
                io_git.get_core_bare(project_root=project_root).map(
                    lambda core_bare: _evaluate(ctx=ctx, core_bare=core_bare),
                )
                if is_repo
                else IOResult.from_value(
                    _skipped(
                        ctx=ctx,
                        message=(
                            "primary-checkout-bare-flag-set: project_root is "
                            "not a git working tree; check skipped"
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
                        f"primary-checkout-bare-flag-set: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                ),
            ),
        )
    )
