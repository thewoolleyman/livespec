"""Tests for livespec.doctor.static.no_stale_merged_pr_branch.

Per `SPECIFICATION/contracts.md` §"Impl-side cleanup invariants
(cross-boundary)" → §"`no-stale-merged-pr-branch`": for every
GitHub branch in `gh api repos/<owner>/<name>/branches` fronted by
a merged PR, the invariant fires `warn` with corrective action
`gh api -X DELETE repos/<owner>/<name>/git/refs/heads/<name>`.

The check fires `pass` when no remote branches have merged PRs
fronting them; `warn` when stale branches exist; `skipped` when
the project is not a git repo OR `origin/HEAD` is unset OR any
gh CLI call fails (auth, network, repo-not-on-GitHub, gh binary
missing).

Tests use a real git repo in `tmp_path` to exercise the
`is_git_repo` + `get_default_branch_name` precondition gates,
then monkeypatch `livespec.io.gh.run_subprocess` to return canned
CompletedProcess carriers for the three gh CLI calls. Real
gh CLI is never invoked.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import no_stale_merged_pr_branch
from livespec.io import gh as io_gh
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOResult, IOSuccess

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
    surrounding repo. Test git operations then fail with
    `fatal: .git/index: index file open failed: Not a directory`.
    Scrubbing the vars confines git to the tmp_path fixture's
    `.git` directory.
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


def _completed(*, stdout: str, returncode: int = 0) -> subprocess.CompletedProcess[str]:
    """Build a fake CompletedProcess carrier for monkeypatched gh.run_subprocess."""
    return subprocess.CompletedProcess(
        args=["fake"],
        returncode=returncode,
        stdout=stdout,
        stderr="",
    )


@dataclass(frozen=True, kw_only=True, slots=True)
class _GhResponse:
    """Canned (stdout, returncode) response for one gh CLI invocation."""

    stdout: str = ""
    returncode: int = 0


_DEFAULT_REPO_VIEW: _GhResponse = _GhResponse(stdout="thewoolleyman/livespec\n")
_DEFAULT_BRANCHES: _GhResponse = _GhResponse()
_DEFAULT_MERGED_PRS: _GhResponse = _GhResponse()


def _install_gh_fake(
    *,
    monkeypatch: pytest.MonkeyPatch,
    repo_view: _GhResponse = _DEFAULT_REPO_VIEW,
    branches: _GhResponse = _DEFAULT_BRANCHES,
    merged_prs: _GhResponse = _DEFAULT_MERGED_PRS,
) -> None:
    """Install a fake `livespec.io.gh.run_subprocess` that discriminates by argv.

    Inspects the second argv token (`repo` / `api` / `pr`) and
    returns the corresponding canned response. The doctor check
    calls the three gh primitives in sequence:
    get_repo_name_with_owner → list_remote_branches →
    list_merged_pull_request_head_refs.
    """
    by_subcommand: dict[str, _GhResponse] = {
        "repo": repo_view,
        "api": branches,
        "pr": merged_prs,
    }

    def fake_run_subprocess(
        *,
        argv: list[str],
        cwd: Path | None = None,
    ) -> IOResult[subprocess.CompletedProcess[str], Any]:
        _ = cwd
        response = by_subcommand[argv[1]]
        return IOResult.from_value(
            _completed(stdout=response.stdout, returncode=response.returncode),
        )

    monkeypatch.setattr(io_gh, "run_subprocess", fake_run_subprocess)


def test_passes_when_no_remote_branch_has_a_merged_pr(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`pass` when remote branches exist but none are fronted by a merged PR."""
    _scrub_git_env(monkeypatch=monkeypatch)
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    _git_commit_file(
        cwd=project_root,
        path=project_root / "seed.md",
        content=b"# Seed\n",
    )
    default_branch = _current_branch(cwd=project_root)
    _git_set_origin_head(cwd=project_root, default_branch=default_branch)
    _install_gh_fake(
        monkeypatch=monkeypatch,
        branches=_GhResponse(stdout=f"{default_branch}\nfeature/wip\n"),
        merged_prs=_GhResponse(stdout=""),
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_merged_pr_branch.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-merged-pr-branch",
        status="pass",
        message=(
            f"no-stale-merged-pr-branch: no remote branches fronted by "
            f"merged PRs to clean up (2 remote branch(es) scanned, "
            f"0 merged PR(s); default branch `{default_branch}` excluded)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_warns_when_remote_branch_fronts_a_merged_pr(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`warn` when at least one remote branch (non-default) has a merged PR fronting it."""
    _scrub_git_env(monkeypatch=monkeypatch)
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    _git_commit_file(
        cwd=project_root,
        path=project_root / "seed.md",
        content=b"# Seed\n",
    )
    default_branch = _current_branch(cwd=project_root)
    _git_set_origin_head(cwd=project_root, default_branch=default_branch)
    _install_gh_fake(
        monkeypatch=monkeypatch,
        repo_view=_GhResponse(stdout="thewoolleyman/livespec\n"),
        branches=_GhResponse(stdout=f"{default_branch}\nfeature/done\nfeature/wip\n"),
        merged_prs=_GhResponse(stdout="feature/done\n"),
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_merged_pr_branch.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-merged-pr-branch",
        status="warn",
        message=(
            "no-stale-merged-pr-branch: 1 remote branch(es) fronted "
            "by merged PR(s) and ready to delete: feature/done. "
            "Corrective action: gh api -X DELETE "
            "repos/thewoolleyman/livespec/git/refs/heads/feature/done"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_excludes_default_branch_from_stale_set(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default branch never appears in the warn-stale set even if it has a merged PR.

    A merged PR landed on default would be the typical case (PRs
    merge INTO the default branch). The contract excludes the
    default branch from cleanup candidacy; this test pins that
    semantics.
    """
    _scrub_git_env(monkeypatch=monkeypatch)
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    _git_commit_file(
        cwd=project_root,
        path=project_root / "seed.md",
        content=b"# Seed\n",
    )
    default_branch = _current_branch(cwd=project_root)
    _git_set_origin_head(cwd=project_root, default_branch=default_branch)
    _install_gh_fake(
        monkeypatch=monkeypatch,
        branches=_GhResponse(stdout=f"{default_branch}\n"),
        merged_prs=_GhResponse(stdout=f"{default_branch}\n"),
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_merged_pr_branch.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-merged-pr-branch",
        status="pass",
        message=(
            f"no-stale-merged-pr-branch: no remote branches fronted by "
            f"merged PRs to clean up (1 remote branch(es) scanned, "
            f"1 merged PR(s); default branch `{default_branch}` excluded)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skipped_when_not_a_git_repo(
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
    result = no_stale_merged_pr_branch.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-merged-pr-branch",
        status="skipped",
        message=(
            "no-stale-merged-pr-branch: project_root is not a git " "working tree; check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skipped_when_origin_head_unset(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`skipped` when origin/HEAD is unset (default branch undetermined).

    Fresh git init with no remote configured; the symbolic-ref
    lookup fails and the lash branch surfaces a skipped finding
    with the precondition-not-met message.
    """
    _scrub_git_env(monkeypatch=monkeypatch)
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    _git_commit_file(
        cwd=project_root,
        path=project_root / "seed.md",
        content=b"# Seed\n",
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_merged_pr_branch.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-merged-pr-branch",
        status="skipped",
        message=(
            "no-stale-merged-pr-branch: precondition not met " "(PreconditionError); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skipped_when_gh_repo_view_fails(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`skipped` when `gh repo view` fails (unauthenticated, no remote, etc.)."""
    _scrub_git_env(monkeypatch=monkeypatch)
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    _git_commit_file(
        cwd=project_root,
        path=project_root / "seed.md",
        content=b"# Seed\n",
    )
    default_branch = _current_branch(cwd=project_root)
    _git_set_origin_head(cwd=project_root, default_branch=default_branch)
    _install_gh_fake(
        monkeypatch=monkeypatch,
        repo_view=_GhResponse(stdout="", returncode=1),
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_merged_pr_branch.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-merged-pr-branch",
        status="skipped",
        message=(
            "no-stale-merged-pr-branch: precondition not met " "(PreconditionError); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)
