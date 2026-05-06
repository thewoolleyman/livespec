"""Tests for livespec.io.git.

Per style doc §"Skill layout — `io/`": io/ is the
impure boundary; every operation that touches the git working
tree lives here under `@impure_safe` so the railway flows
through `IOResult`. The git facade exposes the typed primitive
that `livespec.commands.revise.main` (and `seed.main`'s revision-
auto-capture path) compose against to populate the
revision-file `author_human` field and `revision_front_matter.schema.json`.

The seam is named `io.git.get_git_user` per PROPOSAL.md + `revision_front_matter.schema.json` description on
the `author_human` property. Cycle 5.c.1 lands the smallest
viable surface: a single `get_git_user` primitive that returns
`"Name <email>"` from local git config when both values are
set; later cycles (or consumer pressure) widen the unset/missing-
git fallbacks under a fully-typed Failure carrier.

Phase 7 sub-step 7.a.i adds two more git primitives:
`is_git_repo(*, project_root)` returns IOSuccess(True/False)
without lifting the non-repo case to IOFailure (non-repo is an
expected business outcome for the doctor's out-of-band-edits
check), and `show_at_head(*, project_root, repo_relative_path)`
returns the raw bytes of a path at HEAD so the doctor can
byte-compare against the working tree without a decode step
that could corrupt non-ASCII content.

Phase 7 sub-step 7.a.iv (redo) adds `list_at_head(*,
project_root, repo_relative_dir)` returning the immediate file
basenames at HEAD under a given repo-relative directory. The
out-of-band-edits divergence detection composes this primitive
with `show_at_head` to compare HEAD-active spec content against
HEAD-history-vN snapshot content. Empty subtree and
missing-subtree cases both return IOSuccess(()) — the underlying
`git ls-tree HEAD <dir>/` does not distinguish them — and the
no-HEAD-yet case lifts to IOFailure.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from livespec.io import git as io_git
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def _git_init_with_user(*, cwd: Path, name: str, email: str) -> None:
    """Initialize a git repo at `cwd` and set local user.name + user.email.

    Uses `--local` so the test never writes to the developer's
    global git config. Mirrors the fixture shape in
    `tests/dev-tooling/checks/test_commit_pairs_source_and_test.py`'s
    `_git` helper.
    """
    _ = subprocess.run(
        ["git", "init", "--quiet"],
        cwd=cwd,
        check=True,
    )
    _ = subprocess.run(
        ["git", "config", "--local", "user.name", name],
        cwd=cwd,
        check=True,
    )
    _ = subprocess.run(
        ["git", "config", "--local", "user.email", email],
        cwd=cwd,
        check=True,
    )


def _git_commit_file(*, cwd: Path, path: Path, content: bytes) -> None:
    """Write `content` to `path` and commit it via `git add` + `git commit`.

    Used by `show_at_head` tests to land a known byte sequence at
    HEAD so the round-trip assertion can compare bytes-in-file vs
    bytes-from-git-show without a decode step.
    """
    _ = path.write_bytes(content)
    _ = subprocess.run(
        ["git", "add", str(path.relative_to(cwd))],
        cwd=cwd,
        check=True,
    )
    _ = subprocess.run(
        ["git", "commit", "--quiet", "-m", "fixture commit"],
        cwd=cwd,
        check=True,
    )


def test_get_git_user_returns_combined_name_and_email(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`get_git_user()` returns IOSuccess('Name <email>') when both values set.

    Smallest viable behavior: a fresh `git init` repo in
    `tmp_path` with local `user.name` and `user.email` set,
    monkeypatch cwd to that repo, call `get_git_user()`, assert
    the IOSuccess carrier holds the conventional Git author
    format `"Name <email>"`. Drives the `livespec/io/git.py`
    module into existence (importing it fails at HEAD).

    Per the cwd-fallback isolation rule, monkeypatch.chdir is
    required to scope the git-config read to the test fixture
    repo and not the developer's surrounding repo.
    """
    _git_init_with_user(
        cwd=tmp_path,
        name="Test User",
        email="test@example.com",
    )
    monkeypatch.chdir(tmp_path)

    result = io_git.get_git_user()
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(value):
            assert value == "Test User <test@example.com>"
        case _:
            raise AssertionError(
                f"expected IOSuccess('Test User <test@example.com>'), got {result!r}",
            )


def test_is_git_repo_returns_true_inside_repo(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`is_git_repo(project_root=tmp_path)` returns IOSuccess(True).

    Phase 7 sub-step 7.a.i: the doctor's out-of-band-edits
    static check needs a typed primitive that distinguishes
    "this project is in a git working tree" from
    "this project is NOT in a git working tree" (a freshly
    extracted tarball, a non-versioned dir). A real
    `git init`-ed `tmp_path` exercises the `IOSuccess(True)`
    path. Per the cwd-fallback isolation rule, monkeypatch.chdir
    is held even though `is_git_repo` operates on the explicit
    `project_root` (defense-in-depth: if the impl ever falls
    back to cwd, the test still doesn't leak into the
    developer's repo).
    """
    _git_init_with_user(
        cwd=tmp_path,
        name="Test User",
        email="test@example.com",
    )
    monkeypatch.chdir(tmp_path)

    result = io_git.is_git_repo(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(value):
            assert value is True
        case _:
            raise AssertionError(f"expected IOSuccess(True), got {result!r}")


def test_is_git_repo_returns_false_outside_repo(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`is_git_repo` returns IOSuccess(False) when project_root is not a repo.

    A bare `tmp_path` with no `git init` is the negative case.
    `git rev-parse --is-inside-work-tree` exits non-zero with
    `fatal: not a git repository`; this is NOT an IOFailure —
    non-repo is an expected business outcome the doctor folds
    into its own railway as "skip the out-of-band check, the
    project isn't versioned." The IOFailure track is reserved
    for genuinely unexpected errors (e.g., the `git` binary
    itself missing).
    """
    monkeypatch.chdir(tmp_path)

    result = io_git.is_git_repo(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(value):
            assert value is False
        case _:
            raise AssertionError(f"expected IOSuccess(False), got {result!r}")


def test_show_at_head_returns_committed_bytes(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`show_at_head` returns the raw bytes of a path at HEAD.

    Smallest viable behavior: a file committed at HEAD with
    plain ASCII content round-trips exactly. The fixture uses
    `_git_commit_file` to land a known byte sequence at HEAD,
    then asserts `show_at_head` returns the same bytes.
    """
    _git_init_with_user(
        cwd=tmp_path,
        name="Test User",
        email="test@example.com",
    )
    monkeypatch.chdir(tmp_path)
    spec_path = tmp_path / "SPECIFICATION" / "spec.md"
    _ = spec_path.parent.mkdir(parents=True, exist_ok=True)
    expected = b"# Spec\n\nHello world.\n"
    _git_commit_file(cwd=tmp_path, path=spec_path, content=expected)

    result = io_git.show_at_head(
        project_root=tmp_path,
        repo_relative_path=Path("SPECIFICATION/spec.md"),
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(value):
            assert value == expected
        case _:
            raise AssertionError(f"expected IOSuccess(<bytes>), got {result!r}")


def test_show_at_head_preserves_non_ascii_bytes(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`show_at_head` returns bytes byte-identically (no text decode).

    The doctor's out-of-band-edits check byte-compares the
    HEAD blob against the working-tree blob; a text-mode
    decode would corrupt embedded NULs and bytes outside
    UTF-8. This test pins the binary contract: write a file
    containing a NUL plus the high byte 0xFF, commit it, and
    assert `show_at_head` returns the exact same byte sequence
    (NOT a UnicodeDecodeError, NOT replacement characters,
    NOT a normalized form).
    """
    _git_init_with_user(
        cwd=tmp_path,
        name="Test User",
        email="test@example.com",
    )
    monkeypatch.chdir(tmp_path)
    binary_path = tmp_path / "blob.bin"
    expected = b"hello\x00world\xff"
    _git_commit_file(cwd=tmp_path, path=binary_path, content=expected)

    result = io_git.show_at_head(
        project_root=tmp_path,
        repo_relative_path=Path("blob.bin"),
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(value):
            assert value == expected
        case _:
            raise AssertionError(f"expected IOSuccess(<bytes>), got {result!r}")


def test_show_at_head_returns_failure_when_path_missing_at_head(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`show_at_head` returns IOFailure when the path is not at HEAD.

    A repo with one commit landing `committed.md`; calling
    `show_at_head` for `missing.md` (never added/committed)
    must surface IOFailure(LivespecError) rather than empty
    bytes — the doctor's "compare HEAD vs working tree" needs
    to distinguish "exists at HEAD but differs" from
    "does not exist at HEAD at all".
    """
    _git_init_with_user(
        cwd=tmp_path,
        name="Test User",
        email="test@example.com",
    )
    monkeypatch.chdir(tmp_path)
    committed = tmp_path / "committed.md"
    _git_commit_file(cwd=tmp_path, path=committed, content=b"present at head\n")

    result = io_git.show_at_head(
        project_root=tmp_path,
        repo_relative_path=Path("missing.md"),
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(_):
            return
        case _:
            raise AssertionError(f"expected IOFailure, got {result!r}")


def test_show_at_head_returns_failure_when_no_head(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`show_at_head` returns IOFailure when the repo has no commits yet.

    A freshly `git init`-ed repo with zero commits has no HEAD
    ref. `git show HEAD:path` exits non-zero with
    `fatal: ambiguous argument 'HEAD'`. The doctor folds this
    into "no prior baseline" via the IOFailure track.
    """
    _git_init_with_user(
        cwd=tmp_path,
        name="Test User",
        email="test@example.com",
    )
    monkeypatch.chdir(tmp_path)

    result = io_git.show_at_head(
        project_root=tmp_path,
        repo_relative_path=Path("anything.md"),
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(_):
            return
        case _:
            raise AssertionError(f"expected IOFailure, got {result!r}")


def test_list_at_head_returns_immediate_file_children(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`list_at_head` returns the immediate file basenames at HEAD under a directory.

    Phase 7 sub-step 7.a.iv (redo): the doctor's
    out-of-band-edits static check needs a typed primitive
    that enumerates files at HEAD under a given directory so
    the active-vs-history-vN comparison can iterate over the
    HEAD-committed spec files without a working-tree walk.
    The fixture commits two immediate file children under
    `SPECIFICATION/` plus a subdirectory's file; the assertion
    pins `list_at_head` returning only the two immediate file
    basenames, NOT the subdir name and NOT the file inside
    the subdir.
    """
    _git_init_with_user(
        cwd=tmp_path,
        name="Test User",
        email="test@example.com",
    )
    monkeypatch.chdir(tmp_path)
    spec_root = tmp_path / "SPECIFICATION"
    spec_root.mkdir()
    _git_commit_file(
        cwd=tmp_path,
        path=spec_root / "alpha.md",
        content=b"# Alpha\n",
    )
    _git_commit_file(
        cwd=tmp_path,
        path=spec_root / "beta.md",
        content=b"# Beta\n",
    )
    history_v001 = spec_root / "history" / "v001"
    history_v001.mkdir(parents=True)
    _git_commit_file(
        cwd=tmp_path,
        path=history_v001 / "snapshot.md",
        content=b"# Snapshot\n",
    )

    result = io_git.list_at_head(
        project_root=tmp_path,
        repo_relative_dir=Path("SPECIFICATION"),
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(value):
            assert sorted(value) == ["alpha.md", "beta.md"]
        case _:
            raise AssertionError(f"expected IOSuccess(<names>), got {result!r}")


def test_list_at_head_returns_empty_tuple_when_dir_has_no_immediate_files(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`list_at_head` returns an empty tuple when `repo_relative_dir` has only subdirs at HEAD.

    A directory under HEAD whose only children are
    subdirectories MUST yield an empty tuple — the
    enumeration is a "files only" question, and a "no
    immediate files" answer is a genuinely empty answer
    rather than an IOFailure (the dir IS at HEAD; it just
    contains no enumerable spec files).
    """
    _git_init_with_user(
        cwd=tmp_path,
        name="Test User",
        email="test@example.com",
    )
    monkeypatch.chdir(tmp_path)
    spec_root = tmp_path / "SPECIFICATION"
    spec_root.mkdir()
    history_v001 = spec_root / "history" / "v001"
    history_v001.mkdir(parents=True)
    _git_commit_file(
        cwd=tmp_path,
        path=history_v001 / "snapshot.md",
        content=b"# Snapshot\n",
    )

    result = io_git.list_at_head(
        project_root=tmp_path,
        repo_relative_dir=Path("SPECIFICATION"),
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(value):
            assert value == ()
        case _:
            raise AssertionError(f"expected IOSuccess(()), got {result!r}")


def test_list_at_head_returns_empty_tuple_when_dir_missing_at_head(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`list_at_head` returns IOSuccess(()) when `repo_relative_dir` is not at HEAD.

    A repo with one commit landing `committed.md`; calling
    `list_at_head` for `nonexistent/` (a directory never added
    to any commit) returns IOSuccess with an empty tuple — the
    underlying `git ls-tree HEAD <dir>/` exits 0 with empty
    stdout when the dir-path is unknown to HEAD (it does NOT
    distinguish "empty subtree" from "subtree missing"). The
    doctor folds either zero-result outcome into "no files at
    HEAD under spec_root" so the comparison is a no-op when
    the spec_root has no HEAD baseline. The no-HEAD-at-all
    case (zero commits) is the genuinely-failing branch
    covered by the next test.
    """
    _git_init_with_user(
        cwd=tmp_path,
        name="Test User",
        email="test@example.com",
    )
    monkeypatch.chdir(tmp_path)
    committed = tmp_path / "committed.md"
    _git_commit_file(cwd=tmp_path, path=committed, content=b"present at head\n")

    result = io_git.list_at_head(
        project_root=tmp_path,
        repo_relative_dir=Path("nonexistent"),
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(value):
            assert value == ()
        case _:
            raise AssertionError(f"expected IOSuccess(()), got {result!r}")


def test_list_at_head_returns_failure_when_no_head(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`list_at_head` returns IOFailure when the repo has no commits yet.

    A freshly `git init`-ed repo with zero commits has no
    HEAD ref; `git ls-tree HEAD <dir>/` exits non-zero. The
    doctor folds this into "no prior baseline" — a project
    with no HEAD has no files at HEAD and so no comparison
    target exists.
    """
    _git_init_with_user(
        cwd=tmp_path,
        name="Test User",
        email="test@example.com",
    )
    monkeypatch.chdir(tmp_path)

    result = io_git.list_at_head(
        project_root=tmp_path,
        repo_relative_dir=Path("SPECIFICATION"),
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(_):
            return
        case _:
            raise AssertionError(f"expected IOFailure, got {result!r}")
