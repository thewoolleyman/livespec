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

from hypothesis import given, settings
from hypothesis import strategies as st
from livespec.schemas.dataclasses.seed_input import SeedInput
from livespec.validate import seed_input
from returns.result import Success

__all__: list[str] = []

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude-plugin"
    / "scripts"
    / "livespec"
    / "schemas"
    / "seed_input.schema.json"
)

# Module-level schema cache (v040 D1): hypothesis-based @given
# tests run the body ~100 times per invocation; reloading the schema
# from disk on each example pushes individual examples over the
# default 200ms hypothesis deadline under `pytest -n auto` xdist
# worker contention. Loading once at module-import time eliminates
# per-example file I/O and the associated timing nondeterminism.
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_validate_seed_input_returns_success_with_dataclass_for_valid_payload() -> None:
    """A well-formed seed-input payload validates to Success(SeedInput).

    Payload mirrors the example in PROPOSAL.md §"`seed`": a `livespec` template choice with one main-spec
    file and an empty sub_specs list (the user-answered-no
    branch of the v020 Q2 dialogue).
    """
    schema = _SCHEMA
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


@settings(deadline=None)
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
    schema = _SCHEMA
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
