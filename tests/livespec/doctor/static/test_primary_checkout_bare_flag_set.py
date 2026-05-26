"""Tests for livespec.doctor.static.primary_checkout_bare_flag_set.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary
invariants" → §"`primary-checkout-bare-flag-set`": every
livespec-governed primary checkout MUST have `core.bare = true`
set in its `.git/config`. The check fires `fail` when the value
is absent OR explicitly set to `false`; the invariant MUST NOT
distinguish between the two cases.

The check applies to the PRIMARY checkout only. Secondary
worktrees carry a `.git` file pointing back to the primary; the
check reads `core.bare` via `git config --get core.bare`, which
resolves to the common config (the primary's `.git/config`) by
git's design (`core.bare` is not in the worktree-config-allowed
key set).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import primary_checkout_bare_flag_set
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


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
    surrounding repo. Scrubbing the vars confines git to the
    tmp_path fixture's `.git` directory.
    """
    for var in _GIT_ENV_PASSTHROUGH_VARS:
        monkeypatch.delenv(var, raising=False)


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


def _git_set_core_bare(*, cwd: Path, value: str) -> None:
    """Set `core.bare = <value>` on the repo at `cwd`."""
    _ = subprocess.run(
        ["git", "config", "--local", "core.bare", value],
        cwd=cwd,
        check=True,
    )


def _git_unset_core_bare(*, cwd: Path) -> None:
    """Unset `core.bare` on the repo at `cwd` (idempotent)."""
    _ = subprocess.run(
        ["git", "config", "--local", "--unset", "core.bare"],
        cwd=cwd,
        check=False,
    )


def _pass_message() -> str:
    return (
        "primary-checkout-bare-flag-set: `core.bare = true` is set on "
        "the primary checkout's `.git/config`"
    )


def _fail_message() -> str:
    return (
        "primary-checkout-bare-flag-set: `core.bare` is absent or `false` "
        "on the primary checkout's `.git/config`. Corrective action: run "
        "the documented bootstrap step (see "
        '`non-functional-requirements.md` §"Bare-flag bootstrap '
        'procedure"), which idempotently invokes `git config core.bare '
        "true` against the primary checkout."
    )


def test_primary_checkout_bare_flag_set_passes_when_flag_is_true(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """(a) `pass` when `core.bare = true` is set on the primary checkout."""
    _scrub_git_env(monkeypatch=monkeypatch)
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    _git_commit_file(cwd=project_root, path=project_root / "seed.md", content=b"# Seed\n")
    _git_set_core_bare(cwd=project_root, value="true")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = primary_checkout_bare_flag_set.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-primary-checkout-bare-flag-set",
        status="pass",
        message=_pass_message(),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_primary_checkout_bare_flag_set_fails_when_flag_absent(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """(b) `fail` when `core.bare` is absent from the primary checkout's config."""
    _scrub_git_env(monkeypatch=monkeypatch)
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    _git_commit_file(cwd=project_root, path=project_root / "seed.md", content=b"# Seed\n")
    _git_unset_core_bare(cwd=project_root)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = primary_checkout_bare_flag_set.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-primary-checkout-bare-flag-set",
        status="fail",
        message=_fail_message(),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_primary_checkout_bare_flag_set_fails_when_flag_explicitly_false(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """(c) `fail` when `core.bare = false` is set (same as absent per contract)."""
    _scrub_git_env(monkeypatch=monkeypatch)
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    _git_commit_file(cwd=project_root, path=project_root / "seed.md", content=b"# Seed\n")
    _git_set_core_bare(cwd=project_root, value="false")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = primary_checkout_bare_flag_set.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-primary-checkout-bare-flag-set",
        status="fail",
        message=_fail_message(),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_primary_checkout_bare_flag_set_passes_with_secondary_worktrees(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """(d) `pass` when primary has `core.bare = true` and secondary worktrees exist.

    The invariant reads only the primary `.git/config`; secondary
    worktrees carry a standalone `.git` FILE pointing back to the
    primary and are not inspected. This test creates a primary
    with `core.bare = true` plus a secondary worktree and confirms
    the check still passes.
    """
    _scrub_git_env(monkeypatch=monkeypatch)
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    _git_commit_file(cwd=project_root, path=project_root / "seed.md", content=b"# Seed\n")
    _ = subprocess.run(
        ["git", "branch", "feature/wip"],
        cwd=project_root,
        check=True,
    )
    wt_path = tmp_path / "wt-feature"
    _ = subprocess.run(
        ["git", "worktree", "add", str(wt_path), "feature/wip"],
        cwd=project_root,
        check=True,
    )
    _git_set_core_bare(cwd=project_root, value="true")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = primary_checkout_bare_flag_set.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-primary-checkout-bare-flag-set",
        status="pass",
        message=_pass_message(),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_primary_checkout_bare_flag_set_skipped_when_not_a_git_repo(
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
    result = primary_checkout_bare_flag_set.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-primary-checkout-bare-flag-set",
        status="skipped",
        message=(
            "primary-checkout-bare-flag-set: project_root is not a git "
            "working tree; check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)
