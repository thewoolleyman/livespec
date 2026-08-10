"""Tests for spec pull-request merge policy resolution."""

from __future__ import annotations

from pathlib import Path

from livespec.spec_governance.config import SpecGovernanceConfig
from livespec.spec_governance.spec_pr_merge import (
    awaits_manual_spec_pr_merge,
    effective_spec_pr_merge,
)

__all__: list[str] = []


def test_invalid_proposal_override_resolves_safely_to_manual(*, tmp_path: Path) -> None:
    _write_history_proposal(
        root=tmp_path,
        version="v001",
        stem="topic-a",
        front_matter="spec_pr_merge_policy: robot\n",
    )

    policy = effective_spec_pr_merge(
        project_root=tmp_path,
        config=SpecGovernanceConfig(spec_pr_merge="auto-on-green"),
        proposal_stems=("topic-a",),
    )

    assert policy.value == "manual"
    assert policy.source == "proposal"
    assert awaits_manual_spec_pr_merge(policy=policy)


def test_absent_proposal_override_inherits_valid_global_auto(*, tmp_path: Path) -> None:
    _write_history_proposal(
        root=tmp_path,
        version="v001",
        stem="topic-a",
        front_matter="",
    )

    policy = effective_spec_pr_merge(
        project_root=tmp_path,
        config=SpecGovernanceConfig(spec_pr_merge="auto-on-green"),
        proposal_stems=("topic-a",),
    )

    assert policy.value == "auto-on-green"
    assert policy.source == "global"
    assert not awaits_manual_spec_pr_merge(policy=policy)


def test_malformed_proposal_front_matter_resolves_safely_to_manual(
    *,
    tmp_path: Path,
) -> None:
    proposal_dir = tmp_path / "SPECIFICATION" / "history" / "v001" / "proposed_changes"
    proposal_dir.mkdir(parents=True)
    (proposal_dir / "topic-a.md").write_text("---\ntopic: topic-a\n", encoding="utf-8")

    policy = effective_spec_pr_merge(
        project_root=tmp_path,
        config=SpecGovernanceConfig(spec_pr_merge="auto-on-green"),
        proposal_stems=("topic-a",),
    )

    assert policy.value == "manual"
    assert policy.source == "proposal"


def _write_history_proposal(
    *,
    root: Path,
    version: str,
    stem: str,
    front_matter: str,
) -> None:
    proposal_dir = root / "SPECIFICATION" / "history" / version / "proposed_changes"
    proposal_dir.mkdir(parents=True)
    (proposal_dir / f"{stem}.md").write_text(
        f"---\ntopic: {stem}\n{front_matter}---\n\n## Proposal\n\nBody.\n",
        encoding="utf-8",
    )
