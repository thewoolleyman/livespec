"""Filesystem boundary facade.

Per style doc §"Skill layout — `io/`": every filesystem
operation lives here under `@impure_safe` so the railway flows
through `IOResult`. Pure layers (`parse/`, `validate/`) cannot
import this module (enforced by import-linter's
`parse-and-validate-are-pure` contract).

Cycle 71 lands the success path of `read_text` only;
`PreconditionError` (file-not-found) and `PermissionDeniedError`
(EACCES) mappings arrive in subsequent cycles when consumers
surface those failure modes.
"""

from __future__ import annotations

from pathlib import Path

from returns.io import impure_safe

__all__: list[str] = ["read_text"]


@impure_safe(exceptions=(OSError,))
def read_text(*, path: Path) -> str:
    """Read a UTF-8 text file and return its contents on the IO track.

    `@impure_safe(exceptions=(OSError,))` covers the open failure
    modes (FileNotFoundError, PermissionError, IsADirectoryError —
    all OSError subclasses) onto IOFailure. Future cycles map the
    raw OSError to a typed LivespecError (PreconditionError or
    PermissionDeniedError) when seed.main and other consumers
    pattern-match against the typed surface.
    """
    return path.read_text(encoding="utf-8")
