"""Tests for livespec.parse.jsonc.

The jsonc module is a thin pure wrapper over the vendored
`jsoncomment` shim per PROPOSAL.md §"`livespec/parse/jsonc.py`"
and the briefing's outside-in walking direction. Comments
strip, JSON parses; errors flow as
`Failure(<LivespecError>)` on the railway.
"""

from __future__ import annotations

import json

from hypothesis import given
from hypothesis import strategies as st
from returns.result import Failure, Success

from livespec.errors import ValidationError
from livespec.parse import jsonc

__all__: list[str] = []


def test_jsonc_loads_empty_object_returns_success_empty_dict() -> None:
    """The simplest happy path: `{}` parses to `Success({})`."""
    result = jsonc.loads(text="{}")
    assert result == Success({})


def test_jsonc_loads_malformed_input_returns_validation_failure() -> None:
    """Malformed JSON returns `Failure(ValidationError(...))` on the railway.

    Pure-layer parsers MUST NOT raise; per the style doc §"Raising"
    rules, errors flow as `Failure(<LivespecError>)` payloads.
    """
    result = jsonc.loads(text="{not json}")
    match result:
        case Failure(ValidationError()):
            pass
        case _:
            raise AssertionError(f"expected Failure(ValidationError), got {result!r}")


@given(
    value=st.dictionaries(
        keys=st.text(min_size=1, max_size=10),
        values=st.integers(min_value=-1_000_000, max_value=1_000_000),
        max_size=5,
    ),
)
def test_jsonc_loads_matches_stdlib_for_plain_json_dicts(*, value: dict[str, int]) -> None:
    """For any small string-keyed int dict, `jsonc.loads(json.dumps(d))` round-trips to `Success(d)`.

    Plain JSON (no `//` or `/* */` comments) is a strict subset of
    JSONC, so the vendored shim must agree with stdlib `json` on
    every plain-JSON input. Hypothesis explores arbitrary key /
    value combinations within the small-dict envelope; any
    discrepancy with the stdlib parser is a real defect.
    """
    text = json.dumps(value)
    result = jsonc.loads(text=text)
    assert result == Success(value)
