"""Tests for livespec.io.fs.

Per style doc §"Skill layout — `io/`": every operation that
touches the filesystem lives here under `@impure_safe`. The fs
facade exposes the typed read/write primitives the seed +
propose-change + revise + doctor sub-commands compose against.
"""

from __future__ import annotations

from pathlib import Path

from livespec.errors import PreconditionError
from livespec.io import fs
from returns.io import IOSuccess
from returns.result import Failure
from returns.unsafe import unsafe_perform_io

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


def test_fs_write_text_writes_utf8_content_and_returns_iosuccess(
    *,
    tmp_path: Path,
) -> None:
    """`write_text(path, text)` writes the content to disk and returns IOSuccess(None).

    Smallest behavior: write a UTF-8 text payload to a fresh
    `tmp_path` location, assert the file contents on disk match
    the input verbatim, and assert the railway carrier is the
    IOSuccess(None) shape every seed file-shaping stage composes
    against. PROPOSAL.md §"`seed`" steps 1-3 (write
    `.livespec.jsonc`, main-spec files, sub-spec files) all bind
    against this primitive.
    """
    target = tmp_path / "out.txt"
    payload = "hello, livespec\n"
    result = fs.write_text(path=target, text=payload)
    assert result == IOSuccess(None)
    assert target.read_text(encoding="utf-8") == payload


def test_fs_list_dir_returns_iosuccess_with_sorted_children(*, tmp_path: Path) -> None:
    """`list_dir(path)` returns IOSuccess([...]) with sorted Path children.

    Per the cycle-127 consumer-pressure pull from revise: revise
    needs to enumerate `<spec-target>/history/v*/` directories
    to compute the next `vNNN`. The facade returns a sorted list
    so callers don't need to re-sort.
    """
    (tmp_path / "v002").mkdir()
    (tmp_path / "v001").mkdir()
    (tmp_path / "v003").mkdir()
    result = fs.list_dir(path=tmp_path)
    assert result == IOSuccess(
        [tmp_path / "v001", tmp_path / "v002", tmp_path / "v003"],
    )


def test_fs_list_dir_returns_precondition_error_on_missing_path(
    *,
    tmp_path: Path,
) -> None:
    """`list_dir(path=missing)` returns IOFailure(PreconditionError(...)).

    FileNotFoundError -> PreconditionError per the canonical
    mapping at the io boundary; mirrors read_text's failure-arm
    treatment.
    """
    missing = tmp_path / "does-not-exist"
    result = fs.list_dir(path=missing)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            raise AssertionError(
                f"expected IOFailure(PreconditionError), got {result!r}",
            )


def test_fs_move_renames_byte_identically_and_returns_iosuccess(
    *,
    tmp_path: Path,
) -> None:
    """`move(source, target)` renames the file byte-identically.

    Per cycle-128 consumer pressure from revise: each processed
    proposed-change file must move byte-identically into
    `<spec-target>/history/vNNN/proposed_changes/`. The facade
    creates parent directories on demand.
    """
    source = tmp_path / "src.md"
    target = tmp_path / "subdir" / "dst.md"
    payload = "## Proposal: demo\nContent.\n"
    _ = source.write_text(payload, encoding="utf-8")
    result = fs.move(source=source, target=target)
    assert result == IOSuccess(None)
    assert not source.exists()
    assert target.exists()
    assert target.read_text(encoding="utf-8") == payload


def test_fs_move_returns_precondition_error_on_missing_source(
    *,
    tmp_path: Path,
) -> None:
    """`move(source=missing, ...)` returns IOFailure(PreconditionError(...)).

    OSError (FileNotFoundError on the rename call) -> PreconditionError
    per the canonical mapping at the io boundary.
    """
    missing = tmp_path / "no-such-file.md"
    target = tmp_path / "target.md"
    result = fs.move(source=missing, target=target)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            raise AssertionError(
                f"expected IOFailure(PreconditionError), got {result!r}",
            )


def test_fs_rmtree_removes_populated_directory_and_returns_iosuccess(
    *,
    tmp_path: Path,
) -> None:
    """`rmtree(path)` recursively deletes `path` and returns IOSuccess(None).

    Per cycle 6.c.6 consumer pressure from prune-history: per
    v012 SPECIFICATION/spec.md §"Sub-command lifecycle"
    prune-history paragraph step (c), the wrapper deletes every
    `<spec-root>/history/vK/` where K < N-1. The fixture sets up
    a populated v-style directory tree (nested files +
    subdirectories) and asserts the directory is gone after
    rmtree returns. Mirrors the byte-identical-move primitive
    `fs.move`'s success-arm shape.
    """
    target = tmp_path / "v001"
    target.mkdir()
    nested = target / "proposed_changes"
    nested.mkdir()
    _ = (target / "spec.md").write_text("# spec\n", encoding="utf-8")
    _ = (nested / "demo.md").write_text("## demo\n", encoding="utf-8")
    result = fs.rmtree(path=target)
    assert result == IOSuccess(None)
    assert not target.exists()


def test_fs_rmtree_returns_precondition_error_on_missing_path(
    *,
    tmp_path: Path,
) -> None:
    """`rmtree(path=missing)` returns IOFailure(PreconditionError(...)).

    FileNotFoundError -> PreconditionError per the canonical
    mapping at the io boundary; mirrors `read_text` /
    `list_dir` / `move`'s failure-arm treatment.
    """
    missing = tmp_path / "no-such-dir"
    result = fs.rmtree(path=missing)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            raise AssertionError(
                f"expected IOFailure(PreconditionError), got {result!r}",
            )
