"""Tests for livespec.io.fs.

Per style doc §"Skill layout — `io/`": every operation that
touches the filesystem lives here under `@impure_safe`. The fs
facade exposes the typed read/write primitives the seed +
propose-change + revise + doctor sub-commands compose against.
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOSuccess
from returns.result import Failure
from returns.unsafe import unsafe_perform_io

from livespec.errors import PreconditionError
from livespec.io import fs

__all__: list[str] = []


def test_fs_read_text_returns_iosuccess_with_file_contents(*, tmp_path: Path) -> None:
    """`read_text(path=existing)` returns IOSuccess(<content-string>).

    Smallest behavior: read an existing UTF-8 text file from
    `tmp_path` and assert the IOSuccess wrapper carries the
    exact content. Failure-track behavior (FileNotFoundError ->
    PreconditionError, PermissionError -> PermissionDeniedError)
    is driven by future cycles under consumer pressure.
    """
    payload = '{"template": "livespec"}'
    path = tmp_path / "payload.json"
    _ = path.write_text(payload, encoding="utf-8")
    result = fs.read_text(path=path)
    assert result == IOSuccess(payload)


def test_fs_read_text_returns_precondition_error_on_missing_file(*, tmp_path: Path) -> None:
    """`read_text(path=missing)` returns IOFailure(PreconditionError(...)).

    PreconditionError signals "the project state required for
    this operation is not met" (exit 3 per style doc §"Exit
    code contract"). FileNotFoundError -> PreconditionError is
    the canonical mapping at the io boundary.
    """
    missing = tmp_path / "does-not-exist.json"
    result = fs.read_text(path=missing)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            raise AssertionError(f"expected IOFailure(PreconditionError), got {result!r}")
