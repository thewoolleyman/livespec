"""proposed-changes-and-history-dirs static check.

Verifies `<spec_root>/proposed_changes/` and `<spec_root>/history/`
exist as directories. These are the structural anchors for the
governed-loop; their absence indicates either a pre-seed state
or a manually-broken tree.
"""

from __future__ import annotations

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId

__all__: list[str] = [
    "SLUG",
    "run",
]


SLUG: CheckId = CheckId("doctor-proposed-changes-and-history-dirs")


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    spec_root_str = str(ctx.spec_root)
    pc_dir = ctx.spec_root / "proposed_changes"
    history_dir = ctx.spec_root / "history"
    missing: list[str] = []
    if not pc_dir.is_dir():
        missing.append("proposed_changes/")
    if not history_dir.is_dir():
        missing.append("history/")
    if missing:
        return IOSuccess(
            Finding(
                check_id=SLUG,
                status="fail",
                message=f"missing required spec-root subdirs: {', '.join(missing)}",
                path=None,
                line=None,
                spec_root=spec_root_str,
            ),
        )
    return IOSuccess(
        Finding(
            check_id=SLUG,
            status="pass",
            message="proposed_changes/ and history/ both present",
            path=None,
            line=None,
            spec_root=spec_root_str,
        ),
    )
