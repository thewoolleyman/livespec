"""Tests for livespec.doctor.static.revision_to_proposed_change_pairing.

Per Plan Phase 3 line 1596-1602 + PROPOSAL.md §"`doctor` →
Static-phase checks": this is the seventh of the eight Phase-3
minimum-subset doctor checks. It asserts that every
`history/vNNN/proposed_changes/<topic>.md` has a paired
`<topic>-revision.md` in the same directory (the canonical
revise output shape per PROPOSAL §"`revise`" lines 2422-2429).

Cycle 140 lands the pass arm for a well-paired layout.
The fail arm (orphan proposed-change with no revision) lands
in a subsequent cycle.
"""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import revision_to_proposed_change_pairing
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def test_revision_to_proposed_change_pairing_run_returns_pass_for_paired_topic(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) for a paired topic.md + topic-revision.md.

    Seeds a project root with a populated spec_root containing
    `history/v001/proposed_changes/seed.md` and
    `history/v001/proposed_changes/seed-revision.md` — the
    canonical seed-flow output per PROPOSAL §"`seed`" lines
    2043-2064. Asserts the check yields a pass-status Finding.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    proposed_dir = spec_root / "history" / "v001" / "proposed_changes"
    proposed_dir.mkdir(parents=True)
    _ = (proposed_dir / "seed.md").write_text("# seed\n", encoding="utf-8")
    _ = (proposed_dir / "seed-revision.md").write_text("# revision\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-revision-to-proposed-change-pairing",
        status="pass",
        message="every history/vNNN/proposed_changes/<topic>.md has a paired -revision.md",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert revision_to_proposed_change_pairing.run(ctx=ctx) == IOSuccess(expected)
