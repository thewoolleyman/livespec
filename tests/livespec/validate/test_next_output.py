"""Tests for livespec.validate.next_output.

Per style doc §"Skill layout — `validate/`": the validator
at `validate/next_output.py` exports `validate_next_output(
payload, schema)` returning `Result[NextOutput, ValidationError]`.
The payload carries two required top-level keys — `candidates`
(array of `{action, reason, urgency, target?}` objects with
strict enum membership on `action` and `urgency`) and
`pagination` (`{offset, limit, total, has_more}`) — per
`SPECIFICATION/contracts.md` §"/livespec:next spec-side
thin-transport skill" → "Output schema".
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.next_output import (
    NextCandidate,
    NextOutput,
    NextPagination,
)
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


def _pagination_dict(
    *,
    offset: int = 0,
    limit: int = 5,
    total: int = 0,
    has_more: bool = False,
) -> dict[str, object]:
    """Build a conformant pagination block with overridable fields."""
    return {"offset": offset, "limit": limit, "total": total, "has_more": has_more}


def test_validate_next_output_returns_success_for_well_formed_payload() -> None:
    """A conformant payload returns Success(NextOutput) with nested dataclasses."""
    payload: dict[str, object] = {
        "candidates": [
            {
                "action": "revise",
                "reason": "1 proposed change pending",
                "urgency": "medium",
                "target": "proposed_changes/topic-x.md",
            },
        ],
        "pagination": _pagination_dict(total=1),
    }
    result = next_output.validate_next_output(payload=payload, schema=_SCHEMA)
    assert result == Success(
        NextOutput(
            candidates=(
                NextCandidate(
                    action="revise",
                    reason="1 proposed change pending",
                    urgency="medium",
                    target="proposed_changes/topic-x.md",
                ),
            ),
            pagination=NextPagination(offset=0, limit=5, total=1, has_more=False),
        ),
    )


def test_validate_next_output_accepts_empty_candidates_array() -> None:
    """`candidates: []` (the no-work signal) is schema-conformant."""
    payload: dict[str, object] = {
        "candidates": [],
        "pagination": _pagination_dict(),
    }
    result = next_output.validate_next_output(payload=payload, schema=_SCHEMA)
    assert result == Success(
        NextOutput(
            candidates=(),
            pagination=NextPagination(offset=0, limit=5, total=0, has_more=False),
        ),
    )


def test_validate_next_output_maps_missing_target_to_none() -> None:
    """A candidate without `target` constructs NextCandidate(target=None)."""
    payload: dict[str, object] = {
        "candidates": [
            {"action": "prune-history", "reason": "21 versions", "urgency": "low"},
        ],
        "pagination": _pagination_dict(total=1),
    }
    result = next_output.validate_next_output(payload=payload, schema=_SCHEMA)
    match result:
        case Success(value):
            assert value.candidates[0].target is None
        case _:
            msg = f"expected Success(NextOutput), got {result}"
            raise AssertionError(msg)


def test_validate_next_output_returns_failure_on_invalid_action_enum() -> None:
    """A candidate with an out-of-enum `action` returns Failure(ValidationError)."""
    payload: dict[str, object] = {
        "candidates": [
            {"action": "do-something-novel", "reason": "synthetic", "urgency": "low"},
        ],
        "pagination": _pagination_dict(total=1),
    }
    result = next_output.validate_next_output(payload=payload, schema=_SCHEMA)
    match result:
        case Failure(ValidationError() as err):
            assert "next_output:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_next_output_returns_failure_on_missing_pagination() -> None:
    """A payload missing `pagination` returns Failure(ValidationError).

    Drives the top-level `required` array: fastjsonschema
    rejects payloads that omit either `candidates` or
    `pagination`.
    """
    payload: dict[str, object] = {"candidates": []}
    result = next_output.validate_next_output(payload=payload, schema=_SCHEMA)
    match result:
        case Failure(ValidationError() as err):
            assert "next_output:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_next_output_returns_failure_on_missing_candidate_field() -> None:
    """A candidate missing `urgency` returns Failure(ValidationError).

    Drives the per-item `required` array on `candidates.items`.
    """
    payload: dict[str, object] = {
        "candidates": [{"action": "none", "reason": "nothing pressing"}],
        "pagination": _pagination_dict(total=1),
    }
    result = next_output.validate_next_output(payload=payload, schema=_SCHEMA)
    match result:
        case Failure(ValidationError() as err):
            assert "next_output:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_next_output_returns_failure_on_unknown_field() -> None:
    """A payload with an extra top-level field returns Failure(ValidationError).

    Drives `additionalProperties: false`: fastjsonschema
    rejects any field not enumerated in the schema's
    `properties` keyset.
    """
    payload: dict[str, object] = {
        "candidates": [],
        "pagination": _pagination_dict(),
        "extra": "field",
    }
    result = next_output.validate_next_output(payload=payload, schema=_SCHEMA)
    match result:
        case Failure(ValidationError() as err):
            assert "next_output:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_next_output_returns_failure_on_negative_offset() -> None:
    """`pagination.offset < 0` returns Failure(ValidationError).

    Drives the `minimum: 0` bound on the pagination block so the
    schema (not just the CLI gate) rejects out-of-range echoes.
    """
    payload: dict[str, object] = {
        "candidates": [],
        "pagination": _pagination_dict(offset=-1),
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
        ["revise", "propose-change", "critique", "prune-history", "none"],
    ),
    urgency=st.sampled_from(["high", "medium", "low"]),
    reason=st.text(min_size=1, max_size=80),
    target=st.one_of(st.none(), st.text(min_size=1, max_size=40)),
    pagination=st.fixed_dictionaries(
        {
            "offset": st.integers(min_value=0, max_value=1000),
            "limit": st.integers(min_value=1, max_value=1000),
            "total": st.integers(min_value=0, max_value=1000),
            "has_more": st.booleans(),
        },
    ),
)
def test_validate_next_output_round_trips_every_enum_combination(
    *,
    action: str,
    urgency: str,
    reason: str,
    target: str | None,
    pagination: dict[str, Any],
) -> None:
    """Every conformant (candidate, pagination) draw round-trips verbatim.

    Property: for arbitrary draws from the action/urgency
    enumerations, any non-empty reason, an optional target, and
    in-range pagination integers, the validator yields
    `Success(NextOutput)` whose nested dataclasses equal the
    input payload verbatim. The dataclasses are the
    wire-round-trip fixed-point.
    """
    candidate: dict[str, Any] = {"action": action, "reason": reason, "urgency": urgency}
    if target is not None:
        candidate["target"] = target
    payload: dict[str, object] = {
        "candidates": [candidate],
        "pagination": dict(pagination),
    }
    result = next_output.validate_next_output(payload=payload, schema=_SCHEMA)
    match result:
        case Success(value):
            assert value == NextOutput(
                candidates=(
                    NextCandidate(action=action, reason=reason, urgency=urgency, target=target),
                ),
                pagination=NextPagination(
                    offset=pagination["offset"],
                    limit=pagination["limit"],
                    total=pagination["total"],
                    has_more=pagination["has_more"],
                ),
            )
        case _:
            msg = f"expected Success(NextOutput), got {result}"
            raise AssertionError(msg)
