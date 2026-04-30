"""LivespecError hierarchy for domain (expected-failure) errors.

Per python-skill-script-style-requirements.md §"Exit code contract"
+ §"Raising": every domain error is a one-level subclass of
`LivespecError` carrying an `exit_code` ClassVar. Bugs propagate
as raised exceptions to the supervisor's bug-catcher, NOT as
`LivespecError` subclasses.

The hierarchy widens as consumer pressure surfaces new failure
categories (the briefing's outside-in walking direction). Cycle
63 lands `LivespecError` + `ValidationError` driven by
`livespec/parse/jsonc.py`'s malformed-input failure mode.
"""

from __future__ import annotations

from typing import ClassVar

__all__: list[str] = ["LivespecError", "UsageError", "ValidationError"]


class LivespecError(Exception):
    """Open base class for expected-failure (domain) errors.

    Direct subclassing is permitted by `check-no-inheritance`'s
    allowlist (which enumerates `{Exception, BaseException,
    LivespecError, Protocol, NamedTuple, TypedDict}`). The
    hierarchy is intentionally one level deep: subclassing
    `ValidationError` etc. is forbidden.
    """

    exit_code: ClassVar[int] = 1


class UsageError(LivespecError):
    """CLI-usage error from argparse (bad flag, wrong arg count).

    Per the style doc §"Exit code contract": exit `2`. Distinct
    from PreconditionError (exit 3) because usage errors signal
    "the user invoked the wrapper wrong" rather than "the
    project state precondition failed."
    """

    exit_code: ClassVar[int] = 2


class ValidationError(LivespecError):
    """Schema or wire-format validation failure on inbound payload.

    Per the style doc §"Exit code contract": exit `4`. Retryable
    by the calling SKILL.md prose (re-invoke the template prompt
    with error context).
    """

    exit_code: ClassVar[int] = 4
