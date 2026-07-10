"""Tests for livespec.io.streams."""

from __future__ import annotations

import sys

import pytest
from livespec.io import streams

__all__: list[str] = []


def test_write_stdout_writes_text_to_stdout(
    *,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """write_stdout emits the exact supplied text to stdout."""
    streams.write_stdout(text="payload\n")
    captured = capsys.readouterr()
    assert captured.out == "payload\n"
    assert captured.err == ""


def test_write_stderr_writes_text_to_stderr(
    *,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """write_stderr emits the exact supplied text to stderr."""
    streams.write_stderr(text="warning\n")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "warning\n"


def test_stream_helpers_return_written_character_count(
    *,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The helpers expose the underlying stream's written character count."""
    stdout_count = streams.write_stdout(text="abc")
    stderr_count = streams.write_stderr(text="de")
    _ = capsys.readouterr()
    assert stdout_count == 3
    assert stderr_count == 2


def test_stream_helpers_do_not_replace_standard_streams() -> None:
    """The helpers write through the existing sys streams."""
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    _ = streams.write_stdout(text="")
    _ = streams.write_stderr(text="")
    assert sys.stdout is original_stdout
    assert sys.stderr is original_stderr
