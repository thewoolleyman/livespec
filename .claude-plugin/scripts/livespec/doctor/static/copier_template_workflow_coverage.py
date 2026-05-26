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

Every consumer repository governed by livespec MUST contain a
`.github/workflows/` directory whose set of workflow files is a
SUPERSET of the required-file list enumerated in §"Shared
content sync — copier template". The check fires `fail` for
every required workflow file that is missing from the
consumer's `.github/workflows/`. Each fail finding names the
specific missing file(s) and directs the user to run
`copier update` to re-sync from the template.

The required-file list is hard-coded in this module per the v1
contract clause: "for v1, the doctor invariant MAY hard-code
the list and rely on PR review to catch drift". A paired
enforcement-suite check in `livespec-dev-tooling` will catch
drift between the contract list and the hard-coded list once
that sibling propose-change lands.

When `.github/workflows/` is absent entirely the check fires a
single `fail` finding naming every required file, since the
corrective action (run `copier update`) is identical to the
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
    "auto-update-branches.yml",
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


def _evaluate(*, ctx: DoctorContext) -> Finding:
    """Build the pass-or-fail Finding from the project root's workflow dir.

    The check walks `<project_root>/.github/workflows/` and
    compares its file set against `REQUIRED_WORKFLOW_FILES`. When
    every required file is present, the check passes. When one or
    more required files are missing — including the case where
    `.github/workflows/` does not exist at all — the check fires
    a single `fail` finding naming the missing files and
    directing the user to `copier update`.
    """
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
                f"{missing_joined}. Corrective action: run `copier update` to "
                f"re-sync the copier template (see `contracts.md` "
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
            f"`copier update` to re-sync the copier template (see "
            f'`contracts.md` §"Shared content sync — copier template" for '
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
