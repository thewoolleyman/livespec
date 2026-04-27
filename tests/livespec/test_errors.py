"""Tests for livespec.errors.

The LivespecError hierarchy is a flat one-level structure (v013 M5):
every domain error subclasses LivespecError directly. Each subclass
carries a per-class `exit_code: ClassVar[int]` matching the
exit-code contract in `python-skill-script-style-requirements.md`.
"""

from __future__ import annotations

import pytest

from livespec.errors import (
    GitUnavailableError,
    HelpRequested,
    LivespecError,
    PermissionDeniedError,
    PreconditionError,
    ToolMissingError,
    UsageError,
    ValidationError,
)

__all__: list[str] = []


_EXIT_CODE_USAGE = 2
_EXIT_CODE_PRECONDITION = 3
_EXIT_CODE_VALIDATION = 4
_EXIT_CODE_GIT_UNAVAILABLE = 3
_EXIT_CODE_PERMISSION_DENIED = 126
_EXIT_CODE_TOOL_MISSING = 127
_EXIT_CODE_HELP_REQUESTED = 0
_EXIT_CODE_DEFAULT = 1


def test_livespec_error_default_exit_code() -> None:
    assert LivespecError.exit_code == _EXIT_CODE_DEFAULT


def test_usage_error_exit_code() -> None:
    assert UsageError.exit_code == _EXIT_CODE_USAGE


def test_precondition_error_exit_code() -> None:
    assert PreconditionError.exit_code == _EXIT_CODE_PRECONDITION


def test_validation_error_exit_code() -> None:
    assert ValidationError.exit_code == _EXIT_CODE_VALIDATION


def test_git_unavailable_error_exit_code() -> None:
    assert GitUnavailableError.exit_code == _EXIT_CODE_GIT_UNAVAILABLE


def test_permission_denied_error_exit_code() -> None:
    assert PermissionDeniedError.exit_code == _EXIT_CODE_PERMISSION_DENIED


def test_tool_missing_error_exit_code() -> None:
    assert ToolMissingError.exit_code == _EXIT_CODE_TOOL_MISSING


def test_help_requested_exit_code() -> None:
    assert HelpRequested.exit_code == _EXIT_CODE_HELP_REQUESTED


def test_help_requested_carries_text() -> None:
    """HelpRequested binds the help text via kw-only `text=...`."""
    err = HelpRequested(text="usage: livespec seed --help")
    assert err.text == "usage: livespec seed --help"
    assert "usage" in str(err)


def test_help_requested_does_not_subclass_livespec_error() -> None:
    """HelpRequested is informational, NOT a domain error."""
    assert not issubclass(HelpRequested, LivespecError)


def test_all_domain_errors_subclass_livespec_error_directly() -> None:
    """v013 M5 flat-hierarchy invariant: each domain error has LivespecError as direct parent."""
    domain_errors = [
        UsageError,
        PreconditionError,
        ValidationError,
        GitUnavailableError,
        PermissionDeniedError,
        ToolMissingError,
    ]
    for cls in domain_errors:
        assert cls.__bases__ == (LivespecError,), (
            f"{cls.__name__} must subclass LivespecError directly; got {cls.__bases__}"
        )


def test_livespec_error_can_be_raised_and_caught() -> None:
    with pytest.raises(LivespecError):
        raise LivespecError("test")


def test_subclass_caught_by_base() -> None:
    """Subclasses propagate as LivespecError to satisfy the railway carrier shape."""
    with pytest.raises(LivespecError):
        raise PreconditionError("missing file")
