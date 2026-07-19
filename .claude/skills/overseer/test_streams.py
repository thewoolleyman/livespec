"""Beside-tests for streams.py — the overseer's process-output sinks.

Run: ``uv run pytest .claude/skills/overseer/ -q`` (these beside-tests are NOT
in the product ``tests/`` tree). ``import streams`` resolves via conftest.py.
"""

import io
import sys

import pytest
import streams


def test_write_stdout_writes_verbatim_to_stdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)

    streams.write_stdout(text="hello\n")

    assert buffer.getvalue() == "hello\n"


def test_write_stderr_writes_verbatim_to_stderr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stderr", buffer)

    streams.write_stderr(text="boom\n")

    assert buffer.getvalue() == "boom\n"


def test_the_sinks_do_not_cross_streams(monkeypatch: pytest.MonkeyPatch) -> None:
    """A stdout write must not reach stderr, nor the reverse."""
    out, err = io.StringIO(), io.StringIO()
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)

    streams.write_stdout(text="to-out")
    streams.write_stderr(text="to-err")

    assert out.getvalue() == "to-out"
    assert err.getvalue() == "to-err"


def test_no_newline_is_appended(monkeypatch: pytest.MonkeyPatch) -> None:
    """The caller owns line termination, so two writes concatenate."""
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)

    streams.write_stdout(text="a")
    streams.write_stdout(text="b")

    assert buffer.getvalue() == "ab"


def test_the_sinks_resolve_sys_streams_at_call_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Late binding is what makes the sinks substitutable.

    Holding a module-import-time reference to ``sys.stdout`` would defeat every
    caller that redirects output, including this suite.
    """
    first, second = io.StringIO(), io.StringIO()
    monkeypatch.setattr(sys, "stdout", first)
    streams.write_stdout(text="first")
    monkeypatch.setattr(sys, "stdout", second)
    streams.write_stdout(text="second")

    assert first.getvalue() == "first"
    assert second.getvalue() == "second"
