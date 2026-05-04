"""Tests for livespec.doctor.static.version_directories_complete.

Per Plan Phase 3 + PROPOSAL.md §"`doctor` →
Static-phase checks": this is the fifth of the eight Phase-3
minimum-subset doctor checks. It asserts that every
`<spec_root>/history/vNNN/` directory contains its expected
sub-structure (the main-file + the `proposed_changes/`
subdirectory).

Phase-3 minimum scope: pass arm. The check verifies that every
existing `history/v*/` directory has a `proposed_changes/`
subdirectory. The "main-file" presence (PROPOSAL.md or
template-specific equivalent) is template-aware and lands at
Phase 7. Cycle 138 lands the success arm; subsequent cycles
add the missing-subdirectory failure arm.
"""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import version_directories_complete
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def test_version_directories_complete_run_returns_pass_for_well_formed_history(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) when every vNNN/ has proposed_changes/.

    Seeds a project root with a populated spec_root containing
    `history/v001/proposed_changes/` and
    `history/v002/proposed_changes/` (two contiguous version
    directories, each fully formed). Asserts the check yields
    a pass-status Finding.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history_path = spec_root / "history"
    history_path.mkdir()
    (history_path / "v001" / "proposed_changes").mkdir(parents=True)
    (history_path / "v002" / "proposed_changes").mkdir(parents=True)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-version-directories-complete",
        status="pass",
        message="every history/vNNN/ contains its proposed_changes/ subdir",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert version_directories_complete.run(ctx=ctx) == IOSuccess(expected)


def test_version_directories_complete_run_skips_non_version_entries_in_history(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) ignores non-`v*` entries (files + dirs) under history/.

    Per the seed wrapper's per-tree skill-owned `history/README.md`
    directory-description (Plan Phase 6, 3174-3175,
    3194-3195), the seeded `<spec_root>/history/` directory contains
    a `README.md` file alongside the `vNNN/` version directories.
    The check must walk only `v*` directories when verifying the
    `proposed_changes/` subdir presence; non-`v*` siblings (file or
    dir) are skill-owned scaffolding outside the per-version-dir
    contract and must not be probed.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history_path = spec_root / "history"
    history_path.mkdir()
    (history_path / "v001" / "proposed_changes").mkdir(parents=True)
    (history_path / "README.md").write_text(
        "Skill-owned directory description.\n",
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-version-directories-complete",
        status="pass",
        message="every history/vNNN/ contains its proposed_changes/ subdir",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert version_directories_complete.run(ctx=ctx) == IOSuccess(expected)
