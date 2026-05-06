"""Pure restricted-YAML front-matter parser.

Per §"Revision file
format": values MUST be JSON-compatible scalars (strings,
integers, booleans, `null`); no lists, no nested dicts, no
anchors, no flow style. Schema-level `additionalProperties: false`
owns unknown-key rejection; this module's job is to reject
MALFORMED keys (per the deferred-items.md "front-matter-parser"
entry, paired schemas live at
`schemas/proposed_change_front_matter.schema.json` and
`schemas/revision_front_matter.schema.json`).

The parser is hand-authored (no YAML library is vendored under
`.claude-plugin/scripts/_vendor/`). Errors flow as
`Failure(ValidationError(...))` on the railway; this module
performs no I/O and never bare-raises.

Grammar (deliberately narrow):

  document  := delim line* delim body
  delim     := "---\\n"
  line      := key WS* ":" WS* value "\\n"
  key       := /^[a-zA-Z_][a-zA-Z0-9_]*$/   (Python-identifier-like)
  value     := scalar
  scalar    := "null" | "true" | "false" | INT | quoted_string
             | bare_string
  quoted_string := double-quote-delimited (no escape support)
  bare_string   := non-empty stripped run of safe characters

Reject paths (each → `Failure(ValidationError)`):

  no leading "---\\n"; unterminated front-matter; lines that
  start with "#" (comments); blank lines inside the block;
  duplicate keys; lines without a ":"; flow-style "[" / "{"
  in values; YAML anchors ("&") / aliases ("*") in values;
  block-style continuation lines starting with " " or "\\t";
  empty / non-identifier keys; empty values; unbalanced quotes.
"""

from __future__ import annotations

import re
from typing import Any

from returns.result import Failure, Result, Success

from livespec.errors import ValidationError

__all__: list[str] = ["parse_front_matter"]


_DELIM = "---"
_KEY_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_INT_RE = re.compile(r"^-?\d+$")
# Characters that signal flow-style / anchor / alias in YAML; the
# parser rejects values containing any of them at the leading
# position. Quoted strings strip surrounding quotes BEFORE this
# check, so e.g. `"[bracket-text]"` parses as a string.
_FLOW_LEAD_CHARS = frozenset("[{&*")
# Indented continuation lines (block-style nesting / list items)
# start with one of these characters; the restricted-YAML grammar
# admits only flat `key: value` lines.
_CONTINUATION_LEAD_CHARS = (" ", "\t")
# Minimum well-formed quoted-string token length: opening `"`,
# zero-or-more body characters, closing `"` — i.e. two delimiters
# alone (`""`) is the empty-string case and the smallest valid
# token.
_MIN_QUOTED_LEN = 2
# Keyword scalars whose post-strip raw text maps directly to a
# Python value. Routed via dict dispatch to keep `_parse_value`
# under the PLR0911 return-statement cap and to keep the
# bool-literals out of `Success(...)` call-site argv (FBT003).
_KEYWORD_VALUES: dict[str, Any] = {
    "null": None,
    "true": True,
    "false": False,
}


def _split_front_matter(*, text: str) -> Result[list[str], ValidationError]:
    """Locate the front-matter block bounded by `---\\n` markers.

    Returns the body lines (between the leading and closing
    delimiters, exclusive) on success. The leading delimiter MUST
    be the very first line of the input.
    """
    if not text.startswith(f"{_DELIM}\n"):
        return Failure(ValidationError("front-matter: missing leading `---` delimiter"))
    lines = text.split("\n")
    # `lines[0]` is the leading "---". Search for the closing
    # "---" line strictly after it.
    closing_index: int | None = None
    for index in range(1, len(lines)):
        if lines[index] == _DELIM:
            closing_index = index
            break
    if closing_index is None:
        return Failure(ValidationError("front-matter: unterminated (no closing `---`)"))
    return Success(lines[1:closing_index])


def _parse_quoted(*, raw: str) -> Result[str, ValidationError]:
    """Parse a `"..."` quoted scalar.

    The caller has already verified `raw.startswith('"')`. The
    full token must end in `"` AND be at least `_MIN_QUOTED_LEN`
    characters long (so that `""` is the empty string and `"`
    alone is rejected). No escape sequence support — the
    restricted-YAML grammar admits only literal characters
    between the delimiters.
    """
    if not raw.endswith('"') or len(raw) < _MIN_QUOTED_LEN:
        return Failure(
            ValidationError(f"front-matter: unbalanced quoted value: {raw!r}"),
        )
    return Success(raw[1:-1])


def _parse_value(*, raw: str) -> Result[Any, ValidationError]:
    """Parse a single scalar value from its post-colon raw text.

    The raw text has already had its surrounding whitespace
    stripped by the caller. Recognized scalars (in dispatch
    order): `null`, `true`, `false`, integer literals,
    double-quoted strings, bare strings.
    """
    if not raw:
        return Failure(ValidationError("front-matter: empty value (use explicit `null`)"))
    if raw[0] in _FLOW_LEAD_CHARS:
        return Failure(
            ValidationError(
                f"front-matter: flow-style / anchor / alias not allowed: {raw!r}",
            ),
        )
    if raw in _KEYWORD_VALUES:
        return Success(_KEYWORD_VALUES[raw])
    if _INT_RE.fullmatch(raw):
        return Success(int(raw))
    if raw.startswith('"'):
        return _parse_quoted(raw=raw)
    return Success(raw)


def _validate_line_shape(*, line: str) -> Result[None, ValidationError]:
    """Reject lines that are blank / comments / indented continuations.

    Pulled out of `_parse_line` to keep that function under
    PLR0911's return-statement cap. A successful return signals
    "the line is admissible to key/value extraction"; an empty
    `Success(None)` carries no payload.
    """
    if line == "":
        return Failure(ValidationError("front-matter: blank line not allowed"))
    if line.startswith("#"):
        return Failure(ValidationError("front-matter: comment line not allowed"))
    if line.startswith(_CONTINUATION_LEAD_CHARS):
        return Failure(
            ValidationError(
                f"front-matter: indented continuation line not allowed: {line!r}",
            ),
        )
    return Success(None)


def _split_key_value(*, line: str) -> Result[tuple[str, str], ValidationError]:
    """Split a line into (key, raw-value) on the first `:`.

    The caller has already verified the line is admissible (not
    blank / comment / indented). Returns Failure on missing `:`,
    empty key, or malformed key.
    """
    if ":" not in line:
        return Failure(ValidationError(f"front-matter: missing `:` in line: {line!r}"))
    key_part, _sep, value_part = line.partition(":")
    key_stripped = key_part.strip()
    if not key_stripped:
        return Failure(ValidationError(f"front-matter: empty key in line: {line!r}"))
    if not _KEY_RE.fullmatch(key_stripped):
        return Failure(
            ValidationError(
                f"front-matter: malformed key (must match {_KEY_RE.pattern!r}): "
                f"{key_stripped!r}",
            ),
        )
    return Success((key_stripped, value_part.strip()))


def _parse_line(*, line: str) -> Result[tuple[str, Any], ValidationError]:
    """Parse a single non-delimiter line into a (key, value) pair."""
    return (
        _validate_line_shape(line=line)
        .bind(lambda _none: _split_key_value(line=line))
        .bind(
            lambda key_and_raw: _parse_value(raw=key_and_raw[1]).map(
                lambda parsed: (key_and_raw[0], parsed),
            ),
        )
    )


def parse_front_matter(*, text: str) -> Result[dict[str, Any], ValidationError]:
    """Parse a restricted-YAML front-matter block from a `.md` file.

    `text` is the entire file content; it MUST start with
    `---\\n` and contain a closing `---\\n` line. Body content
    after the closing delimiter is ignored. Returns
    `Success(dict)` on a well-formed block (where each value is
    JSON-compatible: `str`, `int`, `bool`, or `None`); returns
    `Failure(ValidationError(...))` on any malformation.

    Pure: no I/O, never bare-raises.
    """
    split_result = _split_front_matter(text=text)
    if isinstance(split_result, Failure):
        return split_result
    body_lines = split_result.unwrap()
    payload: dict[str, Any] = {}
    for line in body_lines:
        line_result = _parse_line(line=line)
        if isinstance(line_result, Failure):
            return line_result
        key, value = line_result.unwrap()
        if key in payload:
            return Failure(
                ValidationError(f"front-matter: duplicate key: {key!r}"),
            )
        payload[key] = value
    return Success(payload)
