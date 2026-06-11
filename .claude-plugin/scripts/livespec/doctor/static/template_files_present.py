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
"""Static-phase doctor check: template_files_present.

Per `SPECIFICATION/spec.md` §"Template manifest" →
"Heading-coverage and doctor-static rewiring": the check is
manifest-aware. For the main spec tree under an active v2
template, the `spec_files` manifest is the source of truth — the
check verifies that EVERY manifest-declared path exists under the
spec root and fires `fail` naming the missing files otherwise.

v1 templates (no manifest), unresolvable templates, and sub-spec
trees keep the pre-manifest behavior: verify that
`<spec_root>/spec.md` (the file every livespec-template seed
materializes) is present on disk. Manifest resolution flows
through the shared `_template_manifest` loader, which degrades to
"no manifest" on every resolution failure.
"""

from __future__ import annotations

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.doctor.static._template_manifest import (
    is_main_spec_root,
    load_active_template_spec_files,
)
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.finding import Finding
from livespec.schemas.dataclasses.template_config import SpecFileDecl
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-template-files-present")


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="canonical template-materialized files are present",
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _fail_finding(*, ctx: DoctorContext, missing: list[str]) -> Finding:
    """Construct the fail-status Finding naming the missing manifest paths."""
    return Finding(
        check_id=SLUG,
        status="fail",
        message=(
            f"template-files-present: {len(missing)} manifest-declared "
            f"spec file(s) missing from {ctx.spec_root}: {', '.join(missing)}"
        ),
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _spec_md_presence(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """The pre-manifest (v1 / sub-spec) arm: `<spec_root>/spec.md` must read.

    Reads `<ctx.spec_root>/spec.md` to confirm presence; a missing
    file surfaces as the railway's `PreconditionError`, which the
    orchestrator folds into a fail-status "check process error"
    Finding.
    """
    spec_md_path = ctx.spec_root / "spec.md"
    return fs.read_text(path=spec_md_path).bind(
        lambda _text: IOSuccess(_pass_finding(ctx=ctx)),
    )


def _evaluate_manifest(
    *,
    ctx: DoctorContext,
    spec_files: dict[str, SpecFileDecl] | None,
) -> IOResult[Finding, LivespecError]:
    """Verify every manifest-declared path exists; fall back to v1 when None."""
    if spec_files is None:
        return _spec_md_presence(ctx=ctx)
    missing = sorted(
        rel_path for rel_path in spec_files if not (ctx.spec_root / rel_path).is_file()
    )
    if missing:
        return IOSuccess(_fail_finding(ctx=ctx, missing=missing))
    return IOSuccess(_pass_finding(ctx=ctx))


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the template-files-present check against `ctx`.

    Main-tree contexts consult the active template's `spec_files`
    manifest (v2 templates verify every declared path); sub-spec
    trees and no-manifest templates keep the spec.md-presence
    behavior.
    """
    if not is_main_spec_root(ctx=ctx):
        return _spec_md_presence(ctx=ctx)
    return load_active_template_spec_files(project_root=ctx.project_root).bind(
        lambda spec_files: _evaluate_manifest(ctx=ctx, spec_files=spec_files),
    )
