"""Typed JSON-object parsing for the overseer.

`json.loads` is typed as returning `Any`. Under a strict type checker that is
contagious: `isinstance(parsed, dict)` narrows only to `dict[Unknown, Unknown]`,
so every downstream `.get()` yields an unknown type and the checker can no longer
see the `isinstance` guards the call sites already perform on each field.

Funnelling every parse through this module fixes that once, at the boundary. A
JSON object's keys are strings by the grammar, so the narrowing to
`dict[str, object]` is a fact about JSON rather than a wish about this data — and
because the values come back as `object` rather than `Any`, the `isinstance`
checks at each call site become real, checked narrowings instead of decoration.

The alternative the product tree took for the same problem is a file-level
`# pyright: reportUnknown...=none` pragma on a dedicated helpers module. That is
the right call there (a pure-helper module, nothing else in it to weaken); here
the parsing is a few lines inside modules full of unrelated logic, so a
file-level pragma would silence three rules across code that should keep them.

Stdlib-only, like every module in this folder.
"""

from __future__ import annotations

import json
from typing import cast

__all__ = ["as_float", "as_list", "as_object", "parse_object", "parse_object_line"]


def as_object(value: object) -> dict[str, object] | None:
    """Narrow an ALREADY-PARSED JSON value to a string-keyed mapping, or None.

    For callers that must keep their own ``try``/``except`` around the parse —
    typically because they report a malformed file and a well-formed non-object
    file with DIFFERENT diagnostics, a distinction worth more than the few lines
    it costs. They keep their error handling and gain the narrowing.

    :func:`parse_object` is the one-call form for everyone else.
    """
    if not isinstance(value, dict):
        return None
    # Safe by the JSON grammar: object keys are always strings. This is the one
    # place the folder asserts that, so no call site has to.
    return cast("dict[str, object]", value)


def as_list(value: object) -> list[object] | None:
    """Narrow an already-parsed JSON value to a list, or None if it is not one.

    The list sibling of :func:`as_object`, and it exists for the same reason:
    ``isinstance(value, list)`` narrows only to ``list[Unknown]``, so iterating it
    yields unknowns and the per-element ``isinstance`` checks that follow stop
    meaning anything to a type checker. Elements come back as ``object``, which
    those checks then narrow for real.
    """
    if not isinstance(value, list):
        return None
    return cast("list[object]", value)


def as_float(value: object) -> float | None:
    """Coerce an already-parsed JSON scalar to a float, or None if it is not numeric.

    JSON numbers arrive as ``int`` or ``float``; a legacy hand-edited value may be
    a numeric string. Anything else — an object, an array, null, a non-numeric
    string — is not a number, and every caller here treats that as "no value"
    rather than as an error worth raising.

    ``bool`` is rejected deliberately. It is an ``int`` subclass, so a bare
    ``isinstance(value, int)`` would accept ``true`` and silently yield ``1.0``
    from something that was never a number.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def parse_object(text: str) -> dict[str, object] | None:
    """Parse ``text`` as a JSON object.

    Returns None if ``text`` is malformed JSON, or is valid JSON that is not an
    object (a bare list, string, or number). Never raises — callers in this
    folder are all fail-soft readers of files a human or another process may have
    corrupted, and a bad file must degrade one reader, never crash the daemon.
    """
    try:
        parsed: object = json.loads(text)
    except ValueError:
        return None
    return as_object(parsed)


def parse_object_line(line: str) -> dict[str, object] | None:
    """Parse one JSONL record, skipping blank lines.

    The same contract as :func:`parse_object`, plus: a line that is empty or
    whitespace-only returns None rather than being reported as malformed. Every
    JSONL reader here wants that, and doing it per-caller invited each to spell
    the blank-line check slightly differently.
    """
    if not line.strip():
        return None
    return parse_object(line)
