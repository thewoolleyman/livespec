"""Pure JSONC parser: thin Result-wrapping shim over vendored `jsoncomment`.

Per: a pure wrapper that
strips `//` and `/* */` comments via the vendored shim, then
delegates to stdlib JSON. Errors flow as
`Failure(<LivespecError>)` on the railway; this module performs
no I/O and never bare-raises.

The `@safe(exceptions=(...))` decorator + `.alt(...)` pattern is
the canonical way to convert third-party domain-meaningful
exceptions into `LivespecError`-track failures (see
python-skill-script-style-requirements.md §"Raising").

The Phase-3 driver is `.livespec.jsonc` parsing during the seed
flow; cycles widen this module one behavior at a time as
consumers surface new failure modes.
"""

from __future__ import annotations

import json
from typing import Any

import jsoncomment
from returns.result import Result, safe

from livespec.errors import ValidationError

__all__: list[str] = ["loads"]


@safe(exceptions=(json.JSONDecodeError,))
def _raw_loads(*, text: str) -> Any:
    """Decorator-lifted call into the vendored shim. `@safe`
    converts the JSONDecodeError raise-path into Failure carrying
    the raw exception; `loads` then maps that to ValidationError.
    """
    return jsoncomment.loads(text)


def loads(*, text: str) -> Result[Any, ValidationError]:
    """Parse a JSONC string and return `Success(parsed-value)` or
    `Failure(ValidationError(...))` on malformed input.

    Pure: no I/O, never bare-raises. `JSONDecodeError` from the
    vendored shim is mapped to `ValidationError` via the canonical
    `@safe`-+-`.alt(...)` pattern.
    """
    return _raw_loads(text=text).alt(
        lambda exc: ValidationError(f"jsonc parse failed: {exc}"),
    )
