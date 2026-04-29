"""Tests for livespec.schemas.dataclasses.proposal_findings."""

from __future__ import annotations

import dataclasses

import pytest
from livespec.schemas.dataclasses.proposal_findings import (
    ProposalFinding,
    ProposalFindings,
)

__all__: list[str] = []


def _make_finding(*, name: str = "topic-a") -> ProposalFinding:
    return ProposalFinding(
        name=name,
        target_spec_files=["SPECIFICATION/x.md"],
        summary="summary",
        motivation="motivation",
        proposed_changes="proposed",
    )


def test_proposal_finding_construct() -> None:
    finding = _make_finding()
    assert finding.name == "topic-a"
    assert finding.target_spec_files == ["SPECIFICATION/x.md"]
    assert finding.summary == "summary"
    assert finding.motivation == "motivation"
    assert finding.proposed_changes == "proposed"


def test_proposal_findings_empty() -> None:
    payload = ProposalFindings(findings=[])
    assert payload.findings == []


def test_proposal_findings_with_entries() -> None:
    a = _make_finding(name="topic-a")
    b = _make_finding(name="topic-b")
    payload = ProposalFindings(findings=[a, b])
    assert payload.findings == [a, b]


def test_proposal_finding_is_frozen() -> None:
    finding = _make_finding()
    with pytest.raises(dataclasses.FrozenInstanceError):
        finding.name = "renamed"  # type: ignore[misc]


def test_proposal_findings_is_frozen() -> None:
    payload = ProposalFindings(findings=[])
    with pytest.raises(dataclasses.FrozenInstanceError):
        payload.findings = [_make_finding()]  # type: ignore[misc]
