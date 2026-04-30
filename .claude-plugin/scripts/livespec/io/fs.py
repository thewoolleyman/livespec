"""Filesystem boundary facade.

Per style doc §"Skill layout — `io/`": every filesystem
operation lives here under `@impure_safe` so the railway flows
through `IOResult`. Pure layers (`parse/`, `validate/`) cannot
import this module (enforced by import-linter's
`parse-and-validate-are-pure` contract).

Exception-to-LivespecError mapping is the io/ boundary's
responsibility (the only place LivespecError raise-sites are
permitted, per check-no-raise-outside-io). Callers in
`commands/` and `doctor/` pattern-match the typed Failure
payload to derive exit codes.
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult, impure_safe

from livespec.errors import LivespecError, PreconditionError

__all__: list[str] = ["read_text", "write_text"]


@impure_safe(exceptions=(OSError,))
def _raw_read_text(*, path: Path) -> str:
    """Decorator-lifted call into pathlib. Future cycles widen the
    OSError handling to include PermissionDeniedError mapping
    when seed.main hits an EACCES path.
    """
    return path.read_text(encoding="utf-8")


def read_text(*, path: Path) -> IOResult[str, LivespecError]:
    """Read a UTF-8 text file and return its contents on the IO track.

    FileNotFoundError lifts to PreconditionError (exit 3). Other
    OSError subclasses still surface generically until consumer
    pressure forces the typed mapping (PermissionError ->
    PermissionDeniedError, etc.).
    """
    return _raw_read_text(path=path).alt(
        lambda exc: PreconditionError(f"fs.read_text: {exc}"),
    )


@impure_safe(exceptions=(OSError,))
def _raw_write_text(*, path: Path, text: str) -> None:
    """Decorator-lifted call into pathlib's write_text.

    Parent directory creation is the consumer's responsibility
    (the seed file-shaping helpers create `history/v001/`
    explicitly via a separate stage). UTF-8 is the project-wide
    encoding contract.
    """
    _ = path.write_text(text, encoding="utf-8")


def write_text(*, path: Path, text: str) -> IOResult[None, LivespecError]:
    """Write a UTF-8 text file and return IOSuccess(None) on completion.

    Failure mapping is intentionally minimal at this cycle: any
    OSError lifts to PreconditionError. Future cycles widen this
    under consumer pressure (e.g., a parent-dir-missing path
    surfacing FileNotFoundError on the seed history-write stage).
    """
    return _raw_write_text(path=path, text=text).alt(
        lambda exc: PreconditionError(f"fs.write_text: {exc}"),
    )
