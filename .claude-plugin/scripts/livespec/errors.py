"""LivespecError hierarchy.

Holds ONLY expected-failure (domain error) classes per the Error Handling
Discipline. Bugs (unrecoverable programming errors) are NOT LivespecError
subclasses; they propagate as raised exceptions to the outermost
supervisor's bug-catcher and result in exit 1.

Each subclass carries a per-class `exit_code: ClassVar[int]` matching the
exit-code contract in python-skill-script-style-requirements.md
§"Exit code contract". `IOFailure(err)` payloads in the railway are
LivespecError subclasses; supervisors pattern-match on the final
IOResult and exit `err.exit_code`.

`HelpRequested` is intentionally NOT a LivespecError subclass: a -h /
--help request is an informational early-exit category, not a domain
error and not a bug.
"""
from typing import ClassVar

__all__: list[str] = [
    "GitUnavailableError",
    "HelpRequested",
    "LivespecError",
    "PermissionDeniedError",
    "PreconditionError",
    "ToolMissingError",
    "UsageError",
    "ValidationError",
]


class LivespecError(Exception):
    """Base class for expected-failure (domain error) classes.

    A LivespecError represents a domain-meaningful failure that a retry,
    corrected input, or environment fix could resolve. It is ROP-track
    failure-payload material. Bugs (unrecoverable programming errors)
    are NOT LivespecError subclasses; they propagate as raised
    exceptions to the outermost supervisor's bug-catcher.
    """

    exit_code: ClassVar[int] = 1


class UsageError(LivespecError):
    """Bad flag, wrong argument count, or malformed invocation."""

    exit_code: ClassVar[int] = 2


class PreconditionError(LivespecError):
    """Input or precondition failed: referenced file/path/value missing,
    malformed, or in an incompatible state."""

    exit_code: ClassVar[int] = 3


class ValidationError(LivespecError):
    """Schema validation failure on LLM-provided JSON payload.

    Retryable: the sub-command's SKILL.md prose SHOULD inspect exit
    code 4, treat it as a malformed-payload signal, and SHOULD
    re-invoke the template prompt with error context. v1 does not
    specify an exact retry count. Exit code 4 (distinct from
    PreconditionError's exit 3) lets the LLM deterministically
    classify retryable vs non-retryable exit-3-class failures without
    parsing stderr.
    """

    exit_code: ClassVar[int] = 4


class GitUnavailableError(LivespecError):
    """Git is not available, or the working tree is not a git repository."""

    exit_code: ClassVar[int] = 3


class PermissionDeniedError(LivespecError):
    """A required file exists but is not executable/readable/writable."""

    exit_code: ClassVar[int] = 126


class ToolMissingError(LivespecError):
    """Required external tool not on PATH, or Python version too old."""

    exit_code: ClassVar[int] = 127


class HelpRequested(Exception):  # noqa: N818 — intentionally not an error; informational early-exit per style doc
    """User requested help (`-h` or `--help`); NOT a LivespecError.

    A HelpRequested is an informational early-exit category: not a
    domain error (no retry / fix improves it) and not a bug (user
    asked for help). Does not subclass LivespecError. The supervisor
    pattern-matches HelpRequested via keyword destructure and returns
    exit 0 after emitting the help text to stdout.
    """

    exit_code: ClassVar[int] = 0

    def __init__(self, *, text: str) -> None:
        super().__init__(text)
        self.text = text
