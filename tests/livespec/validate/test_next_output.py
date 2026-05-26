"""Tests for livespec.validate.next_output.

Per style doc §"Skill layout — `validate/`": the validator
at `validate/next_output.py` exports `validate_next_output(
payload, schema)` returning `Result[NextOutput, ValidationError]`.
All three schema fields are required and the schema enforces
strict enum membership on `action` and `urgency`.
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.next_output import NextOutput
from livespec.validate import next_output
from returns.result import Failure, Success

__all__: list[str] = []


_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude-plugin"
    / "scripts"
    / "livespec"
    / "schemas"
    / "next_output.schema.json"
)
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_validate_next_output_returns_success_for_well_formed_payload() -> None:
    """A conformant payload returns Success(NextOutput) with the three fields populated."""
    payload: dict[str, object] = {
        "action": "revise",
        "reason": "1 proposed change pending",
        "urgency": "medium",
    }
    result = next_output.validate_next_output(payload=payload, schema=_SCHEMA)
    assert result == Success(
        NextOutput(action="revise", reason="1 proposed change pending", urgency="medium"),
    )


def test_validate_next_output_returns_failure_on_invalid_action_enum() -> None:
    """A payload with an out-of-enum `action` returns Failure(ValidationError)."""
    payload: dict[str, object] = {
        "action": "do-something-novel",
        "reason": "synthetic",
        "urgency": "low",
    }
    result = next_output.validate_next_output(payload=payload, schema=_SCHEMA)
    match result:
        case Failure(ValidationError() as err):
            assert "next_output:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_next_output_returns_failure_on_missing_required_field() -> None:
    """A payload missing `urgency` returns Failure(ValidationError).

    Drives the `required` array on next_output.schema.json:
    fastjsonschema rejects payloads that omit any of `action`,
    `reason`, or `urgency`.
    """
    payload: dict[str, object] = {"action": "none", "reason": "nothing pressing"}
    result = next_output.validate_next_output(payload=payload, schema=_SCHEMA)
    match result:
        case Failure(ValidationError() as err):
            assert "next_output:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_next_output_returns_failure_on_unknown_field() -> None:
    """A payload with an extra field returns Failure(ValidationError).

    Drives `additionalProperties: false`: fastjsonschema
    rejects any field not enumerated in the schema's
    `properties` keyset.
    """
    payload: dict[str, object] = {
        "action": "none",
        "reason": "synthetic",
        "urgency": "low",
        "extra": "field",
    }
    result = next_output.validate_next_output(payload=payload, schema=_SCHEMA)
    match result:
        case Failure(ValidationError() as err):
            assert "next_output:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


@settings(deadline=None)
@given(
    action=st.sampled_from(
        ["revise", "propose-change", "critique", "prune-history", "capture-work-item", "none"],
    ),
    urgency=st.sampled_from(["high", "medium", "low"]),
    reason=st.text(min_size=1, max_size=80),
)
def test_validate_next_output_round_trips_every_enum_combination(
    *,
    action: str,
    urgency: str,
    reason: str,
) -> None:
    """Every (action, urgency) pair with a non-empty reason round-trips.

    Property: for arbitrary draws from the action/urgency
    enumerations and any non-empty reason string, the validator
    yields `Success(NextOutput)` whose fields equal the input
    payload verbatim. The dataclass is the wire-round-trip
    fixed-point.
    """
    payload: dict[str, object] = {"action": action, "reason": reason, "urgency": urgency}
    result = next_output.validate_next_output(payload=payload, schema=_SCHEMA)
    match result:
        case Success(value):
            assert value == NextOutput(action=action, reason=reason, urgency=urgency)
        case _:
            msg = f"expected Success(NextOutput), got {result}"
            raise AssertionError(msg)
