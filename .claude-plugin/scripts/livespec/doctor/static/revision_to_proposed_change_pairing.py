"""revision-to-proposed-change-pairing static check.

For each `<stem>-revision.md` under `<spec_root>/history/v<N>/
proposed_changes/`, verifies that the paired `<stem>.md` exists
in the same directory. Per PROPOSAL §"revise" lines 2445-2449:
the check walks filename stems (NOT front-matter `topic` values),
because v014 N6 collision-disambiguation puts a `-N` suffix on
the filename stem but keeps the front-matter `topic` canonical.
"""

from __future__ import annotations

import re

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId

__all__: list[str] = [
    "SLUG",
    "run",
]


SLUG: CheckId = CheckId("doctor-revision-to-proposed-change-pairing")
_VNNN_RE = re.compile(r"^v\d+$")


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    spec_root_str = str(ctx.spec_root)
    history_dir = ctx.spec_root / "history"
    if not history_dir.is_dir():
        return IOSuccess(
            Finding(
                check_id=SLUG,
                status="skipped",
                message="skipped: history/ does not exist (pre-seed state)",
                path=None,
                line=None,
                spec_root=spec_root_str,
            ),
        )
    orphans: list[str] = []
    for vdir in sorted(history_dir.iterdir()):
        if not (_VNNN_RE.match(vdir.name) and vdir.is_dir()):
            continue
        pc_dir = vdir / "proposed_changes"
        if not pc_dir.is_dir():
            continue
        for entry in sorted(pc_dir.iterdir()):
            if not entry.name.endswith("-revision.md"):
                continue
            stem = entry.name[: -len("-revision.md")]
            paired = pc_dir / f"{stem}.md"
            if not paired.is_file():
                orphans.append(f"history/{vdir.name}/proposed_changes/{entry.name}")
    if orphans:
        return IOSuccess(
            Finding(
                check_id=SLUG,
                status="fail",
                message=f"orphan revision files (missing paired <stem>.md): {', '.join(orphans)}",
                path=None,
                line=None,
                spec_root=spec_root_str,
            ),
        )
    return IOSuccess(
        Finding(
            check_id=SLUG,
            status="pass",
            message="every <stem>-revision.md pairs with <stem>.md in the same directory",
            path=None,
            line=None,
            spec_root=spec_root_str,
        ),
    )
