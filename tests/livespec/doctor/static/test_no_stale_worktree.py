"""Tests for livespec.doctor.static.no_stale_worktree.

Per `SPECIFICATION/contracts.md` §"Impl-side cleanup invariants
(cross-boundary)" → §"`no-stale-worktree`": for every git
worktree whose underlying branch is merged into default, the
invariant fires `warn` with corrective action `git worktree
remove <path>`. Excludes the primary worktree.

v1 implementation surfaces case (a) (merged-into-default) only;
case (b) (remote absence) is deferred to the gh-CLI integration
of no-stale-merged-pr-branch.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import no_stale_worktree
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


_GIT_ENV_PASSTHROUGH_VARS: tuple[str, ...] = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
    "GIT_LITERAL_PATHSPECS",
    "GIT_PREFIX",
)


def _scrub_git_env(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove inherited GIT_* env vars so test git operations isolate cleanly.

    When tests run as part of a git pre-commit hook (lefthook),
    git sets GIT_DIR/GIT_WORK_TREE/GIT_INDEX_FILE pointing at the
    surrounding repo. `git worktree add` (the only git command
    these tests exercise that's sensitive to this leakage) then
    fails with `fatal: .git/index: index file open failed: Not a
    directory`. Scrubbing the vars confines git to the tmp_path
    fixture's `.git` directory.
    """
    for var in _GIT_ENV_PASSTHROUGH_VARS:
        monkeypatch.delenv(var, raising=False)


def test_no_stale_worktree_passes_when_only_primary_worktree(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`pass` when the repo has only the primary worktree."""
    _scrub_git_env(monkeypatch=monkeypatch)
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
    result = no_stale_worktree.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-worktree",
        status="pass",
        message=(
            f"no-stale-worktree: no secondary worktrees on branches merged "
            f"into `{default_branch}` (1 worktree(s) scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_no_stale_worktree_warns_when_secondary_on_merged_branch(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`warn` when a secondary worktree is on a branch merged into default."""
    _scrub_git_env(monkeypatch=monkeypatch)
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
    wt_path = tmp_path / "wt-feature"
    _ = subprocess.run(
        ["git", "worktree", "add", str(wt_path), "feature/done"],
        cwd=project_root,
        check=True,
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_worktree.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-worktree",
        status="warn",
        message=(
            f"no-stale-worktree: 1 secondary worktree(s) on branches merged "
            f"into `{default_branch}` and ready to clean up: {wt_path}. "
            f"Corrective action: git worktree remove {wt_path}"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_no_stale_worktree_skipped_when_not_a_git_repo(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`skipped` when `project_root` is not a git working tree."""
    _scrub_git_env(monkeypatch=monkeypatch)
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    monkeypatch.chdir(project_root)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_worktree.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-worktree",
        status="skipped",
        message=("no-stale-worktree: project_root is not a git working tree; check skipped"),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_no_stale_worktree_skipped_when_origin_head_unset(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`skipped` when origin/HEAD is unset (default branch undetermined)."""
    _scrub_git_env(monkeypatch=monkeypatch)
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    _git_commit_file(cwd=project_root, path=project_root / "seed.md", content=b"# Seed\n")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_worktree.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-worktree",
        status="skipped",
        message=("no-stale-worktree: precondition not met (PreconditionError); check skipped"),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)
