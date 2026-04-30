"""Static-phase doctor check: proposed_change_topic_format.

Per Plan Phase 3 line 1596-1602 + PROPOSAL.md §"`doctor` →
Static-phase checks": this check asserts that every
`<spec_root>/proposed_changes/<topic>.md` filename follows the
canonical topic-slug format (lowercase letters, digits, and
hyphens only — pattern `^[a-z0-9-]+$`).

Cycle 141 lands the pass arm. Subsequent cycles add the
fail arm (invalid topic slug — uppercase, underscores, etc.).
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "doctor-proposed-change-topic-format"


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="every proposed_changes/<topic>.md filename uses the canonical slug format",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _evaluate(
    *,
    ctx: DoctorContext,
    proposed_files: list[Path],
) -> IOResult[Finding, LivespecError]:
    """Evaluate the proposed-change filenames against the slug regex.

    Cycle 141 lands the smallest viable behavior: any list
    yields a pass-Finding. The actual slug-pattern
    discriminator lands in the next cycle when its fail-arm
    test forces it into existence.
    """
    _ = proposed_files
    return IOSuccess(_pass_finding(ctx=ctx))


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the proposed-change-topic-format check against `ctx`.

    Lists `<ctx.spec_root>/proposed_changes/` and evaluates the
    filenames. On success yields IOSuccess(Finding(status=
    'pass')); the fail arm (invalid slug) lands in subsequent
    cycles.
    """
    proposed_path = ctx.spec_root / "proposed_changes"
    return fs.list_dir(path=proposed_path).bind(
        lambda proposed_files: _evaluate(ctx=ctx, proposed_files=proposed_files),
    )
