"""Tests for spec-governance proposed-change front-matter edits."""

from __future__ import annotations

from pathlib import Path

from livespec.spec_governance.proposal_edit import write_proposal_override

__all__: list[str] = []


def test_proposal_override_validation_paths(*, tmp_path: Path) -> None:
    proposal_dir = tmp_path / "SPECIFICATION" / "proposed_changes"
    proposal_dir.mkdir(parents=True)
    (proposal_dir / "bad.md").write_text("no front matter\n", encoding="utf-8")
    (proposal_dir / "unterminated.md").write_text("---\ntopic: x\n", encoding="utf-8")

    assert isinstance(
        write_proposal_override(project_root=tmp_path, proposal_stem="missing", value="auto-spawn"),
        str,
    )
    assert isinstance(
        write_proposal_override(project_root=tmp_path, proposal_stem="bad", value="auto-spawn"),
        str,
    )
    assert isinstance(
        write_proposal_override(
            project_root=tmp_path, proposal_stem="unterminated", value="auto-spawn"
        ),
        str,
    )


def test_existing_proposal_override_is_replaced(*, tmp_path: Path) -> None:
    proposal_dir = tmp_path / "SPECIFICATION" / "proposed_changes"
    proposal_dir.mkdir(parents=True)
    proposal = proposal_dir / "topic-b.md"
    proposal.write_text(
        "---\ntopic: topic-b\nratification_review_policy: manual-spawn\n---\nBody.\n",
        encoding="utf-8",
    )

    result = write_proposal_override(
        project_root=tmp_path,
        proposal_stem="topic-b",
        value="auto-spawn",
    )

    assert isinstance(result, Path)
    assert "ratification_review_policy: auto-spawn" in proposal.read_text(encoding="utf-8")
