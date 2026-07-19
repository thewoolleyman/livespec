"""Beside-tests for jsonio.py — typed JSON-object parsing.

Run: ``uv run pytest .claude/skills/overseer/ -q`` (these beside-tests are NOT
in the product ``tests/`` tree). ``import jsonio`` resolves via conftest.py.
"""

import jsonio
import pytest


def test_parses_a_json_object():
    assert jsonio.parse_object('{"a": 1, "b": "two"}') == {"a": 1, "b": "two"}


def test_nested_values_survive_intact():
    """The narrowing is to `dict[str, object]`; it must not flatten or coerce values."""
    parsed = jsonio.parse_object('{"outer": {"inner": [1, 2]}}')
    assert parsed == {"outer": {"inner": [1, 2]}}


def test_empty_object_is_an_object_not_a_failure():
    """`{}` is falsy — callers must be able to tell it from a parse failure."""
    assert jsonio.parse_object("{}") == {}
    assert jsonio.parse_object("{}") is not None


@pytest.mark.parametrize(
    "text",
    [
        "not json at all",
        '{"unterminated": ',
        "",
        "   ",
    ],
)
def test_malformed_input_is_none_never_raises(text):
    assert jsonio.parse_object(text) is None


@pytest.mark.parametrize("text", ["[1, 2, 3]", '"a bare string"', "17", "null", "true"])
def test_valid_json_that_is_not_an_object_is_none(text):
    """A bare list or scalar parses fine but is not what any caller here wants."""
    assert jsonio.parse_object(text) is None


def test_parse_object_line_skips_blank_lines():
    assert jsonio.parse_object_line("") is None
    assert jsonio.parse_object_line("   \n") is None


def test_parse_object_line_parses_a_record():
    assert jsonio.parse_object_line('{"id": "x"}\n') == {"id": "x"}


def test_parse_object_line_rejects_a_malformed_record():
    assert jsonio.parse_object_line("{oops}\n") is None


def test_duplicate_keys_take_the_last_value():
    """Standard `json` behavior, pinned so a future parser swap cannot change it silently."""
    assert jsonio.parse_object('{"k": 1, "k": 2}') == {"k": 2}


# --------------------------------------------------------------------------- #
# as_list
# --------------------------------------------------------------------------- #


def test_as_list_narrows_a_list():
    assert jsonio.as_list([1, "two", None]) == [1, "two", None]


def test_as_list_preserves_the_empty_list():
    """`[]` is falsy — it must be distinguishable from "not a list"."""
    assert jsonio.as_list([]) == []
    assert jsonio.as_list([]) is not None


@pytest.mark.parametrize("value", [{"a": 1}, "string", 17, None, True])
def test_as_list_rejects_non_lists(value):
    assert jsonio.as_list(value) is None


# --------------------------------------------------------------------------- #
# as_float
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("value", "expected"),
    [(1, 1.0), (0, 0.0), (-3, -3.0), (1.5, 1.5), ("2.5", 2.5), ("7", 7.0), ("-0.5", -0.5)],
)
def test_as_float_coerces_numbers_and_numeric_strings(value, expected):
    assert jsonio.as_float(value) == expected


@pytest.mark.parametrize("value", [True, False])
def test_as_float_rejects_bools(value):
    """`bool` is an `int` subclass: without an explicit guard `true` would become 1.0."""
    assert jsonio.as_float(value) is None


@pytest.mark.parametrize("value", ["", "abc", "1.2.3", None, {"a": 1}, [1], object()])
def test_as_float_rejects_non_numeric_values(value):
    assert jsonio.as_float(value) is None


def test_as_float_returns_zero_not_none_for_zero():
    """0.0 is falsy — a caller testing `is None` must not confuse it with absence."""
    assert jsonio.as_float(0) == 0.0
    assert jsonio.as_float(0) is not None
