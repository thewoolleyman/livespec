"""Tests for livespec.doctor.static.proposed_changes_and_history_dirs.

Per Plan Phase 3 +: this is the fourth of the eight Phase-3
minimum-subset doctor checks. It asserts that
`<spec_root>/proposed_changes/` and `<spec_root>/history/`
directories both exist (the canonical seeded-revise tree
shape steps 4-5).

Phase-3 minimum scope: pass arm. Cycle 137 lands the success
case; the missing-directory failure arms land in subsequent
cycles when their tests force the discrimination.
"""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import proposed_changes_and_history_dirs
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def test_proposed_changes_and_history_dirs_run_returns_pass_when_both_present(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) when both dirs exist.

    Seeds a project root with a populated spec_root containing
    both `proposed_changes/` and `history/` directories.
    Asserts the check yields a pass-status Finding.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    (spec_root / "proposed_changes").mkdir()
    (spec_root / "history").mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-proposed-changes-and-history-dirs",
        status="pass",
        message="proposed_changes/ and history/ directories are present",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert proposed_changes_and_history_dirs.run(ctx=ctx) == IOSuccess(expected)
