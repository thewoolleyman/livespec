"""Retry policy for cross-repo subprocess queries.

Per livespec/SPECIFICATION/contracts.md v072: 3 attempts with 1s / 2s /
4s exponential backoff. After every attempt fails the caller surfaces
`RefStatus.UNKNOWN` rather than raising; this module returns a
`RetryExhausted` on the failure track and lets the caller translate.

⚠️ IT USED TO RETURN `T | None`, WHICH IS THE SHAPE THIS SEAM EXISTS TO
REMOVE. `None` meant "all attempts failed" and carried NOTHING about
which call failed or why — so a resolution that degraded to `UNKNOWN`
could not say what it had failed to reach. `RetryExhausted` carries the
last failure's own description, and the translation the caller performs
is unchanged.

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
from dataclasses import dataclass
from typing import TypeVar

from returns.io import IOFailure, IOResult, IOSuccess
from returns.unsafe import unsafe_perform_io

__all__: list[str] = ["RetryExhausted", "retry_with_backoff"]

T = TypeVar("T")
E = TypeVar("E")

_ATTEMPTS = 3
_BACKOFFS_SECONDS: tuple[float, ...] = (1.0, 2.0, 4.0)


@dataclass(frozen=True, slots=True, kw_only=True)
class RetryExhausted:
    """Every attempt failed, and this is what the LAST one said.

    Normalised rather than generic in the caller's own failure type, so
    this module stays reusable across non-resolve callers and does not
    have to name any domain's error vocabulary — the same reason it
    deliberately does not import `RefStatus`.
    """

    attempts: int
    detail: str


def retry_with_backoff(*, fn: Callable[[], IOResult[T, E]]) -> IOResult[T, RetryExhausted]:
    """Run `fn` with the documented retry policy.

    Returns `fn()`'s value on the first attempt that lands on the
    SUCCESS track; returns `RetryExhausted` on the failure track after
    all `_ATTEMPTS` attempts fail. Callers translate that failure into
    `RefStatus.UNKNOWN` at the resolve-ref boundary; this module
    deliberately doesn't import the status enum to keep the seam
    minimal.

    ⚠️ BOTH FAILURE CHANNELS ARE RETRIED, AND THE BROAD CATCH IS KEPT ON
    PURPOSE. `fn` landing on the failure track is the ordinary transport
    case now that the `gh` provider is on the railway. But `fn` RAISING
    is still caught, because the retry layer does not differentiate
    between transient transport errors and bugs: a bug-shaped exception
    burns all 3 attempts and surfaces as a failure the resolve-ref
    walker translates to `RefStatus.UNKNOWN` (never an assert), so the
    live system degrades gracefully on impl-side errors. Dropping that
    catch would turn an impl bug into a crash in every consumer's
    dispatcher, which is a behaviour change this conversion does not
    make.
    """
    detail = "no attempt was made"
    for attempt_index in range(_ATTEMPTS):
        try:
            outcome = fn()
        except Exception as raised:  # Breadth is the POLICY here — see the docstring.
            detail = f"{type(raised).__name__}: {raised}"
        else:
            if not isinstance(outcome, IOFailure):
                # Re-lifted rather than returned as-is: `fn`'s failure type is
                # the CALLER's, and this function normalises every failure to
                # `RetryExhausted`, so the two `IOResult`s are not the same type
                # even though the success branch carries the same value.
                return IOSuccess(unsafe_perform_io(outcome.unwrap()))
            detail = str(unsafe_perform_io(outcome.failure()))
        if attempt_index < _ATTEMPTS - 1:
            time.sleep(_BACKOFFS_SECONDS[attempt_index])
    return IOFailure(RetryExhausted(attempts=_ATTEMPTS, detail=detail))
