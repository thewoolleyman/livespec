"""Tests for livespec.io.gh.

Per style doc §"Skill layout — `io/`": every operation that
touches the gh CLI binary lives at this seam under @impure_safe so
the railway flows through IOResult. The gh facade exposes three
merged-PR/branch introspection operations:
get_repo_name_with_owner, list_remote_branches,
list_merged_pull_request_head_refs.

Tests monkeypatch `livespec.io.gh.run_subprocess` to a fake that
returns canned CompletedProcess carriers; the real gh CLI binary
is never invoked. This pattern mirrors how io/git tests would
mock proc when network or external state is required (the git
facade tests happen to use real local git operations because git
runs entirely against the tmp_path repo, but gh requires a
remote GitHub repo + auth which is impractical in tests).
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
from livespec.errors import PreconditionError
from livespec.io import gh
from returns.io import IOResult
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def _completed(*, stdout: str, returncode: int = 0) -> subprocess.CompletedProcess[str]:
    """Build a fake CompletedProcess carrier for monkeypatched run_subprocess."""
    return subprocess.CompletedProcess(
        args=["fake"],
        returncode=returncode,
        stdout=stdout,
        stderr="",
    )


def _install_fake(
    *,
    monkeypatch: pytest.MonkeyPatch,
    factory: Any,
) -> None:
    """Replace `livespec.io.gh.run_subprocess` with a closure that returns IOSuccess(<fake>).

    `factory` is a callable taking `(argv, cwd)` and returning a
    CompletedProcess to lift onto the IOSuccess track. The test
    inspects argv to discriminate which gh subcommand was invoked
    and returns the appropriate canned response.
    """

    def fake_run_subprocess(
        *,
        argv: list[str],
        cwd: Path | None = None,
    ) -> IOResult[subprocess.CompletedProcess[str], PreconditionError]:
        return IOResult.from_value(factory(argv, cwd))

    monkeypatch.setattr(gh, "run_subprocess", fake_run_subprocess)


def test_get_repo_name_with_owner_returns_iosuccess_on_zero_exit(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """`gh repo view --json nameWithOwner` returns the owner/name string."""
    _install_fake(
        monkeypatch=monkeypatch,
        factory=lambda _argv, _cwd: _completed(stdout="thewoolleyman/livespec\n"),
    )
    result = gh.get_repo_name_with_owner(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(value):
            assert value == "thewoolleyman/livespec"
        case _:
            raise AssertionError(f"expected IOSuccess(<str>), got {result!r}")


def test_get_repo_name_with_owner_returns_iofailure_on_nonzero_exit(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """`gh repo view` non-zero exit lifts to IOFailure(PreconditionError)."""
    _install_fake(
        monkeypatch=monkeypatch,
        factory=lambda _argv, _cwd: _completed(stdout="", returncode=1),
    )
    result = gh.get_repo_name_with_owner(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            raise AssertionError(
                f"expected IOFailure(PreconditionError), got {result!r}",
            )


def test_get_repo_name_with_owner_returns_iofailure_on_empty_stdout(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Empty stdout after zero exit lifts to IOFailure(PreconditionError)."""
    _install_fake(
        monkeypatch=monkeypatch,
        factory=lambda _argv, _cwd: _completed(stdout="   \n", returncode=0),
    )
    result = gh.get_repo_name_with_owner(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            raise AssertionError(
                f"expected IOFailure(PreconditionError), got {result!r}",
            )


def test_list_remote_branches_parses_one_branch_per_line(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """`gh api repos/{owner}/{repo}/branches --jq .[].name` returns parsed names."""
    _install_fake(
        monkeypatch=monkeypatch,
        factory=lambda _argv, _cwd: _completed(
            stdout="master\nfeature/done\nfeature/wip\n",
        ),
    )
    result = gh.list_remote_branches(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(value):
            assert value == ("master", "feature/done", "feature/wip")
        case _:
            raise AssertionError(f"expected IOSuccess(<tuple>), got {result!r}")


def test_list_remote_branches_returns_empty_tuple_on_zero_branches(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An empty branches result still surfaces on the IOSuccess track."""
    _install_fake(
        monkeypatch=monkeypatch,
        factory=lambda _argv, _cwd: _completed(stdout=""),
    )
    result = gh.list_remote_branches(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(value):
            assert value == ()
        case _:
            raise AssertionError(f"expected IOSuccess(()), got {result!r}")


def test_list_remote_branches_returns_iofailure_on_nonzero_exit(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """`gh api repos/branches` non-zero exit lifts to IOFailure(PreconditionError)."""
    _install_fake(
        monkeypatch=monkeypatch,
        factory=lambda _argv, _cwd: _completed(stdout="", returncode=1),
    )
    result = gh.list_remote_branches(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            raise AssertionError(
                f"expected IOFailure(PreconditionError), got {result!r}",
            )


def test_list_merged_pull_request_head_refs_parses_head_ref_names(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """`gh pr list --state merged --jq .[].headRefName` returns parsed head refs."""
    _install_fake(
        monkeypatch=monkeypatch,
        factory=lambda _argv, _cwd: _completed(
            stdout="feature/done\nfeature/old\n",
        ),
    )
    result = gh.list_merged_pull_request_head_refs(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(value):
            assert value == ("feature/done", "feature/old")
        case _:
            raise AssertionError(f"expected IOSuccess(<tuple>), got {result!r}")


def test_list_merged_pull_request_head_refs_returns_iofailure_on_nonzero_exit(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """`gh pr list` non-zero exit lifts to IOFailure(PreconditionError)."""
    _install_fake(
        monkeypatch=monkeypatch,
        factory=lambda _argv, _cwd: _completed(stdout="", returncode=1),
    )
    result = gh.list_merged_pull_request_head_refs(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            raise AssertionError(
                f"expected IOFailure(PreconditionError), got {result!r}",
            )


def test_gh_facade_passes_project_root_as_cwd(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Every gh facade call threads `cwd=project_root` to run_subprocess.

    gh lacks a `-C` flag; it resolves the local origin remote
    from cwd. This test inspects the cwd argument the facade
    threads through and verifies it is exactly `project_root` for
    each of the three operations.
    """
    observed: list[Path | None] = []

    def fake_run_subprocess(
        *,
        argv: list[str],
        cwd: Path | None = None,
    ) -> IOResult[subprocess.CompletedProcess[str], PreconditionError]:
        _ = argv
        observed.append(cwd)
        return IOResult.from_value(_completed(stdout="x\n"))

    monkeypatch.setattr(gh, "run_subprocess", fake_run_subprocess)
    _ = gh.get_repo_name_with_owner(project_root=tmp_path)
    _ = gh.list_remote_branches(project_root=tmp_path)
    _ = gh.list_merged_pull_request_head_refs(project_root=tmp_path)
    assert observed == [tmp_path, tmp_path, tmp_path]
