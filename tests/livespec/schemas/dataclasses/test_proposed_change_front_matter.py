"""Tests for livespec.schemas.dataclasses.proposed_change_front_matter."""

from __future__ import annotations

import dataclasses

from livespec.schemas.dataclasses.proposed_change_front_matter import (
    ImplFollowup,
    ProposedChangeFrontMatter,
    SpecCommitments,
)
from livespec.types import Author, TopicSlug

__all__: list[str] = []


def test_proposed_change_front_matter_dataclasses_are_strict() -> None:
    """Every wire dataclass is frozen, keyword-only, and slotted."""
    for cls in (ImplFollowup, ProposedChangeFrontMatter, SpecCommitments):
        params = cls.__dataclass_params__  # pyright: ignore[reportAttributeAccessIssue]
        assert params.frozen, f"{cls.__name__} must be frozen"
        assert all(field.kw_only for field in dataclasses.fields(cls))
        assert hasattr(cls, "__slots__")


def test_decision_policy_defaults_to_none_and_preserves_wire_value() -> None:
    """Direct construction carries the optional decision-policy wire value."""
    base = {
        "topic": TopicSlug("demo"),
        "author": Author("agent"),
        "created_at": "2026-08-04T00:00:00Z",
    }
    assert ProposedChangeFrontMatter(**base).decision_policy is None
    assert (
        ProposedChangeFrontMatter(**base, decision_policy="delegated").decision_policy
        == "delegated"
    )
