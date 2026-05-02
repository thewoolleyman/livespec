"""Tests for livespec.validate.seed_input.

Per style doc §"Skill layout — `validate/`": each validator at
`validate/<name>.py` exports a function
`validate_<name>(payload: dict, schema: dict) -> Result[<Dataclass>, ValidationError]`
where `<Dataclass>` is the paired dataclass at
`schemas/dataclasses/<name>.py`.

Cycle 75 lands the success path: a well-formed seed-input
payload validates and produces a SeedInput dataclass instance.
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
from returns.result import Success

from livespec.schemas.dataclasses.seed_input import SeedInput
from livespec.validate import seed_input

__all__: list[str] = []

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude-plugin"
    / "scripts"
    / "livespec"
    / "schemas"
    / "seed_input.schema.json"
)


def test_validate_seed_input_returns_success_with_dataclass_for_valid_payload() -> None:
    """A well-formed seed-input payload validates to Success(SeedInput).

    Payload mirrors the example in PROPOSAL.md §"`seed`" (lines
    1937-1967): a `livespec` template choice with one main-spec
    file and an empty sub_specs list (the user-answered-no
    branch of the v020 Q2 dialogue).
    """
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "template": "livespec",
        "intent": "build a thing",
        "files": [{"path": "SPECIFICATION/spec.md", "content": "# Spec\n"}],
        "sub_specs": [],
    }
    result = seed_input.validate_seed_input(payload=payload, schema=schema)
    expected = SeedInput(
        template="livespec",
        intent="build a thing",
        files=[{"path": "SPECIFICATION/spec.md", "content": "# Spec\n"}],
        sub_specs=[],
    )
    assert result == Success(expected)


@given(intent=st.text(min_size=1, max_size=200))
def test_validate_seed_input_round_trips_intent_text(*, intent: str) -> None:
    """For arbitrary `intent` strings, the success path preserves the text verbatim.

    The validator's job on the success path is a pure projection
    of the validated payload into `SeedInput`; the `intent` field
    is captured verbatim into the auto-emitted seed proposed-
    change file, so any silent mutation here would corrupt
    downstream artifacts. The schema constrains `intent` to
    `type: string` with no further restrictions, so any string
    must round-trip unchanged.
    """
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "template": "livespec",
        "intent": intent,
        "files": [{"path": "SPECIFICATION/spec.md", "content": "# Spec\n"}],
        "sub_specs": [],
    }
    result = seed_input.validate_seed_input(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.intent == intent
        case _:
            msg = f"expected Success(SeedInput), got {result}"
            raise AssertionError(msg)
