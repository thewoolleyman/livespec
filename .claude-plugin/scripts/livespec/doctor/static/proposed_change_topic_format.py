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
"""Static-phase doctor check: proposed_change_topic_format.

Per Plan  +: this check asserts that every
`<spec_root>/proposed_changes/<topic>.md` filename follows the
canonical topic-slug format (lowercase letters, digits, and
hyphens only — pattern `^[a-z0-9-]+$`).

This work lands the pass arm. Subsequent cycles add the
fail arm (invalid topic slug — uppercase, underscores, etc.).
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


SLUG: CheckId = CheckId("doctor-proposed-change-topic-format")


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="every proposed_changes/<topic>.md filename uses the canonical slug format",
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _evaluate(
    *,
    ctx: DoctorContext,
    proposed_files: list[Path],
) -> IOResult[Finding, LivespecError]:
    """Evaluate the proposed-change filenames against the slug regex.

    This work lands the smallest viable behavior: any list
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
