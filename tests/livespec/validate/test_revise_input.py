"""Tests for livespec.validate.revise_input.

Per style doc §"Skill layout — `validate/`": each validator at
`validate/<name>.py` exports a function
`validate_<name>(payload: dict, schema: dict) -> Result[<Dataclass>, ValidationError]`
where `<Dataclass>` is the paired dataclass at
`schemas/dataclasses/<name>.py`.

Cycle 126 lands the success + rejection paths: a well-formed
revise-input payload validates and produces a RevisionInput
dataclass instance; a schema-violating payload returns
Failure(ValidationError).
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
from returns.result import Failure, Success

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.revise_input import RevisionInput
from livespec.validate import revise_input

__all__: list[str] = []

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude-plugin"
    / "scripts"
    / "livespec"
    / "schemas"
    / "revise_input.schema.json"
)


def test_validate_revise_input_returns_success_with_dataclass_for_valid_payload() -> None:
    """A well-formed revise-input payload validates to Success(RevisionInput).

    Payload mirrors the example in PROPOSAL.md §"`revise`" lines
    2375-2410: one decision with `proposal_topic`, `decision`,
    and `rationale`. The optional `author` field is omitted
    here so the validator's `.get("author")` -> None branch is
    exercised.
    """
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "decisions": [
            {
                "proposal_topic": "demo",
                "decision": "reject",
                "rationale": "Demo rationale.",
            },
        ],
    }
    result = revise_input.validate_revise_input(payload=payload, schema=schema)
    expected = RevisionInput(
        author=None,
        decisions=[
            {
                "proposal_topic": "demo",
                "decision": "reject",
                "rationale": "Demo rationale.",
            },
        ],
    )
    assert result == Success(expected)


def test_validate_revise_input_returns_failure_on_schema_violation() -> None:
    """A schema-violating payload returns Failure(ValidationError).

    The payload `{}` is a valid JSON object but is missing the
    required `decisions` array, so fastjsonschema raises
    JsonSchemaValueException, which the @safe-decorated raw
    validator lifts to Failure and the public seam .alt-maps to
    a ValidationError. The error message embeds the schema-
    violation context.
    """
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    result = revise_input.validate_revise_input(payload={}, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "revise_input:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_revise_input_carries_optional_author_when_present() -> None:
    """When `author` is present in the payload, RevisionInput.author is set.

    Drives the `.get("author")` branch where the value is the
    populated string rather than the missing-default None.
    """
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "author": "claude-opus-4-7",
        "decisions": [
            {
                "proposal_topic": "demo",
                "decision": "reject",
                "rationale": "Demo rationale.",
            },
        ],
    }
    result = revise_input.validate_revise_input(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert isinstance(value, RevisionInput)
            assert value.author == "claude-opus-4-7"
        case _:
            msg = f"expected Success(RevisionInput), got {result}"
            raise AssertionError(msg)


@given(
    rationale=st.text(min_size=1, max_size=200),
    author=st.text(min_size=1, max_size=80),
)
def test_validate_revise_input_round_trips_text_fields_through_success_path(
    *,
    rationale: str,
    author: str,
) -> None:
    """For arbitrary `rationale` + `author` strings, the success path preserves them verbatim.

    The validator's job on the success path is a pure projection
    of the validated payload into the `RevisionInput` dataclass;
    no normalization, no truncation, no encoding rewrites. This
    property asserts that contract holds for arbitrary user-
    provided text within the schema's `type: string` constraint.
    """
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "author": author,
        "decisions": [
            {
                "proposal_topic": "demo",
                "decision": "reject",
                "rationale": rationale,
            },
        ],
    }
    result = revise_input.validate_revise_input(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.author == author
            assert value.decisions[0]["rationale"] == rationale
        case _:
            msg = f"expected Success(RevisionInput), got {result}"
            raise AssertionError(msg)
