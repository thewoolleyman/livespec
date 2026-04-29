"""Tests for livespec.validate.revision_front_matter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import livespec.schemas
from hypothesis import HealthCheck, given, settings
from hypothesis_jsonschema import from_schema
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.revision_front_matter import (
    RevisionFrontMatter,
)
from livespec.validate.revision_front_matter import make_validator
from returns.result import Failure, Success

if TYPE_CHECKING:
    from livespec.io.fastjsonschema_facade import Validator

__all__: list[str] = []


_SCHEMA_PATH = Path(livespec.schemas.__file__).parent / "revision_front_matter.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


_VALID_PAYLOAD: dict[str, Any] = {
    "proposal": "rewrite-auth.md",
    "decision": "accept",
    "revised_at": "2026-04-26T10:00:00Z",
    "author_human": "thewoolleyman",
    "author_llm": "claude-4-7",
}


def test_well_formed_payload_returns_success(
    *,
    revision_front_matter_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=revision_front_matter_validator)
    result = validator(payload=dict(_VALID_PAYLOAD))
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert isinstance(parsed, RevisionFrontMatter)
    assert parsed.proposal == "rewrite-auth.md"
    assert parsed.decision == "accept"
    assert parsed.author_human == "thewoolleyman"
    assert parsed.author_llm == "claude-4-7"


def test_proposal_filename_pattern_rejects_wrong_extension(
    *,
    revision_front_matter_validator: Validator,
) -> None:
    """Pattern requires the .md extension."""
    validator = make_validator(fast_validator=revision_front_matter_validator)
    payload: dict[str, Any] = {**_VALID_PAYLOAD, "proposal": "rewrite-auth.txt"}
    result = validator(payload=payload)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), ValidationError)


def test_decision_enum_rejects_unknown_value(
    *,
    revision_front_matter_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=revision_front_matter_validator)
    payload: dict[str, Any] = {**_VALID_PAYLOAD, "decision": "approve"}
    result = validator(payload=payload)
    assert isinstance(result, Failure)


@given(payload=from_schema(_SCHEMA))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
def test_pbt_schema_conforming_payloads_always_succeed(
    *,
    payload: dict[str, Any],
    revision_front_matter_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=revision_front_matter_validator)
    result = validator(payload=payload)
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert isinstance(parsed, RevisionFrontMatter)
    assert parsed.proposal == payload["proposal"]
    assert parsed.decision == payload["decision"]
