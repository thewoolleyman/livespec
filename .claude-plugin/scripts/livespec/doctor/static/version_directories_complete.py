"""version-directories-complete static check.

Verifies each `<spec_root>/history/v<NNN>/` carries a
`proposed_changes/` subdirectory. Phase 3 minimum-viable: just
verifies the proposed_changes/ subdir is present in each version
directory. Phase 7 widens to also verify the active template's
versioned spec files are present (per template_config's
versioned-surface declaration).
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


SLUG: CheckId = CheckId("doctor-version-directories-complete")
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
    incomplete: list[str] = []
    for entry in sorted(history_dir.iterdir()):
        if not _VNNN_RE.match(entry.name):
            continue
        if not (entry / "proposed_changes").is_dir():
            incomplete.append(f"history/{entry.name}/")
    if incomplete:
        return IOSuccess(
            Finding(
                check_id=SLUG,
                status="fail",
                message=(
                    f"incomplete version directories (missing proposed_changes/): "
                    f"{', '.join(incomplete)}"
                ),
                path=None,
                line=None,
                spec_root=spec_root_str,
            ),
        )
    return IOSuccess(
        Finding(
            check_id=SLUG,
            status="pass",
            message="all version directories carry proposed_changes/",
            path=None,
            line=None,
            spec_root=spec_root_str,
        ),
    )
