"""Static-phase doctor check: template_files_present.

Per Plan Phase 3 +: this check asserts that the canonical
template-materialized files are present in the spec_root.

Phase-3 minimum scope: verifies that `<spec_root>/spec.md` (the
file every livespec-template seed materializes per step 2) is present on disk. Phase 7 widens
this to walk the template's full declared file manifest
(template.json + recursively-discovered template-source files).

Cycle 136 lands the success arm. Subsequent cycles add the
missing-file failure arm.
"""

from __future__ import annotations

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "doctor-template-files-present"


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="canonical template-materialized files are present",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
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
