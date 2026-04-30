"""Tests for livespec.io.fs.

Per style doc §"Skill layout — `io/`": every operation that
touches the filesystem lives here under `@impure_safe`. The fs
facade exposes the typed read/write primitives the seed +
propose-change + revise + doctor sub-commands compose against.
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOSuccess

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
