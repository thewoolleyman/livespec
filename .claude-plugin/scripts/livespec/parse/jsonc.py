"""Thin pure wrapper over the vendored `jsoncomment` shim (v026 D1).

`parse/` is the pure layer: no `livespec.io.*` imports, no
filesystem, no `subprocess`, no `socket`. Functions here accept
in-memory `str` and return `Result[<value>, <LivespecError>]`.
Failures flow on the `Failure` track via constructed (NOT raised)
LivespecError instances, preserving the raise-discipline rule
that LivespecError raise-sites stay in `io/**`.

`jsonc.py` is the canonical JSONC entry point for the rest of
livespec. The vendored `jsoncomment` shim (post-v026 D1, drop-in
named `jsoncomment` so `import jsoncomment` resolves to the
hand-authored shim) strips `//` and `/* */` comments and defers
to stdlib `json.loads` for actual parsing. Multi-line strings
and trailing-commas — supported by upstream jsoncomment 0.4.2
but not by the v026 D1 shim — are NOT exposed here; widen the
shim one feature at a time if a future caller surfaces the
need.
"""
from __future__ import annotations

import json
from typing import Any

import jsoncomment
from returns.result import Failure, Result, Success

from livespec.errors import PreconditionError

__all__: list[str] = [
    "parse",
]


def parse(*, text: str) -> Result[dict[str, Any], PreconditionError]:
    """Parse `text` as JSONC and return the top-level dict.

    Returns:

    - `Success(parsed)` when `text` parses cleanly to a JSON object.
    - `Failure(PreconditionError(<message>))` when:
      - `text` is malformed JSONC (caught `json.JSONDecodeError`
        from the underlying `json.loads` after comment-stripping).
      - The top-level JSON value is not an object (livespec's v1
        consumers — `.livespec.jsonc`, JSON Schemas,
        propose-change/revise payloads — all expect objects;
        widen to `Result[object, ...]` if a future caller needs
        top-level arrays or scalars).

    Errors are CONSTRUCTED (not raised) and shipped via `Failure`,
    keeping the LivespecError raise-discipline confined to
    `io/**`.
    """
    try:
        parsed = jsoncomment.loads(text)
    except json.JSONDecodeError as e:
        return Failure(
            PreconditionError(
                f"JSONC parse failure at line {e.lineno}, column {e.colno}: {e.msg}",
            ),
        )
    if not isinstance(parsed, dict):
        return Failure(
            PreconditionError(
                f"JSONC top-level value must be an object; got {type(parsed).__name__}",
            ),
        )
    return Success(parsed)
