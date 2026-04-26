"""version-contiguity static check.

Verifies `<spec_root>/history/v<N>/` directory names form a
contiguous sequence starting at v001 with no gaps. Detects manual
deletion of intermediate versions.
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


SLUG: CheckId = CheckId("doctor-version-contiguity")
_VNNN_RE = re.compile(r"^v(\d+)$")


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
    versions: list[int] = []
    for entry in history_dir.iterdir():
        m = _VNNN_RE.match(entry.name)
        if m and entry.is_dir():
            versions.append(int(m.group(1)))
    versions.sort()
    if not versions:
        return IOSuccess(
            Finding(
                check_id=SLUG,
                status="skipped",
                message="skipped: no version directories under history/",
                path=None,
                line=None,
                spec_root=spec_root_str,
            ),
        )
    gaps = _find_gaps(versions=versions)
    if gaps:
        gap_list = ",".join(f"v{n:03d}" for n in gaps)
        return IOSuccess(
            Finding(
                check_id=SLUG,
                status="fail",
                message=f"version sequence gaps detected: missing {gap_list}",
                path=None,
                line=None,
                spec_root=spec_root_str,
            ),
        )
    return IOSuccess(
        Finding(
            check_id=SLUG,
            status="pass",
            message=f"version sequence contiguous from v001 to v{versions[-1]:03d}",
            path=None,
            line=None,
            spec_root=spec_root_str,
        ),
    )


def _find_gaps(*, versions: list[int]) -> list[int]:
    """Return missing integers in the range [1, max(versions)] not present in `versions`."""
    seen = set(versions)
    return [n for n in range(1, max(versions) + 1) if n not in seen]
