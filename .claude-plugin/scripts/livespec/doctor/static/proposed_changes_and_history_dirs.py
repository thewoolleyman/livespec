"""Static-phase doctor check: proposed_changes_and_history_dirs.

Per Plan Phase 3 + PROPOSAL.md §"`doctor` →
Static-phase checks": this check asserts that
`<spec_root>/proposed_changes/` and `<spec_root>/history/`
directories both exist (the canonical seeded-revise tree shape
per PROPOSAL §"`seed`" steps 4-5).

Cycle 137 lands the pass arm. Subsequent cycles add the
fail arms (one or both directories missing) under outside-in
consumer pressure.
"""

from __future__ import annotations

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "doctor-proposed-changes-and-history-dirs"


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="proposed_changes/ and history/ directories are present",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the proposed-changes-and-history-dirs check against `ctx`.

    Lists `<ctx.spec_root>/proposed_changes/` and
    `<ctx.spec_root>/history/` to confirm both are present.
    On success yields IOSuccess(Finding(status='pass')). The
    missing-directory failure arm lands in subsequent cycles.
    """
    proposed_changes_path = ctx.spec_root / "proposed_changes"
    history_path = ctx.spec_root / "history"
    return (
        fs.list_dir(path=proposed_changes_path)
        .bind(lambda _: fs.list_dir(path=history_path))
        .bind(lambda _: IOSuccess(_pass_finding(ctx=ctx)))
    )
