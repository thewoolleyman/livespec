"""Tests for livespec.parse.jsonc.

The jsonc module is a thin pure wrapper over the vendored
`jsoncomment` shim per PROPOSAL.md §"`livespec/parse/jsonc.py`"
and the briefing's outside-in walking direction. Comments
strip, JSON parses; errors flow as
`Failure(<LivespecError>)` on the railway.
"""

from __future__ import annotations

from returns.result import Success

from livespec.parse import jsonc

__all__: list[str] = []


def test_jsonc_loads_empty_object_returns_success_empty_dict() -> None:
    """The simplest happy path: `{}` parses to `Success({})`."""
    result = jsonc.loads(text="{}")
    assert result == Success({})
