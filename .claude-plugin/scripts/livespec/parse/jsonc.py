"""Thin pure wrapper over the vendored `jsoncomment` shim (v026 D1).

`parse/` is the pure layer: no `livespec.io.*` imports, no
filesystem, no `subprocess`, no `socket`. Functions here accept
in-memory `str` and return `Result[<value>, <LivespecError>]`.
Failures flow on the `Failure` track via constructed (NOT raised)
LivespecError instances, preserving the raise-discipline rule
that LivespecError raise-sites stay in `io/**`.

Per style doc §"Error Handling Discipline" lines 545-560, the
third-party `json.JSONDecodeError` (a domain-meaningful exception)
is caught via `@safe(exceptions=(json.JSONDecodeError,))` rather
than an explicit `try/except` clause; this satisfies
`check-no-except-outside-io` (no explicit `except` outside io/**
except the supervisor bug-catcher).

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
from typing import Any, NoReturn

import jsoncomment
from returns.result import Failure, Result, Success, safe
from typing_extensions import assert_never

from livespec.errors import PreconditionError

__all__: list[str] = [
    "parse",
]


@safe(exceptions=(json.JSONDecodeError,))
def _raw_load(*, text: str) -> object:
    """Call the vendored jsoncomment shim under `@safe` to wrap
    `json.JSONDecodeError` into the `Failure` track.

    The vendored shim defers to stdlib `json.loads` after stripping
    comments; `json.JSONDecodeError` is the only domain-meaningful
    exception it raises on bad-but-loadable input. Other exceptions
    (e.g., `TypeError` if `text` is not a string) propagate as bugs.
    """
    return jsoncomment.loads(text)


def parse(*, text: str) -> Result[dict[str, Any], PreconditionError]:
    """Parse `text` as JSONC and return the top-level dict.

    Returns:

    - `Success(parsed)` when `text` parses cleanly to a JSON object.
    - `Failure(PreconditionError(<message>))` when:
      - `text` is malformed JSONC (caught `json.JSONDecodeError`
        via `@safe` in `_raw_load`).
      - The top-level JSON value is not an object (livespec's v1
        consumers — `.livespec.jsonc`, JSON Schemas,
        propose-change/revise payloads — all expect objects;
        widen to `Result[object, ...]` if a future caller needs
        top-level arrays or scalars).

    Errors are CONSTRUCTED (not raised) and shipped via `Failure`,
    keeping the LivespecError raise-discipline confined to
    `io/**`.
    """
    raw_result = _raw_load(text=text)
    match raw_result:
        case Success(parsed):
            if isinstance(parsed, dict):
                return Success(parsed)
            return Failure(
                PreconditionError(
                    f"JSONC top-level value must be an object; "
                    f"got {type(parsed).__name__}",
                ),
            )
        case Failure(exc):
            return Failure(
                PreconditionError(
                    f"JSONC parse failure at line {exc.lineno}, "
                    f"column {exc.colno}: {exc.msg}",
                ),
            )
        case _ as unreachable:
            _unreachable(unreachable)


def _unreachable(value: object) -> NoReturn:
    assert_never(value)  # type: ignore[arg-type]
