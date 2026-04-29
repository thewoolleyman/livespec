"""Tests for livespec.validate.proposed_change_front_matter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import livespec.schemas
from hypothesis import HealthCheck, given, settings
from hypothesis_jsonschema import from_schema
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.proposed_change_front_matter import (
    ProposedChangeFrontMatter,
)
from livespec.validate.proposed_change_front_matter import make_validator
from returns.result import Failure, Success

if TYPE_CHECKING:
    from livespec.io.fastjsonschema_facade import Validator

__all__: list[str] = []


_SCHEMA_PATH = Path(livespec.schemas.__file__).parent / "proposed_change_front_matter.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


_VALID_PAYLOAD: dict[str, Any] = {
    "topic": "rewrite-auth",
    "author": "claude-4-7",
    "created_at": "2026-04-26T09:30:00Z",
}


def test_well_formed_payload_returns_success(
    *,
    proposed_change_front_matter_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=proposed_change_front_matter_validator)
    result = validator(payload=dict(_VALID_PAYLOAD))
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert isinstance(parsed, ProposedChangeFrontMatter)
    assert parsed.topic == "rewrite-auth"
    assert parsed.author == "claude-4-7"
    assert parsed.created_at == "2026-04-26T09:30:00Z"


def test_topic_with_invalid_uppercase_returns_failure(
    *,
    proposed_change_front_matter_validator: Validator,
) -> None:
    """Pattern enforces lowercase kebab-case."""
    validator = make_validator(fast_validator=proposed_change_front_matter_validator)
    payload: dict[str, Any] = {**_VALID_PAYLOAD, "topic": "Rewrite-Auth"}
    result = validator(payload=payload)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), ValidationError)


def test_missing_required_field_returns_failure(
    *,
    proposed_change_front_matter_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=proposed_change_front_matter_validator)
    result = validator(payload={"topic": "x", "author": "y"})
    assert isinstance(result, Failure)


@given(payload=from_schema(_SCHEMA))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=25)
def test_pbt_schema_conforming_payloads_always_succeed(
    *,
    payload: dict[str, Any],
    proposed_change_front_matter_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=proposed_change_front_matter_validator)
    result = validator(payload=payload)
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert isinstance(parsed, ProposedChangeFrontMatter)
    assert parsed.topic == payload["topic"]
