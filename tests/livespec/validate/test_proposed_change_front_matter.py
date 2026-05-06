"""Tests for livespec.validate.proposed_change_front_matter.

Per style doc §"Skill layout — `validate/`": validator at
`validate/proposed_change_front_matter.py` exports
`validate_proposed_change_front_matter(payload, schema)`
returning `Result[ProposedChangeFrontMatter, ValidationError]`.

The wire payload is the YAML front-matter at the top of a
proposed-change file at `<spec-root>/proposed_changes/<topic>.md`
(per PROPOSAL §"Proposed-change file format"):
required `topic` (kebab-case slug), `author` identifier, and
`created_at` UTC ISO-8601 datetime.
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.proposed_change_front_matter import (
    ProposedChangeFrontMatter,
)
from livespec.types import Author, TopicSlug
from livespec.validate import proposed_change_front_matter
from returns.result import Failure, Success

__all__: list[str] = []

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude-plugin"
    / "scripts"
    / "livespec"
    / "schemas"
    / "proposed_change_front_matter.schema.json"
)

# Module-level schema cache (v040 D1): hypothesis-based @given
# tests run the body ~100 times per invocation; reloading the schema
# from disk on each example pushes individual examples over the
# default 200ms hypothesis deadline under `pytest -n auto` xdist
# worker contention. Loading once at module-import time eliminates
# per-example file I/O and the associated timing nondeterminism.
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_validate_proposed_change_front_matter_returns_success_for_valid_payload() -> None:
    """A well-formed front-matter payload validates to Success(ProposedChangeFrontMatter)."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "topic": "switch-auth-middleware",
        "author": "claude-opus-4-7",
        "created_at": "2026-05-02T09:30:00Z",
    }
    result = proposed_change_front_matter.validate_proposed_change_front_matter(
        payload=payload,
        schema=schema,
    )
    expected = ProposedChangeFrontMatter(
        topic=TopicSlug("switch-auth-middleware"),
        author=Author("claude-opus-4-7"),
        created_at="2026-05-02T09:30:00Z",
    )
    assert result == Success(expected)


def test_validate_proposed_change_front_matter_returns_failure_on_invalid_topic_slug() -> None:
    """A topic that doesn't match the kebab-case pattern returns Failure."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "topic": "Invalid Topic With Spaces",
        "author": "claude-opus-4-7",
        "created_at": "2026-05-02T09:30:00Z",
    }
    result = proposed_change_front_matter.validate_proposed_change_front_matter(
        payload=payload,
        schema=schema,
    )
    match result:
        case Failure(ValidationError() as err):
            assert "proposed_change_front_matter:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_proposed_change_front_matter_returns_failure_on_missing_required_field() -> None:
    """A payload missing `created_at` returns Failure(ValidationError)."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "topic": "demo",
        "author": "claude-opus-4-7",
    }
    result = proposed_change_front_matter.validate_proposed_change_front_matter(
        payload=payload,
        schema=schema,
    )
    match result:
        case Failure(ValidationError()):
            pass
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


@settings(deadline=None)
@given(
    author=st.text(min_size=1, max_size=80),
)
def test_validate_proposed_change_front_matter_round_trips_author_text(
    *,
    author: str,
) -> None:
    """For arbitrary author text, the success path preserves it verbatim."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "topic": "demo",
        "author": author,
        "created_at": "2026-05-02T09:30:00Z",
    }
    result = proposed_change_front_matter.validate_proposed_change_front_matter(
        payload=payload,
        schema=schema,
    )
    match result:
        case Success(value):
            assert value.author == author
        case _:
            msg = f"expected Success(ProposedChangeFrontMatter), got {result}"
            raise AssertionError(msg)
