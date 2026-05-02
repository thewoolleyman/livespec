"""Tests for livespec.validate.revision_front_matter.

Per style doc §"Skill layout — `validate/`": validator at
`validate/revision_front_matter.py` exports
`validate_revision_front_matter(payload, schema)` returning
`Result[RevisionFrontMatter, ValidationError]`.

The wire payload is the YAML front-matter at the top of a
revision file at
`<spec-root>/history/vNNN/proposed_changes/<topic>-revision.md`
(per PROPOSAL §"Revision file format" lines 3027-3050):
required `proposal`, `decision` (enum), `revised_at`,
`author_human`, `author_llm`.
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
from returns.result import Failure, Success

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.revision_front_matter import RevisionFrontMatter
from livespec.types import Author
from livespec.validate import revision_front_matter

__all__: list[str] = []

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude-plugin"
    / "scripts"
    / "livespec"
    / "schemas"
    / "revision_front_matter.schema.json"
)


def test_validate_revision_front_matter_returns_success_for_valid_accept() -> None:
    """A well-formed accept-decision payload validates to Success."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "proposal": "switch-auth-middleware.md",
        "decision": "accept",
        "revised_at": "2026-05-02T09:30:00Z",
        "author_human": "thewoolleyman <chad@example.com>",
        "author_llm": "claude-opus-4-7",
    }
    result = revision_front_matter.validate_revision_front_matter(
        payload=payload,
        schema=schema,
    )
    expected = RevisionFrontMatter(
        proposal="switch-auth-middleware.md",
        decision="accept",
        revised_at="2026-05-02T09:30:00Z",
        author_human=Author("thewoolleyman <chad@example.com>"),
        author_llm=Author("claude-opus-4-7"),
    )
    assert result == Success(expected)


def test_validate_revision_front_matter_returns_failure_on_invalid_decision_enum() -> None:
    """A decision outside the enum returns Failure(ValidationError)."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "proposal": "demo.md",
        "decision": "maybe",
        "revised_at": "2026-05-02T09:30:00Z",
        "author_human": "h",
        "author_llm": "l",
    }
    result = revision_front_matter.validate_revision_front_matter(
        payload=payload,
        schema=schema,
    )
    match result:
        case Failure(ValidationError() as err):
            assert "revision_front_matter:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_revision_front_matter_carries_modify_decision() -> None:
    """A `modify` decision validates and the dataclass carries the value through."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "proposal": "demo.md",
        "decision": "modify",
        "revised_at": "2026-05-02T09:30:00Z",
        "author_human": "h",
        "author_llm": "l",
    }
    result = revision_front_matter.validate_revision_front_matter(
        payload=payload,
        schema=schema,
    )
    match result:
        case Success(value):
            assert value.decision == "modify"
        case _:
            msg = f"expected Success(RevisionFrontMatter), got {result}"
            raise AssertionError(msg)


@given(author_llm=st.text(min_size=1, max_size=80))
def test_validate_revision_front_matter_round_trips_author_llm(*, author_llm: str) -> None:
    """For arbitrary author_llm text, the success path preserves it verbatim."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "proposal": "demo.md",
        "decision": "reject",
        "revised_at": "2026-05-02T09:30:00Z",
        "author_human": "h",
        "author_llm": author_llm,
    }
    result = revision_front_matter.validate_revision_front_matter(
        payload=payload,
        schema=schema,
    )
    match result:
        case Success(value):
            assert value.author_llm == author_llm
        case _:
            msg = f"expected Success(RevisionFrontMatter), got {result}"
            raise AssertionError(msg)
