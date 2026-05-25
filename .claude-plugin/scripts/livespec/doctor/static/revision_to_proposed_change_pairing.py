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
"""Static-phase doctor check: revision_to_proposed_change_pairing.

Per Plan  +: this check asserts that every
`history/vNNN/proposed_changes/<topic>.md` has a paired
`<topic>-revision.md` in the same directory.

This work lands the pass arm. Subsequent cycles add the
fail arm (orphan proposed-change with no revision).
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


SLUG: CheckId = CheckId("doctor-revision-to-proposed-change-pairing")


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="every history/vNNN/proposed_changes/<topic>.md has a paired -revision.md",
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _evaluate(
    *,
    ctx: DoctorContext,
    version_paths: list[Path],
) -> IOResult[Finding, LivespecError]:
    """Evaluate the version directories for revision-pairing.

    This work lands the smallest viable behavior: any list
    yields a pass-Finding. The actual orphan-discovery
    discriminator lands in the next cycle when its fail-arm
    test forces it into existence.
    """
    _ = version_paths
    return IOSuccess(_pass_finding(ctx=ctx))


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the revision-to-proposed-change-pairing check against `ctx`.

    Lists `<ctx.spec_root>/history/` and evaluates the result.
    On success yields IOSuccess(Finding(status='pass'));
    orphan-detection failure arm lands in subsequent cycles.
    """
    history_path = ctx.spec_root / "history"
    return fs.list_dir(path=history_path).bind(
        lambda version_paths: _evaluate(ctx=ctx, version_paths=version_paths),
    )
