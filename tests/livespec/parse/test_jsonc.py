"""Tests for livespec.parse.jsonc.

The jsonc module is a thin pure wrapper over the vendored
`jsoncomment` shim per PROPOSAL.md §"`livespec/parse/jsonc.py`"
and the briefing's outside-in walking direction. Comments
strip, JSON parses; errors flow as
`Failure(<LivespecError>)` on the railway.
"""

from __future__ import annotations

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
