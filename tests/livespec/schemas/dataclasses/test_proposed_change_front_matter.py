"""Tests for livespec.schemas.dataclasses.proposed_change_front_matter."""

from __future__ import annotations

from livespec.schemas.dataclasses.proposed_change_front_matter import (
    ProposedChangeFrontMatter,
)
from livespec.types import Author, TopicSlug

__all__: list[str] = []


def test_construct_required_fields() -> None:
    fm = ProposedChangeFrontMatter(
        topic=TopicSlug("my-topic"),
        author=Author("you@example.com"),
        created_at="2026-04-27T08:00:00Z",
    )
    assert fm.topic == "my-topic"
    assert fm.author == "you@example.com"
    assert fm.created_at == "2026-04-27T08:00:00Z"
