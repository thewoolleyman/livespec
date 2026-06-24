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

import shutil
from pathlib import Path

from returns.io import IOResult, impure_safe

from livespec.errors import LivespecError, PreconditionError

__all__: list[str] = [
    "copy_file",
    "list_dir",
    "list_tree",
    "move",
    "read_text",
    "rmtree",
    "stat_mtime",
    "write_text",
]


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

    Parent directories are created on demand
    (`mkdir(parents=True, exist_ok=True)`) so the seed
    file-shaping stages can write to nested paths
    (e.g., `<project-root>/SPECIFICATION/spec.md`) without
    a separate mkdir stage. UTF-8 is the project-wide encoding
    contract.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
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


@impure_safe(exceptions=(OSError,))
def _raw_list_dir(*, path: Path) -> list[Path]:
    """Decorator-lifted call into pathlib's iterdir.

    Returns immediate children of `path` as a list; the order is
    deterministic-via-sort so callers don't need to re-sort.
    Missing or non-directory paths lift to PreconditionError via
    the public seam.
    """
    return sorted(path.iterdir())


def list_dir(*, path: Path) -> IOResult[list[Path], LivespecError]:
    """List immediate children of `path` as a sorted list of Paths.

    FileNotFoundError / NotADirectoryError lift to
    PreconditionError (exit 3). Used by revise to enumerate the
    existing `<spec-target>/history/v*/` directories so the next
    `vNNN` can be computed.
    """
    return _raw_list_dir(path=path).alt(
        lambda exc: PreconditionError(f"fs.list_dir: {exc}"),
    )


@impure_safe(exceptions=(OSError,))
def _raw_list_tree(*, root: Path, exclude_top_level: frozenset[str]) -> list[Path]:
    """Decorator-lifted recursive walk under `root`.

    Returns every regular file reachable from `root`, EXCEPT any
    file whose path descends through an immediate child directory
    of `root` whose name is in `exclude_top_level`. The returned
    paths are sorted for deterministic ordering so callers don't
    need to re-sort. Symlinks are followed only as `rglob` follows
    them (it does not recurse into symlinked directories).

    `Path.rglob` silently yields nothing for a missing or
    non-directory `root`; an explicit guard raises so the public
    seam maps the precondition failure to PreconditionError,
    matching `list_dir`'s missing-path contract.
    """
    if not root.is_dir():
        raise FileNotFoundError(f"list_tree: root is not a directory: {root}")
    out: list[Path] = []
    for candidate in sorted(root.rglob("*")):
        if not candidate.is_file():
            continue
        first_segment = candidate.relative_to(root).parts[0]
        if first_segment in exclude_top_level:
            continue
        out.append(candidate)
    return out


def list_tree(
    *,
    root: Path,
    exclude_top_level: frozenset[str],
) -> IOResult[list[Path], LivespecError]:
    """Recursively list every file under `root`, sorted, on the IO track.

    Files reached through an immediate-child directory of `root`
    named in `exclude_top_level` are omitted (the directory itself
    and its whole subtree). FileNotFoundError / NotADirectoryError
    lift to PreconditionError (exit 3). Used by revise to snapshot
    the whole working spec tree into `history/vNNN/` while excluding
    the `history/`, `proposed_changes/`, and `templates/` sibling
    subdirectories.
    """
    return _raw_list_tree(root=root, exclude_top_level=exclude_top_level).alt(
        lambda exc: PreconditionError(f"fs.list_tree: {exc}"),
    )


@impure_safe(exceptions=(OSError,))
def _raw_move(*, source: Path, target: Path) -> None:
    """Decorator-lifted byte-identical move via pathlib.Path.rename.

    Parent directories of the target are created on demand
    (`mkdir(parents=True, exist_ok=True)`) so the revise stage
    can move into a freshly-cut `history/vNNN/proposed_changes/`
    without a separate mkdir stage. Path.rename preserves the
    file content byte-for-byte (atomic on the same filesystem).
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    _ = source.rename(target)


def move(*, source: Path, target: Path) -> IOResult[None, LivespecError]:
    """Move `source` to `target` byte-identically; return IOSuccess(None).

     OSError (source missing, cross-device move, permission denied)
     lifts to PreconditionError (exit 3). Used by revise to move
     each processed `<spec-target>/proposed_changes/<stem>.md`
     into `<spec-target>/history/vNNN/proposed_changes/<stem>.md`
    .
    """
    return _raw_move(source=source, target=target).alt(
        lambda exc: PreconditionError(f"fs.move: {exc}"),
    )


@impure_safe(exceptions=(OSError,))
def _raw_copy_file(*, source: Path, target: Path) -> None:
    """Decorator-lifted byte-identical copy via shutil.copyfile.

    Parent directories of the target are created on demand so the
    revise snapshot stage can copy into nested
    `history/vNNN/<subdir>/` paths without a separate mkdir stage.
    `shutil.copyfile` is binary-safe (no text decode), which opaque
    committed assets (e.g. an alternate tool's image output) require.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    _ = shutil.copyfile(source, target)


def copy_file(*, source: Path, target: Path) -> IOResult[None, LivespecError]:
    """Copy `source` to `target` byte-identically; return IOSuccess(None).

    OSError (source missing, permission denied) lifts to
    PreconditionError (exit 3). Consumer: the whole-tree history
    snapshot, which copies subdirectory spec files (including
    opaque committed binary assets) byte-for-byte into
    `history/vNNN/`.
    """
    return _raw_copy_file(source=source, target=target).alt(
        lambda exc: PreconditionError(f"fs.copy_file: {exc}"),
    )


@impure_safe(exceptions=(OSError,))
def _raw_stat_mtime(*, path: Path) -> float:
    """Decorator-lifted call into pathlib's stat for the mtime field."""
    return path.stat().st_mtime


def stat_mtime(*, path: Path) -> IOResult[float, LivespecError]:
    """Read `path`'s modification time (epoch seconds) on the IO track.

    FileNotFoundError lifts to PreconditionError (exit 3) per the
    canonical mapping at the io boundary. A generic stat facade
    method retained for mtime-based comparisons.
    """
    return _raw_stat_mtime(path=path).alt(
        lambda exc: PreconditionError(f"fs.stat_mtime: {exc}"),
    )


@impure_safe(exceptions=(OSError,))
def _raw_rmtree(*, path: Path) -> None:
    """Decorator-lifted recursive-delete via shutil.rmtree.

    `shutil.rmtree` removes `path` and all of its contents. Missing
    or non-directory `path` lifts to OSError → PreconditionError via
    the public seam.
    """
    shutil.rmtree(path)


def rmtree(*, path: Path) -> IOResult[None, LivespecError]:
    """Recursively remove `path` and all contents; return IOSuccess(None).

    Per SPECIFICATION/spec.md §"Sub-command lifecycle"
    prune-history paragraph step (c): the wrapper deletes every
    `<spec-root>/history/vK/` where K < N-1. OSError
    (FileNotFoundError on a missing path, permission denied)
    lifts to PreconditionError (exit 3) per the canonical mapping
    at the io boundary.
    """
    return _raw_rmtree(path=path).alt(
        lambda exc: PreconditionError(f"fs.rmtree: {exc}"),
    )
