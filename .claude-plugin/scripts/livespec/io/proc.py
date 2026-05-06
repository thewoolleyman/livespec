"""Subprocess boundary facade.

Per style doc §"Skill layout — `io/`": every operation
that touches the subprocess boundary lives here under
`@impure_safe` so the railway flows through `IOResult`.
Mirrors the shape of `livespec.io.fs` (every operation is a thin
wrapper over one side-effecting call; OSError lifts to
PreconditionError).

Cycle 144 lands the smallest viable surface: a single
`run_subprocess` primitive that captures stdout/stderr and
yields the `subprocess.CompletedProcess` carrier on the
IOSuccess track. Future cycles widen this under consumer
pressure (e.g., environment overrides, cwd, timeout) when
seed.main and the other lifecycle composers need them.

Why subprocess: the layered-architecture import-linter contract
`livespec.commands | livespec.doctor` treats `commands` and
`doctor` as independent sibling layers that cannot import each
other. Subprocess invocation respects that boundary while still
letting `commands.<cmd>.main()` own the deterministic lifecycle
per style doc.
"""

from __future__ import annotations

import subprocess  # subprocess is the documented io/ surface (style doc)

from returns.io import IOResult, impure_safe

from livespec.errors import LivespecError, PreconditionError

__all__: list[str] = ["run_subprocess"]


@impure_safe(exceptions=(OSError,))
def _raw_run_subprocess(*, argv: list[str]) -> subprocess.CompletedProcess[str]:
    """Decorator-lifted call into subprocess.run with stdout/stderr capture.

    Captures stdout + stderr as text (UTF-8 implied via `text=True`)
    so callers (e.g., seed.main parsing doctor's `{"findings":
    [...]}` JSON payload from stdout) can read the captured
    streams off the CompletedProcess carrier without an extra
    decode step. `check=False` keeps non-zero exits on the
    IOSuccess track — the SUBPROCESS RAN; the IO operation
    succeeded; the caller folds returncode into its own railway.
    """
    # S603: argv is a fixed list provided by the caller (no shell
    # expansion); the only public consumer is seed.main composing
    # a repo-controlled wrapper path + literal flags + tmp_path-
    # derived inputs. No untrusted shell input.
    return subprocess.run(  # noqa: S603
        argv,
        capture_output=True,
        text=True,
        check=False,
    )


def run_subprocess(
    *,
    argv: list[str],
) -> IOResult[subprocess.CompletedProcess[str], LivespecError]:
    """Run a subprocess and return its CompletedProcess on the IO track.

    Failure mapping is intentionally minimal at this cycle: any
    OSError (notably FileNotFoundError when the executable is
    absent) lifts to PreconditionError. Future cycles widen this
    under consumer pressure (e.g., PermissionError ->
    PermissionDeniedError when an executable exists but is not
    executable; TimeoutExpired when a timeout argument is added).

    Non-zero exit codes from the child are NOT failures at this
    boundary — they lift to IOSuccess(CompletedProcess) so the
    caller can pattern-match `completed.returncode` and fold the
    semantics into its own railway. Per the sub-command lifecycle
    semantics in SPECIFICATION/spec.md, any `status: "fail"`
    finding from post-step doctor aborts the wrapper with exit 3,
    but the doctor subprocess itself ran correctly — the failure
    is on the wrapper's own railway, not the io boundary.
    """
    return _raw_run_subprocess(argv=argv).alt(
        lambda exc: PreconditionError(f"proc.run_subprocess: {exc}"),
    )
