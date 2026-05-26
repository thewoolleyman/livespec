"""Retry policy for cross-repo subprocess queries.

Per livespec/SPECIFICATION/contracts.md v072 §"Cross-repo dependency
awareness" → "Retry policy": 3 attempts with 1s / 2s / 4s exponential
backoff. After every attempt fails the caller surfaces
`RefStatus.UNKNOWN` rather than raising; this module returns `None`
on exhaustion and lets the caller translate.

The policy is intentionally NOT user-configurable in v1. Projects
with bandwidth-constrained CI environments are expected to pre-fetch
sibling repos to local clones (configured via the `local_clone` field
in `cross_repo_targets`) to avoid the GitHub-query path entirely.

`time.sleep` is called directly so tests can monkeypatch it to a no-op
or a list-append spy and verify the backoff sequence without burning
real wall-clock seconds.
"""

import time
from collections.abc import Callable
from typing import TypeVar

__all__: list[str] = ["retry_with_backoff"]

T = TypeVar("T")

_ATTEMPTS = 3
_BACKOFFS_SECONDS: tuple[float, ...] = (1.0, 2.0, 4.0)


def retry_with_backoff(*, fn: Callable[[], T]) -> T | None:
    """Run `fn` with the documented retry policy.

    Returns `fn()`'s value on first success; returns `None` after all
    `_ATTEMPTS` attempts raise. Callers translate the `None` return
    into `RefStatus.UNKNOWN` at the resolve-ref boundary; this module
    deliberately doesn't import the status enum to keep the seam
    minimal (retry layer is reusable across non-resolve callers).

    Exceptions raised by `fn` are caught broadly: the retry layer does
    not differentiate between transient transport errors and bugs. A
    bug-shaped exception will burn all 3 attempts and surface as
    `None` — the resolve-ref walker MUST translate `None` to
    `RefStatus.UNKNOWN` (never an assert) so the live system degrades
    gracefully on impl-side errors.
    """
    for attempt_index in range(_ATTEMPTS):
        try:
            return fn()
        except Exception:
            if attempt_index < _ATTEMPTS - 1:
                time.sleep(_BACKOFFS_SECONDS[attempt_index])
    return None
