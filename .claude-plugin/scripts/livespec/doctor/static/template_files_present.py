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

Per Plan  +: this check asserts that the canonical
template-materialized files are present in the spec_root.

Phase-3 minimum scope: verifies that `<spec_root>/spec.md` (the
file every livespec-template seed materializes per step 2) is present on disk.  widens
this to walk the template's full declared file manifest
(template.json + recursively-discovered template-source files).

This work lands the success arm. Subsequent cycles add the
missing-file failure arm.
"""

from __future__ import annotations

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.finding import Finding
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


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the template-files-present check against `ctx`.

    Reads `<ctx.spec_root>/spec.md` to confirm presence. On
    success yields IOSuccess(Finding(status='pass')). The
    missing-file failure arm lands in the next cycle.
    """
    spec_md_path = ctx.spec_root / "spec.md"
    return fs.read_text(path=spec_md_path).bind(
        lambda _text: IOSuccess(_pass_finding(ctx=ctx)),
    )
