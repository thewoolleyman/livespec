"""Pure JSONC parser: thin Result-wrapping shim over vendored `jsoncomment`.

Per PROPOSAL.md §"`livespec/parse/jsonc.py`": a pure wrapper that
strips `//` and `/* */` comments via the vendored shim, then
delegates to stdlib JSON. Errors flow as
`Failure(<LivespecError>)` on the railway; this module performs
no I/O.

The Phase-3 driver is `.livespec.jsonc` parsing during the seed
flow; cycles widen this module one behavior at a time as
consumers surface new failure modes.
"""

from __future__ import annotations

from typing import Any

import jsoncomment
from returns.result import Result, Success

__all__: list[str] = ["loads"]


def loads(*, text: str) -> Result[Any, Exception]:
    """Parse a JSONC string and return `Success(parsed-value)`.

    Failure modes will be added as consumer pressure surfaces them
    (malformed JSON, unsupported constructs, etc.).
    """
    return Success(jsoncomment.loads(text))
