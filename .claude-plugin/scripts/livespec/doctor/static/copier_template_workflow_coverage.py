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
"""Static-phase doctor check: copier_template_workflow_coverage.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary
invariants" → §"`copier-template-workflow-coverage`":

The invariant applies ONLY to project roots that are
copier-template consumers, detected by the presence of a
`.copier-answers.yml` file at the project root. A project root
that does NOT carry `.copier-answers.yml` is out of scope: the
check emits a single non-failing `skipped` finding and does NOT
inspect `.github/workflows/`. Only `livespec-impl-*` consumers
generated from the impl-plugin copier template carry that marker;
`livespec` itself, `livespec-dev-tooling`, `livespec-runtime`,
and other non-consumer repos legitimately carry a different
workflow set and are exempt.

For consumer repositories (marker present), the repo MUST contain
a `.github/workflows/` directory whose set of workflow files is a
SUPERSET of the required-file list enumerated in §"Shared
content sync — copier template". The check fires `fail` for
every required workflow file that is missing from the
consumer's `.github/workflows/`. Each fail finding names the
specific missing file(s) and directs the user to run
`copier update --vcs-ref=master` to re-sync from the template.

The required-file list is hard-coded in this module per the v1
contract clause: "for v1, the doctor invariant MAY hard-code
the list and rely on PR review to catch drift". A paired
enforcement-suite check in `livespec-dev-tooling` will catch
drift between the contract list and the hard-coded list once
that sibling propose-change lands.

When `.github/workflows/` is absent entirely the check fires a
single `fail` finding naming every required file, since the
corrective action (run `copier update --vcs-ref=master`) is
identical to the
"one or more missing files" case.
"""

from __future__ import annotations

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["REQUIRED_WORKFLOW_FILES", "SLUG", "run"]


SLUG: CheckId = CheckId("doctor-copier-template-workflow-coverage")


REQUIRED_WORKFLOW_FILES: tuple[str, ...] = (
    "auto-enable-merge.yml",
    "bump-pin-from-dispatch.yml",
    "ci.yml",
    "copier-update-drift.yml",
    "pin-freshness.yml",
    "release-dispatch.yml",
)


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
    """Build a skipped-status Finding (non-failing precondition-not-met).

    Emitted when the project root is not a copier-template
    consumer (no `.copier-answers.yml` marker), so the
    workflow-coverage invariant does not apply.
    """
    return Finding(
        check_id=SLUG,
        status="skipped",
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _evaluate(*, ctx: DoctorContext) -> Finding:
    """Build the skip-or-pass-or-fail Finding for the project root.

    Per `SPECIFICATION/contracts.md`
    §"`copier-template-workflow-coverage`", the invariant applies
    ONLY to copier-template consumers, detected by a
    `.copier-answers.yml` file at the project root. When that
    marker is absent the project root is out of scope: the check
    returns a single non-failing `skipped` finding WITHOUT
    inspecting `.github/workflows/`.

    For consumer roots (marker present) the check walks
    `<project_root>/.github/workflows/` and compares its file set
    against `REQUIRED_WORKFLOW_FILES`. When every required file is
    present, the check passes. When one or more required files are
    missing — including the case where `.github/workflows/` does
    not exist at all — the check fires a single `fail` finding
    naming the missing files and directing the user to
    `copier update --vcs-ref=master`.
    """
    copier_answers = ctx.project_root / ".copier-answers.yml"
    if not copier_answers.exists():
        return _skipped(
            ctx=ctx,
            message=(
                "copier-template-workflow-coverage: project root is not a "
                "copier-template consumer (`.copier-answers.yml` is absent); "
                "the invariant applies only to `livespec-impl-*` consumers "
                "generated from the impl-plugin copier template, so the "
                "workflow-coverage check is not applicable here."
            ),
        )
    workflows_dir = ctx.project_root / ".github" / "workflows"
    if not workflows_dir.is_dir():
        missing = list(REQUIRED_WORKFLOW_FILES)
        missing_joined = ", ".join(missing)
        return _fail(
            ctx=ctx,
            message=(
                f"copier-template-workflow-coverage: "
                f"`.github/workflows/` directory is absent from project root; "
                f"all {len(missing)} required workflow file(s) are missing: "
                f"{missing_joined}. Corrective action: run `copier update --vcs-ref=master` to "
                f"re-sync the copier template (see `non-functional-requirements.md` "
                f'§"Shared content sync — copier template" for the canonical '
                f"required-file list)."
            ),
        )
    present_names = {entry.name for entry in workflows_dir.iterdir() if entry.is_file()}
    missing = [name for name in REQUIRED_WORKFLOW_FILES if name not in present_names]
    if not missing:
        return _pass(
            ctx=ctx,
            message=(
                f"copier-template-workflow-coverage: all "
                f"{len(REQUIRED_WORKFLOW_FILES)} required workflow file(s) "
                f"are present in `.github/workflows/`"
            ),
        )
    missing_joined = ", ".join(missing)
    return _fail(
        ctx=ctx,
        message=(
            f"copier-template-workflow-coverage: "
            f"{len(missing)} required workflow file(s) missing from "
            f"`.github/workflows/`: {missing_joined}. Corrective action: run "
            f"`copier update --vcs-ref=master` to re-sync the copier template (see "
            f'`non-functional-requirements.md` §"Shared content sync — copier template" for '
            f"the canonical required-file list)."
        ),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run copier-template-workflow-coverage against `ctx`.

    Wraps `_evaluate` in an `IOSuccess` so the return shape matches
    every other static check's `IOResult[Finding, LivespecError]`
    signature. The check is a pure filesystem inspection and never
    fails on the IO track — absent or unreadable workflow
    directories surface as `fail` findings, not `IOFailure`.
    """
    return IOSuccess(_evaluate(ctx=ctx))
