"""Typed re-exports of `dry-python/returns` primitives.

Per style doc lines 1026-1033, the returns library's types
(`Result`, `IOResult`) are used pervasively throughout the
codebase, not only at boundaries; the facade pattern does not
apply uniformly. The returns-pyright-plugin-disposition was
settled in v025 D1: NO pyright plugin is vendored. The seven
strict-plus diagnostics manually enabled in `[tool.pyright]` are
the load-bearing guardrails against silent `Result` / `IOResult`
discards (`reportUnusedCallResult` in particular).

This facade provides a unified single-import surface for the
primitives livespec uses pervasively. Importing from
`livespec.io.returns_facade` is OPTIONAL — `from returns.io
import impure_safe` and `from returns.result import Result,
Success, Failure` work equivalently. The facade exists so that
if Phase 5+ pyright strict-mode surfaces specific typing gaps
that would benefit from `cast`-narrowed re-exports, those wrappers
can land here without touching call-sites that already import
through the facade.

Per Phase 3 minimum-viable scope, this is plain re-exports —
no `cast`, no wrappers. Phase 5 widens if needed.
"""

from returns.io import (
    IOFailure,
    IOResult,
    IOResultE,
    IOSuccess,
    impure_safe,
)
from returns.result import (
    Failure,
    Result,
    ResultE,
    Success,
    safe,
)

__all__: list[str] = [
    "Failure",
    "IOFailure",
    "IOResult",
    "IOResultE",
    "IOSuccess",
    "Result",
    "ResultE",
    "Success",
    "impure_safe",
    "safe",
]
