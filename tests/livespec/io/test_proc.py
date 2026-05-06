"""Tests for livespec.io.proc.

Per style doc §"Skill layout — `io/`": "io/ — impure
boundary. Every function wraps a side-effecting operation
(filesystem, subprocess, git) with @impure_safe." The proc
facade exposes the typed subprocess primitive that
`livespec.commands.seed.main` (and future sub-command wrappers)
compose against to invoke `bin/doctor_static.py` for the
post-step lifecycle phase per PROPOSAL.md §"Sub-command
lifecycle orchestration".

Subprocess invocation is the chosen composition mechanism (over
direct in-process import) because the layered-architecture
import-linter contract `livespec.commands | livespec.doctor`
treats `commands` and `doctor` as independent sibling layers
that cannot import each other. Subprocess invocation respects
that boundary while still letting `commands.<cmd>.main()` own
the deterministic lifecycle per style doc.
"""

from __future__ import annotations

import sys
from pathlib import Path

from livespec.errors import PreconditionError
from livespec.io import proc
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def test_proc_run_subprocess_returns_iosuccess_with_completed_process() -> None:
    """`run_subprocess(argv=...)` returns IOSuccess(CompletedProcess) on success.

    Smallest behavior: invoke `python -c "print('hello')"` (a
    deterministic zero-exit subprocess with stdout content) and
    assert the IOSuccess wrapper carries a CompletedProcess with
    returncode 0 and the captured stdout. Drives the proc facade
    into existence.

    The subprocess shape mirrors fs.read_text's IOSuccess(<value>)
    contract: the typed value carrier is the CompletedProcess
    itself (returncode + stdout + stderr), so callers can pattern-
    match the carrier and inspect any field they need.
    """
    result = proc.run_subprocess(argv=[sys.executable, "-c", "print('hello')"])
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(completed):
            assert completed.returncode == 0
            assert "hello" in completed.stdout
        case _:
            raise AssertionError(
                f"expected IOSuccess(CompletedProcess), got {result!r}",
            )


def test_proc_run_subprocess_captures_nonzero_exit_on_iosuccess_track() -> None:
    """`run_subprocess(argv=...)` for a non-zero-exit child returns IOSuccess.

    Per the canonical subprocess contract: a non-zero exit is NOT
    an exception in the parent — it's a normal CompletedProcess
    with returncode != 0. The proc facade therefore lifts non-zero
    exits onto the IOSuccess track (the SUBPROCESS RAN; the IO
    operation succeeded). The caller (e.g., seed.main) then
    pattern-matches `completed.returncode != 0` to fold doctor
    fail-status findings into a typed Failure on its own railway.

    The fs.read_text analogue: a missing file lifts to
    IOFailure(PreconditionError) because the OS-level call raises
    FileNotFoundError. A non-zero subprocess exit doesn't raise
    in the parent, so it lifts to IOSuccess(CompletedProcess).
    """
    result = proc.run_subprocess(argv=[sys.executable, "-c", "raise SystemExit(3)"])
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(completed):
            assert completed.returncode == 3
        case _:
            raise AssertionError(
                f"expected IOSuccess(CompletedProcess) with returncode 3, " f"got {result!r}",
            )


def test_proc_run_subprocess_returns_precondition_error_on_executable_not_found(
    *,
    tmp_path: Path,
) -> None:
    """`run_subprocess(argv=[<missing-executable>, ...])` -> IOFailure(PreconditionError).

    OSError (FileNotFoundError on the exec call when the executable
    does not exist on the filesystem) lifts to PreconditionError
    per the canonical mapping at the io boundary. Mirrors
    fs.read_text's missing-file failure-arm treatment.

    The fixture uses a `tmp_path`-derived path that's guaranteed
    non-existent rather than a hard-coded "no-such-binary" string,
    so the test stays hermetic across environments where some
    "binary" might happen to exist on PATH.
    """
    missing = tmp_path / "no-such-executable"
    result = proc.run_subprocess(argv=[str(missing)])
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            raise AssertionError(
                f"expected IOFailure(PreconditionError), got {result!r}",
            )
