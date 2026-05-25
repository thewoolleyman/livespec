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
"""Static-phase doctor check: version_contiguity.

Per Plan  +: this check asserts that the
`<spec_root>/history/vNNN/` directory numbers form a
contiguous sequence starting from `v001` with no gaps.

This work lands the pass arm for a well-formed contiguous
sequence. The fail arm (gap detected) lands in a subsequent
cycle.
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-version-contiguity")


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="history/vNNN/ numbers form a contiguous sequence starting at v001",
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _evaluate(
    *,
    ctx: DoctorContext,
    version_paths: list[Path],
) -> IOResult[Finding, LivespecError]:
    """Evaluate the directory list for contiguity.

    This work lands the smallest viable behavior: as long as
    fs.list_dir returned a list (success), produce the
    pass-Finding. The actual contiguity discriminator (gap
    detection) lands in the next cycle when its test forces
    it into existence.
    """
    _ = version_paths
    return IOSuccess(_pass_finding(ctx=ctx))


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the version-contiguity check against `ctx`.

    Lists `<ctx.spec_root>/history/` and evaluates the result.
    On success yields IOSuccess(Finding(status='pass')); the
    gap-detection failure arm lands in subsequent cycles.
    """
    history_path = ctx.spec_root / "history"
    return fs.list_dir(path=history_path).bind(
        lambda version_paths: _evaluate(ctx=ctx, version_paths=version_paths),
    )
