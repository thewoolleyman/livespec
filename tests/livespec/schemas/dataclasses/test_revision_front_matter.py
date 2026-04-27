"""Tests for livespec.schemas.dataclasses.revision_front_matter."""

from __future__ import annotations

from livespec.schemas.dataclasses.revision_front_matter import RevisionFrontMatter
from livespec.types import Author

__all__: list[str] = []


def test_construct_revision_front_matter_accept() -> None:
    fm = RevisionFrontMatter(
        proposal="my-topic",
        decision="accept",
        revised_at="2026-04-27T09:00:00Z",
        author_human=Author("you@example.com"),
        author_llm=Author("claude@anthropic.com"),
    )
    assert fm.decision == "accept"
    assert fm.author_human == "you@example.com"
    assert fm.author_llm == "claude@anthropic.com"


def test_construct_revision_front_matter_modify() -> None:
    fm = RevisionFrontMatter(
        proposal="adjust-x",
        decision="modify",
        revised_at="2026-04-27T09:00:00Z",
        author_human=Author("a"),
        author_llm=Author("b"),
    )
    assert fm.decision == "modify"


def test_construct_revision_front_matter_reject() -> None:
    fm = RevisionFrontMatter(
        proposal="bad-idea",
        decision="reject",
        revised_at="2026-04-27T09:00:00Z",
        author_human=Author("a"),
        author_llm=Author("b"),
    )
    assert fm.decision == "reject"
