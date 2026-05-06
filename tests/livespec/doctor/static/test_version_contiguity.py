"""Tests for livespec.doctor.static.version_contiguity.

Per Plan Phase 3 +: this is the sixth of the eight Phase-3
minimum-subset doctor checks. It asserts that the
`<spec_root>/history/vNNN/` directory numbers are contiguous
starting from `v001` with no gaps (e.g., v001, v002, v003 is
valid; v001, v003 is a gap).

Cycle 139 lands the pass arm for a contiguous v001..vN
sequence. The fail arm (gap detected) lands in a subsequent
cycle.
"""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import version_contiguity
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def test_version_contiguity_run_returns_pass_for_contiguous_versions(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) for v001..v003 contiguous.

    Seeds a project root with a populated spec_root containing
    `history/v001/`, `history/v002/`, `history/v003/` (a
    contiguous sequence). Asserts the check yields a
    pass-status Finding.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history_path = spec_root / "history"
    history_path.mkdir()
    for tag in ("v001", "v002", "v003"):
        (history_path / tag).mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-version-contiguity",
        status="pass",
        message="history/vNNN/ numbers form a contiguous sequence starting at v001",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert version_contiguity.run(ctx=ctx) == IOSuccess(expected)
