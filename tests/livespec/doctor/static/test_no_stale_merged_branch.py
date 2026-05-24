"""Tests for livespec.doctor.static.no_stale_merged_branch.

Per `SPECIFICATION/contracts.md` §"Impl-side cleanup invariants
(cross-boundary)" → §"`no-stale-merged-branch`": for every local
branch whose tip is reachable from the default branch, the
invariant fires `warn` with corrective action
`git branch -d <name>`. Excludes the default branch itself.

The check fires `warn` (v074) when stale-merged branches exist;
fires `pass` when only the default branch is in the merged set;
fires `skipped` when the project is not a git repo OR when
`origin/HEAD` is unset (default branch undetermined).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import no_stale_merged_branch
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def _git_init_with_user(*, cwd: Path, name: str, email: str) -> None:
    """Initialize a git repo at `cwd` with local user.name/user.email set."""
    _ = subprocess.run(["git", "init", "--quiet"], cwd=cwd, check=True)
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
    """Write `content` to `path` and commit it."""
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


def _git_set_origin_head(*, cwd: Path, default_branch: str) -> None:
    """Stage a fake `origin` remote + set `origin/HEAD` to point at `default_branch`."""
    _ = subprocess.run(
        ["git", "remote", "add", "origin", str(cwd)],
        cwd=cwd,
        check=True,
    )
    _ = subprocess.run(
        ["git", "update-ref", f"refs/remotes/origin/{default_branch}", "HEAD"],
        cwd=cwd,
        check=True,
    )
    _ = subprocess.run(
        [
            "git",
            "symbolic-ref",
            "refs/remotes/origin/HEAD",
            f"refs/remotes/origin/{default_branch}",
        ],
        cwd=cwd,
        check=True,
    )


def _current_branch(*, cwd: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def test_no_stale_merged_branch_passes_when_only_default_branch_present(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`pass` when the repo has only the default branch (nothing to clean up)."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    _git_commit_file(cwd=project_root, path=project_root / "seed.md", content=b"# Seed\n")
    default_branch = _current_branch(cwd=project_root)
    _git_set_origin_head(cwd=project_root, default_branch=default_branch)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_merged_branch.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-merged-branch",
        status="pass",
        message=(
            f"no-stale-merged-branch: no local branches merged into "
            f"`{default_branch}` (default branch itself excluded)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_no_stale_merged_branch_warns_when_merged_branch_remains(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`warn` when at least one local branch other than default is merged.

    The fixture creates `feature/done` at the same commit as the
    default branch, making it trivially merged. The doctor
    surfaces it with the `git branch -d` corrective action.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    _git_commit_file(cwd=project_root, path=project_root / "seed.md", content=b"# Seed\n")
    default_branch = _current_branch(cwd=project_root)
    _git_set_origin_head(cwd=project_root, default_branch=default_branch)
    _ = subprocess.run(
        ["git", "branch", "feature/done"],
        cwd=project_root,
        check=True,
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_merged_branch.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-merged-branch",
        status="warn",
        message=(
            f"no-stale-merged-branch: 1 local branch(es) merged into "
            f"`{default_branch}` and ready to delete: feature/done. "
            f"Corrective action: git branch -d feature/done"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_no_stale_merged_branch_skipped_when_not_a_git_repo(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`skipped` when `project_root` is not a git working tree."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    monkeypatch.chdir(project_root)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_merged_branch.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-merged-branch",
        status="skipped",
        message=(
            "no-stale-merged-branch: project_root is not a git " "working tree; check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_no_stale_merged_branch_skipped_when_origin_head_unset(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`skipped` when origin/HEAD is unset (default branch undetermined).

    Fresh git init with no remote configured; the symbolic-ref
    lookup fails and the lash branch surfaces a skipped finding
    with the precondition-not-met message.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    _git_commit_file(cwd=project_root, path=project_root / "seed.md", content=b"# Seed\n")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_merged_branch.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-merged-branch",
        status="skipped",
        message=(
            "no-stale-merged-branch: precondition not met " "(PreconditionError); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)
