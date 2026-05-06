"""Tests for livespec.doctor.static.proposed_change_topic_format.

Per Plan Phase 3 +: this is the eighth and final Phase-3
minimum-subset doctor check. It asserts that every
`<spec_root>/proposed_changes/<topic>.md` filename follows the
canonical topic-slug format (lowercase letters, digits, and
hyphens only).

Cycle 141 lands the pass arm for a well-named proposed-change
topic. The fail arm (uppercase or invalid characters in topic
slug) lands in a subsequent cycle.
"""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import proposed_change_topic_format
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def test_proposed_change_topic_format_run_returns_pass_for_valid_slug(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) for a valid topic slug.

    Seeds a project root with a populated spec_root containing
    `proposed_changes/add-feature.md` — a canonical topic slug
    matching `^[a-z0-9-]+$`. Asserts the check yields a
    pass-status Finding.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    proposed_dir = spec_root / "proposed_changes"
    proposed_dir.mkdir()
    _ = (proposed_dir / "add-feature.md").write_text("# proposal\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-proposed-change-topic-format",
        status="pass",
        message="every proposed_changes/<topic>.md filename uses the canonical slug format",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert proposed_change_topic_format.run(ctx=ctx) == IOSuccess(expected)
