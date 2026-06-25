"""LivespecError hierarchy for domain (expected-failure) errors.

Per python-skill-script-style-requirements.md: every domain error is a one-level subclass of
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

__all__: list[str] = [
    "HelpRequestedError",
    "LivespecError",
    "PreconditionError",
    "UsageError",
    "ValidationError",
]


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

    Per the style doc: exit `2`. Distinct from PreconditionError (exit 3)
    because usage errors signal "the user invoked the wrapper wrong"
    rather than "the project state precondition failed."
    """

    exit_code: ClassVar[int] = 2


class HelpRequestedError(LivespecError):
    """Argparse help request.

    `argparse` implements `-h` / `--help` by printing help text
    and raising `SystemExit(0)`. The CLI facade keeps that path
    on the railway so supervisors can short-circuit with exit 0
    without treating help as a usage failure.
    """

    exit_code: ClassVar[int] = 0


class PreconditionError(LivespecError):
    """Project-state precondition not met (file missing, malformed
    config, idempotency conflict, etc.).

    Per the style doc: exit `3`. Distinct from UsageError because the
    user invoked the wrapper correctly but the on-disk state isn't
    ready for the operation.
    """

    exit_code: ClassVar[int] = 3


class ValidationError(LivespecError):
    """Schema or wire-format validation failure on inbound payload.

    Per the style doc: exit `4`. Retryable by the calling SKILL.md
    prose (re-invoke the template prompt with error context).
    """

    exit_code: ClassVar[int] = 4
