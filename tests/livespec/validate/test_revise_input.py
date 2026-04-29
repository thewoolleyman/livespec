"""Tests for livespec.validate.revise_input."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import livespec.schemas
from hypothesis import HealthCheck, given, settings
from hypothesis_jsonschema import from_schema
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.revise_input import ReviseInput
from livespec.validate.revise_input import make_validator
from returns.result import Failure, Success

if TYPE_CHECKING:
    from livespec.io.fastjsonschema_facade import Validator

__all__: list[str] = []


_SCHEMA_PATH = Path(livespec.schemas.__file__).parent / "revise_input.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_minimal_decision_payload(*, revise_input_validator: Validator) -> None:
    validator = make_validator(fast_validator=revise_input_validator)
    payload: dict[str, Any] = {
        "decisions": [
            {
                "proposal_topic": "topic-a",
                "decision": "reject",
                "rationale": "not now",
            },
        ],
    }
    result = validator(payload=payload)
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert isinstance(parsed, ReviseInput)
    assert parsed.author is None
    assert len(parsed.decisions) == 1
    assert parsed.decisions[0].decision == "reject"
    assert parsed.decisions[0].resulting_files == []
    assert parsed.decisions[0].modifications is None


def test_modify_decision_with_resulting_files(
    *,
    revise_input_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=revise_input_validator)
    payload: dict[str, Any] = {
        "author": "claude-4-7",
        "decisions": [
            {
                "proposal_topic": "topic-b",
                "decision": "modify",
                "rationale": "tweaked",
                "modifications": "renamed X to Y",
                "resulting_files": [
                    {"path": "SPECIFICATION/x.md", "content": "..."},
                ],
            },
        ],
    }
    result = validator(payload=payload)
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert parsed.author == "claude-4-7"
    assert parsed.decisions[0].modifications == "renamed X to Y"
    assert len(parsed.decisions[0].resulting_files) == 1
    assert parsed.decisions[0].resulting_files[0].path == "SPECIFICATION/x.md"


def test_unknown_decision_value_returns_failure(
    *,
    revise_input_validator: Validator,
) -> None:
    """Schema's enum constrains decision to accept/modify/reject."""
    validator = make_validator(fast_validator=revise_input_validator)
    payload: dict[str, Any] = {
        "decisions": [
            {
                "proposal_topic": "x",
                "decision": "approve",  # not in enum
                "rationale": "...",
            },
        ],
    }
    result = validator(payload=payload)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), ValidationError)


@given(payload=from_schema(_SCHEMA))
@settings(
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.too_slow,
    ],
    max_examples=15,
)
def test_pbt_schema_conforming_payloads_always_succeed(
    *,
    payload: dict[str, Any],
    revise_input_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=revise_input_validator)
    result = validator(payload=payload)
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert isinstance(parsed, ReviseInput)
    assert len(parsed.decisions) == len(payload["decisions"])
