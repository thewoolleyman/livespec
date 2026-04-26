"""Filesystem operations (`@impure_safe`).

Each public function is a thin wrapper over a single side-effecting
filesystem operation, decorated with `@impure_safe(exceptions=(...))`
from dry-python/returns. `@impure_safe` catches the enumerated
exception types raised inside the function body and converts them
to `IOFailure(exc)`; anything outside the list propagates as a
raised exception (bug → supervisor's bug-catcher → exit 1).

LivespecError subclasses are RAISED here in `io/` (raise-site
restricted to `io/**` per `check-no-raise-outside-io`). Pure layers
compose these `IOResult` values via `.bind` / `.lash` without
raising. Mapping low-level filesystem exceptions to LivespecError
subclasses is inline: each function catches the OS-level exception
(FileNotFoundError, PermissionError, etc.) and re-raises a
LivespecError subclass with the path embedded. `@impure_safe` then
catches the LivespecError and ships it on the failure track.

`*` as the first parameter on every public def enforces keyword-only
argument passing (`check-keyword-only-args`). All paths are
`pathlib.Path`; text I/O is UTF-8.

`find_upward` is the shared upward-walk helper per v017 Q9: every
wrapper except `bin/seed.py` reuses it to locate `.livespec.jsonc`
from `--project-root`. `livespec.doctor.run_static` also uses it
for the same purpose.
"""
from pathlib import Path

from returns.io import impure_safe

from livespec.errors import (
    PermissionDeniedError,
    PreconditionError,
)

__all__: list[str] = [
    "find_upward",
    "list_dir",
    "mkdir_p",
    "path_exists",
    "read_text",
    "remove_file",
    "write_text",
]


@impure_safe(exceptions=(PermissionDeniedError, PreconditionError))
def read_text(*, path: Path) -> str:
    """Read `path` as UTF-8 text.

    Maps FileNotFoundError → PreconditionError (exit 3),
    PermissionError → PermissionDeniedError (exit 126),
    IsADirectoryError → PreconditionError (exit 3). Any other
    OSError propagates as a bug.
    """
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise PreconditionError(f"file not found: {path}") from e
    except PermissionError as e:
        raise PermissionDeniedError(f"permission denied reading: {path}") from e
    except IsADirectoryError as e:
        raise PreconditionError(f"path is a directory, not a file: {path}") from e


@impure_safe(exceptions=(PermissionDeniedError, PreconditionError))
def write_text(*, path: Path, content: str) -> None:
    """Write `content` to `path` as UTF-8 text.

    The parent directory MUST exist. Maps PermissionError →
    PermissionDeniedError (exit 126), FileNotFoundError on missing
    parent → PreconditionError (exit 3), IsADirectoryError →
    PreconditionError (exit 3).
    """
    try:
        path.write_text(content, encoding="utf-8")
    except PermissionError as e:
        raise PermissionDeniedError(f"permission denied writing: {path}") from e
    except FileNotFoundError as e:
        raise PreconditionError(
            f"parent directory missing: {path.parent}",
        ) from e
    except IsADirectoryError as e:
        raise PreconditionError(f"path is a directory, not a file: {path}") from e


@impure_safe(exceptions=(PermissionDeniedError,))
def path_exists(*, path: Path) -> bool:
    """Return True iff `path` refers to an existing file or directory.

    `Path.exists()` follows symlinks; broken symlinks return False.
    PermissionError on an intermediate directory is mapped to
    PermissionDeniedError (exit 126).
    """
    try:
        return path.exists()
    except PermissionError as e:
        raise PermissionDeniedError(f"permission denied checking: {path}") from e


@impure_safe(exceptions=(PermissionDeniedError, PreconditionError))
def mkdir_p(*, path: Path) -> None:
    """Create `path` and any missing parents (idempotent).

    Equivalent to `path.mkdir(parents=True, exist_ok=True)`.
    Existing-as-directory is fine; existing-as-file raises
    PreconditionError.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise PermissionDeniedError(f"permission denied creating: {path}") from e
    except FileExistsError as e:
        raise PreconditionError(
            f"path exists as a file, not a directory: {path}",
        ) from e


@impure_safe(exceptions=(PermissionDeniedError, PreconditionError))
def list_dir(*, path: Path) -> list[Path]:
    """List entries in `path` as a sorted list of `Path` objects.

    Maps FileNotFoundError / NotADirectoryError → PreconditionError
    (exit 3), PermissionError → PermissionDeniedError (exit 126).
    """
    try:
        return sorted(path.iterdir())
    except FileNotFoundError as e:
        raise PreconditionError(f"directory not found: {path}") from e
    except NotADirectoryError as e:
        raise PreconditionError(f"path is not a directory: {path}") from e
    except PermissionError as e:
        raise PermissionDeniedError(f"permission denied listing: {path}") from e


@impure_safe(exceptions=(PermissionDeniedError, PreconditionError))
def remove_file(*, path: Path) -> None:
    """Remove the file at `path`.

    Maps FileNotFoundError → PreconditionError (exit 3),
    PermissionError → PermissionDeniedError (exit 126),
    IsADirectoryError → PreconditionError (exit 3). Use
    `mkdir_p` for directory removal (none in v1).
    """
    try:
        path.unlink()
    except FileNotFoundError as e:
        raise PreconditionError(f"file not found: {path}") from e
    except IsADirectoryError as e:
        raise PreconditionError(f"path is a directory, not a file: {path}") from e
    except PermissionError as e:
        raise PermissionDeniedError(f"permission denied removing: {path}") from e


@impure_safe(exceptions=(PermissionDeniedError, PreconditionError))
def find_upward(*, start: Path, name: str) -> Path:
    """Walk upward from `start.resolve()` until a sibling named
    `name` is found. Returns the first match.

    The walk stops at the filesystem root (where `parent == self`).
    Raises PreconditionError if `name` is not found in any ancestor.
    Used by every wrapper except `bin/seed.py` to locate
    `.livespec.jsonc` from `--project-root` (v017 Q9), and by
    `livespec.doctor.run_static` for the same purpose.
    """
    try:
        current = start.resolve()
    except (OSError, RuntimeError) as e:
        raise PreconditionError(f"cannot resolve start path: {start}") from e
    while current != current.parent:
        candidate = current / name
        try:
            if candidate.exists():
                return candidate
        except PermissionError as e:
            raise PermissionDeniedError(
                f"permission denied checking: {candidate}",
            ) from e
        current = current.parent
    raise PreconditionError(f"{name} not found in any ancestor of {start}")
