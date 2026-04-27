"""Tests for livespec.schemas.dataclasses.revise_input."""

from __future__ import annotations

from livespec.schemas.dataclasses.revise_input import (
    ProposalDecision,
    ResultingFile,
    ReviseInput,
)
from livespec.types import Author, TopicSlug

__all__: list[str] = []


def test_resulting_file_construct() -> None:
    rf = ResultingFile(path="SPECIFICATION/x.md", content="...")
    assert rf.path == "SPECIFICATION/x.md"
    assert rf.content == "..."


def test_proposal_decision_default_resulting_files() -> None:
    """`_empty_resulting_files()` factory covers line 36 (the `return []` body)."""
    decision = ProposalDecision(
        proposal_topic=TopicSlug("topic-a"),
        decision="reject",
        rationale="not now",
    )
    assert decision.resulting_files == []
    assert decision.modifications is None


def test_proposal_decision_factory_returns_fresh_lists() -> None:
    a = ProposalDecision(proposal_topic=TopicSlug("a"), decision="accept", rationale="ok")
    b = ProposalDecision(proposal_topic=TopicSlug("b"), decision="accept", rationale="ok")
    assert a.resulting_files is not b.resulting_files


def test_proposal_decision_with_modifications() -> None:
    decision = ProposalDecision(
        proposal_topic=TopicSlug("topic-b"),
        decision="modify",
        rationale="tweaked",
        modifications="renamed X to Y",
        resulting_files=[ResultingFile(path="x.md", content="content")],
    )
    assert decision.modifications == "renamed X to Y"
    assert len(decision.resulting_files) == 1


def test_revise_input_default_author() -> None:
    payload = ReviseInput(decisions=[])
    assert payload.author is None


def test_revise_input_with_author() -> None:
    payload = ReviseInput(decisions=[], author=Author("you"))
    assert payload.author == "you"
