"""Tests for livespec.parse.front_matter.

The restricted-YAML front-matter parser per
SPECIFICATION/spec.md §"Proposed-change and revision file
formats". Format restrictions:

    Format restrictions: values MUST be JSON-compatible scalars
    (strings, integers, booleans, `null`); no lists, no nested
    dicts, no anchors, no flow style. Unknown keys are a parse
    error.

The parser is hand-authored (no YAML library is vendored under
`.claude-plugin/scripts/_vendor/`); it walks the body lines
between the leading and closing `---` markers, parses each as
`<key>: <value>` per a deliberately narrow grammar, and returns
`Result[dict[str, Any], ValidationError]`.

Per `tests/livespec/parse/CLAUDE.md`: pure-layer tests must
include at least one `@given(...)`-decorated property-based
test (enforced by `check-pbt-coverage-pure-modules`).
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
from livespec.errors import ValidationError
from livespec.parse.front_matter import parse_front_matter
from returns.result import Failure, Success

__all__: list[str] = []


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


def test_single_key_value_returns_success_one_key_dict() -> None:
    """The simplest happy path: one `key: value` line."""
    result = parse_front_matter(text="---\nkey: value\n---\nbody\n")
    assert result == Success({"key": "value"})


def test_multiple_keys_each_round_trip_to_dict() -> None:
    """Five `key: value` lines parse to a five-entry dict."""
    text = (
        "---\n"
        "topic: my-topic\n"
        "author: alice\n"
        "created_at: 2026-05-05T11:00:00Z\n"
        "decision: accept\n"
        "revised_at: 2026-05-05T11:30:00Z\n"
        "---\n"
        "body\n"
    )
    result = parse_front_matter(text=text)
    assert result == Success(
        {
            "topic": "my-topic",
            "author": "alice",
            "created_at": "2026-05-05T11:00:00Z",
            "decision": "accept",
            "revised_at": "2026-05-05T11:30:00Z",
        },
    )


def test_empty_front_matter_returns_success_empty_dict() -> None:
    """An empty front-matter block (immediate close) returns `Success({})`."""
    result = parse_front_matter(text="---\n---\nbody\n")
    assert result == Success({})


def test_value_null_parses_to_none() -> None:
    """`null` parses to Python `None` per JSON-compatible scalar rule."""
    result = parse_front_matter(text="---\nkey: null\n---\n")
    assert result == Success({"key": None})


def test_value_true_parses_to_python_true() -> None:
    """`true` parses to Python `True` per JSON-compatible scalar rule."""
    result = parse_front_matter(text="---\nkey: true\n---\n")
    assert result == Success({"key": True})


def test_value_false_parses_to_python_false() -> None:
    """`false` parses to Python `False` per JSON-compatible scalar rule."""
    result = parse_front_matter(text="---\nkey: false\n---\n")
    assert result == Success({"key": False})


def test_value_integer_parses_to_python_int() -> None:
    """Bare integers parse to Python `int` per JSON-compatible scalar rule."""
    result = parse_front_matter(text="---\nkey: 42\n---\n")
    assert result == Success({"key": 42})


def test_value_negative_integer_parses_to_python_int() -> None:
    """Bare negative integers parse to Python `int`."""
    result = parse_front_matter(text="---\nkey: -7\n---\n")
    assert result == Success({"key": -7})


def test_value_quoted_string_strips_quotes() -> None:
    """Double-quoted strings have their quotes stripped."""
    result = parse_front_matter(text='---\nkey: "quoted string"\n---\n')
    assert result == Success({"key": "quoted string"})


def test_value_quoted_preserves_what_would_be_a_keyword() -> None:
    """A quoted `"true"` stays a string (the quotes force string interpretation)."""
    result = parse_front_matter(text='---\nkey: "true"\n---\n')
    assert result == Success({"key": "true"})


def test_value_quoted_preserves_what_would_be_an_integer() -> None:
    """A quoted `"42"` stays a string (the quotes force string interpretation)."""
    result = parse_front_matter(text='---\nkey: "42"\n---\n')
    assert result == Success({"key": "42"})


def test_value_bare_string_returns_string() -> None:
    """A bare unquoted token that is not a keyword/int parses as a string."""
    result = parse_front_matter(text="---\nkey: bare string\n---\n")
    assert result == Success({"key": "bare string"})


def test_value_unicode_in_string_preserved() -> None:
    """Unicode characters in string values are preserved verbatim."""
    result = parse_front_matter(text="---\nkey: hello 世界\n---\n")
    assert result == Success({"key": "hello 世界"})


def test_value_leading_trailing_whitespace_stripped() -> None:
    """Leading and trailing whitespace on values is stripped."""
    result = parse_front_matter(text="---\nkey:    spaced value   \n---\n")
    assert result == Success({"key": "spaced value"})


def test_value_iso_8601_datetime_stays_string() -> None:
    """ISO 8601 datetime strings stay strings (the schema/dataclass owns
    type promotion)."""
    result = parse_front_matter(text="---\ncreated_at: 2026-05-05T11:00:00Z\n---\n")
    assert result == Success({"created_at": "2026-05-05T11:00:00Z"})


def test_value_kebab_case_string_stays_string() -> None:
    """A kebab-case identifier (e.g., a topic slug) stays a bare string."""
    result = parse_front_matter(text="---\ntopic: my-cool-topic\n---\n")
    assert result == Success({"topic": "my-cool-topic"})


def test_body_after_closing_delimiter_is_ignored() -> None:
    """Whatever appears after the closing `---` line is ignored entirely."""
    result = parse_front_matter(
        text="---\nkey: value\n---\n## body heading\nfree-form prose\n",
    )
    assert result == Success({"key": "value"})


def test_no_trailing_newline_after_body_still_parses() -> None:
    """A file without a trailing newline still parses correctly."""
    result = parse_front_matter(text="---\nkey: value\n---\nbody")
    assert result == Success({"key": "value"})


def test_no_body_after_closing_delimiter_still_parses() -> None:
    """A file with nothing after the closing `---` still parses."""
    result = parse_front_matter(text="---\nkey: value\n---\n")
    assert result == Success({"key": "value"})


def test_proposed_change_front_matter_real_world_shape() -> None:
    """The fields validated by the proposed_change schema parse cleanly."""
    text = (
        "---\n"
        "topic: example-topic\n"
        "author: alice\n"
        "created_at: 2026-05-05T11:00:00Z\n"
        "---\n"
        "## Proposal: example\n"
    )
    result = parse_front_matter(text=text)
    assert result == Success(
        {
            "topic": "example-topic",
            "author": "alice",
            "created_at": "2026-05-05T11:00:00Z",
        },
    )


def test_revision_front_matter_real_world_shape() -> None:
    """The fields validated by the revision schema parse cleanly."""
    text = (
        "---\n"
        "proposal: example.md\n"
        "decision: accept\n"
        "revised_at: 2026-05-05T11:30:00Z\n"
        "author_human: alice\n"
        "author_llm: livespec-seed\n"
        "---\n"
        "## Decision and Rationale\n"
    )
    result = parse_front_matter(text=text)
    assert result == Success(
        {
            "proposal": "example.md",
            "decision": "accept",
            "revised_at": "2026-05-05T11:30:00Z",
            "author_human": "alice",
            "author_llm": "livespec-seed",
        },
    )


# ---------------------------------------------------------------------------
# Reject paths
# ---------------------------------------------------------------------------


def _assert_validation_failure(result: object) -> None:
    """Helper to assert `result` is `Failure(ValidationError(...))`."""
    match result:
        case Failure(ValidationError()):
            return
        case _:
            raise AssertionError(
                f"expected Failure(ValidationError), got {result!r}",
            )


def test_no_leading_delimiter_rejected() -> None:
    """Text that does not start with `---\\n` is rejected."""
    _assert_validation_failure(parse_front_matter(text="key: value\n---\nbody\n"))


def test_leading_blank_line_before_delimiter_rejected() -> None:
    """A leading blank line before the `---` is rejected (strict start)."""
    _assert_validation_failure(parse_front_matter(text="\n---\nkey: value\n---\n"))


def test_unterminated_front_matter_rejected() -> None:
    """No closing `---` line is rejected."""
    _assert_validation_failure(parse_front_matter(text="---\nkey: value\nbody\n"))


def test_empty_text_rejected() -> None:
    """Empty input is rejected (no leading delimiter)."""
    _assert_validation_failure(parse_front_matter(text=""))


def test_only_leading_delimiter_rejected() -> None:
    """A bare `---\\n` with nothing after is rejected (no closing)."""
    _assert_validation_failure(parse_front_matter(text="---\n"))


def test_list_value_flow_style_rejected() -> None:
    """Flow-style list values (`[...]`) are rejected per restricted-YAML."""
    _assert_validation_failure(parse_front_matter(text="---\nkey: [1, 2, 3]\n---\n"))


def test_list_value_block_style_rejected() -> None:
    """Block-style lists (continuation `- item` lines) are rejected."""
    text = "---\nkey:\n  - item1\n  - item2\n---\n"
    _assert_validation_failure(parse_front_matter(text=text))


def test_nested_dict_flow_style_rejected() -> None:
    """Flow-style nested dicts (`{...}`) are rejected per restricted-YAML."""
    _assert_validation_failure(parse_front_matter(text="---\nkey: {a: 1}\n---\n"))


def test_nested_dict_block_style_rejected() -> None:
    """Block-style nested dicts (indented child) are rejected."""
    text = "---\nkey:\n  nested: value\n---\n"
    _assert_validation_failure(parse_front_matter(text=text))


def test_yaml_anchor_rejected() -> None:
    """YAML anchors (`&name`) are rejected per restricted-YAML."""
    _assert_validation_failure(parse_front_matter(text="---\nkey: &foo value\n---\n"))


def test_yaml_alias_rejected() -> None:
    """YAML aliases (`*name`) are rejected per restricted-YAML."""
    _assert_validation_failure(parse_front_matter(text="---\nkey: *foo\n---\n"))


def test_malformed_line_no_colon_rejected() -> None:
    """A line without a `:` separator is rejected."""
    _assert_validation_failure(parse_front_matter(text="---\nnokey\n---\n"))


def test_empty_key_rejected() -> None:
    """A line with an empty key (`: value`) is rejected."""
    _assert_validation_failure(parse_front_matter(text="---\n: value\n---\n"))


def test_whitespace_only_key_rejected() -> None:
    """A line with only whitespace before the colon is rejected."""
    _assert_validation_failure(parse_front_matter(text="---\n   : value\n---\n"))


def test_empty_value_rejected() -> None:
    """A line with `key:` and no value is rejected (use explicit `null`)."""
    _assert_validation_failure(parse_front_matter(text="---\nkey:\n---\n"))


def test_duplicate_keys_rejected() -> None:
    """Duplicate keys are rejected (restricted-YAML; not last-wins)."""
    text = "---\nkey: a\nkey: b\n---\n"
    _assert_validation_failure(parse_front_matter(text=text))


def test_comment_line_inside_front_matter_rejected() -> None:
    """Comment lines (`# ...`) inside the front-matter are rejected.

    Restricted-YAML is a minimal `key: value`-only grammar; comment
    lines have no purpose inside a parser-only front-matter block.
    """
    _assert_validation_failure(parse_front_matter(text="---\n# comment\nkey: v\n---\n"))


def test_blank_line_inside_front_matter_rejected() -> None:
    """Blank lines inside the front-matter are rejected (strict)."""
    _assert_validation_failure(parse_front_matter(text="---\nkey: v\n\nfoo: b\n---\n"))


def test_key_with_dot_rejected() -> None:
    """Keys containing `.` (suggestive of nesting) are rejected."""
    _assert_validation_failure(parse_front_matter(text="---\nkey.sub: value\n---\n"))


def test_key_with_internal_whitespace_rejected() -> None:
    """Keys containing whitespace are rejected (malformed identifier)."""
    _assert_validation_failure(parse_front_matter(text="---\nkey two: value\n---\n"))


def test_key_with_hyphen_rejected() -> None:
    """Keys containing `-` are rejected (matches Python-identifier regex)."""
    _assert_validation_failure(parse_front_matter(text="---\nkey-two: value\n---\n"))


def test_key_starting_with_digit_rejected() -> None:
    """Keys starting with a digit are rejected (matches identifier regex)."""
    _assert_validation_failure(parse_front_matter(text="---\n1key: value\n---\n"))


def test_value_unbalanced_quotes_rejected() -> None:
    """A value with an opening but no closing quote is rejected."""
    _assert_validation_failure(parse_front_matter(text='---\nkey: "unclosed\n---\n'))


def test_value_quoted_with_trailing_garbage_rejected() -> None:
    """A quoted value followed by non-whitespace is rejected."""
    _assert_validation_failure(parse_front_matter(text='---\nkey: "v" extra\n---\n'))


# ---------------------------------------------------------------------------
# Property-based tests (Hypothesis)
# ---------------------------------------------------------------------------


@given(
    keys_values=st.dictionaries(
        keys=st.from_regex(r"^[a-zA-Z_][a-zA-Z0-9_]{0,15}$", fullmatch=True),
        values=st.text(
            alphabet=st.characters(
                blacklist_categories=("Cs",),
                blacklist_characters='\n\r":{}[]&*#',
            ),
            min_size=1,
            max_size=20,
        )
        .map(str.strip)
        .filter(
            lambda s: bool(s)
            and s not in {"true", "false", "null"}
            and not s.lstrip("-").isdigit(),
        ),
        max_size=5,
    ),
)
def test_round_trip_serialize_then_parse_returns_input(
    *,
    keys_values: dict[str, str],
) -> None:
    """For any small {identifier-key: bare-string-value} dict, the
    canonical serialization parses back to the input.

    Hypothesis explores arbitrary identifier keys + non-keyword
    string values; the serialized front-matter is
    `---\\n<key>: <value>\\n...---\\n`. Reserved tokens (`true`,
    `false`, `null`, integer-like) are excluded from the value
    strategy because the parser would interpret them as their
    typed equivalents — outside this round-trip's scope.
    """
    body = "".join(f"{k}: {v}\n" for k, v in keys_values.items())
    text = f"---\n{body}---\n"
    result = parse_front_matter(text=text)
    assert result == Success(keys_values)
