"""Tests for livespec.parse.jsonc."""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from livespec.errors import PreconditionError
from livespec.parse import jsonc
from livespec.parse.jsonc import parse
from returns.result import Failure, Success

__all__: list[str] = []


def test_well_formed_object() -> None:
    result = parse(text='{"a": 1, "b": "two"}')
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert parsed == {"a": 1, "b": "two"}


def test_empty_object() -> None:
    result = parse(text="{}")
    assert isinstance(result, Success)
    assert result.unwrap() == {}


def test_line_comments_are_stripped() -> None:
    """The vendored shim strips `//` comments before stdlib json.loads."""
    text = """
    {
        // a leading comment
        "x": 1
    }
    """
    result = parse(text=text)
    assert isinstance(result, Success)
    assert result.unwrap() == {"x": 1}


def test_block_comments_are_stripped() -> None:
    """The vendored shim strips `/* */` block comments."""
    text = """
    {
        /* a block comment */
        "x": 1
    }
    """
    result = parse(text=text)
    assert isinstance(result, Success)
    assert result.unwrap() == {"x": 1}


def test_malformed_json_returns_precondition_error() -> None:
    """`json.JSONDecodeError` flows through @safe → Failure(PreconditionError)."""
    result = parse(text="{not valid json")
    assert isinstance(result, Failure)
    err = result.failure()
    assert isinstance(err, PreconditionError)
    assert "JSONC parse failure" in str(err)
    assert "line" in str(err)


def test_array_top_level_returns_precondition_error() -> None:
    """The v1 contract requires top-level objects only."""
    result = parse(text="[1, 2, 3]")
    assert isinstance(result, Failure)
    err = result.failure()
    assert isinstance(err, PreconditionError)
    assert "must be an object" in str(err)
    assert "list" in str(err)


def test_scalar_top_level_returns_precondition_error() -> None:
    """A bare number / string / boolean is also rejected at the top level."""
    result = parse(text="42")
    assert isinstance(result, Failure)
    err = result.failure()
    assert isinstance(err, PreconditionError)
    assert "must be an object" in str(err)


def test_assert_never_guards_unexpected_raw_load_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The `case _: assert_never(raw_result)` guard fires when `_raw_load`
    returns something other than `Success`/`Failure` — a structural
    impossibility under the `@safe`-decorated production contract, but
    a defensive guard against refactor-induced type drift.

    Hand-rolled stub satisfies the keyword-only call shape that the
    decorated production callable carries; a positional-only `lambda`
    would TypeError before reaching the match statement.
    """

    def _stub(*, text: str) -> object:  # noqa: ARG001 — text matches the wrapped signature
        return object()

    monkeypatch.setattr(jsonc, "_raw_load", _stub)
    with pytest.raises(AssertionError, match="Expected code to be unreachable"):
        parse(text="{}")


@given(
    payload=st.dictionaries(
        keys=st.text(min_size=1, max_size=8).filter(lambda s: '"' not in s and "\\" not in s),
        values=st.one_of(st.integers(), st.text(max_size=8), st.booleans(), st.none()),
        max_size=5,
    ),
)
@settings(max_examples=30)
def test_pbt_round_trip_preserves_dict_payloads(*, payload: dict[str, Any]) -> None:
    """Any well-formed JSON object survives serialize+parse round-trip."""
    import json

    text = json.dumps(payload)
    result = parse(text=text)
    assert isinstance(result, Success)
    assert result.unwrap() == payload
