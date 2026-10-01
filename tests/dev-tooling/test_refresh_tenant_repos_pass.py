"""Tests for `dev-tooling/refresh_tenant_repos_pass.py` — one repo's pass.

`process_target` is driven END TO END, against real temporary git
repositories and a fake `gh`, by `test_refresh_tenant_repos.py`: the
orchestrator's only job is the registry, the preflight, and the loop, so
every clone/refresh/preserve path reached through it is this module's.
What lives here is the seam that file cannot reach — the entry point's own
contract, asserted directly.
"""

from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest
import structlog

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "dev-tooling" / "refresh_tenant_repos_pass.py"


def _load_module() -> ModuleType:
    """Import the pass by file path (`dev-tooling/` is not a package)."""
    sys.path.insert(0, str(_REPO_ROOT / "dev-tooling"))
    spec = importlib.util.spec_from_file_location("refresh_tenant_repos_pass", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_process_target_is_the_only_entry_point_the_orchestrator_may_call() -> None:
    """The split is a boundary, not a file move: nothing private crosses it.

    pyright strict (`reportPrivateUsage`) and the `private_calls` check
    both reject importing a `_`-prefixed name across modules, so the pass
    exposes exactly one public name and the orchestrator imports only it.
    """
    module = _load_module()

    assert module.__all__ == ["process_target"]
    assert callable(module.process_target)


_OWNER = "acme"
_GITHUB = "https://github.com/"

_FAKE_GH = """#!/usr/bin/env bash
set -uo pipefail
if [[ "${1:-} ${2:-}" == "repo view" ]]; then
    printf '{"nameWithOwner":"%s","defaultBranchRef":{"name":"master"}}\\n' "$3"
    exit 0
fi
exit 99
"""


def _git(*, cwd: Path, args: list[str]) -> None:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, f"git {' '.join(args)} failed: {result.stderr}"


def test_a_failed_in_progress_probe_preserves_the_repo_as_an_inspection_failure(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A probe that could not look must never be read as "nothing in progress".

    This is the one fail-closed branch the end-to-end suite cannot reach:
    the identity check settles FIRST and resolves the git directory, so any
    real corruption that breaks `git rev-parse --absolute-git-dir` has
    already been reported as a placement problem by the time this probe
    runs. `test_refresh_tenant_repos_git.py` proves the probe really does
    answer with a problem on a real directory that has no git dir; what is
    asserted here is the WIRING above it — that such an answer preserves
    the repo as an inspection failure rather than falling through to the
    sweep, the fetch, and a fast-forward.
    """
    module = _load_module()
    facts = importlib.import_module("refresh_tenant_repos_git").TextFacts
    peer_root = tmp_path / "peers"
    peer_root.mkdir()
    dest = peer_root / "widget"
    dest.mkdir()
    _git(cwd=dest, args=["init", "-q", "-b", "master"])
    _git(cwd=dest, args=["remote", "add", "origin", f"{_GITHUB}{_OWNER}/widget"])
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_path = bin_dir / "gh"
    gh_path.write_text(_FAKE_GH, encoding="utf-8")
    gh_path.chmod(gh_path.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setattr(
        module,
        "in_progress_operation",
        lambda *, repo: facts(  # noqa: ARG005  — the probe ignores its repo here.
            problem="git inspection `git rev-parse --absolute-git-dir` failed: not a repository",
            values=(),
        ),
    )

    problem = module.process_target(
        target=module.RepoTarget(
            repo="widget",
            owner=_OWNER,
            github_url=f"{_GITHUB}{_OWNER}/widget",
            default_branch="master",
        ),
        peer_root=peer_root,
        log=structlog.get_logger(),
    )

    assert problem is not None
    assert problem.state == "inspection-failed"
    assert "git rev-parse --absolute-git-dir" in problem.detail


def _render_to_stderr() -> structlog.stdlib.BoundLogger:
    """A logger configured exactly as the refresher's own is, JSON onto stderr.

    The point of the case below is the text an operator READS, so the
    rendering has to be the real one rather than a captured event dict.
    """
    structlog.reset_defaults()
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    return structlog.get_logger("refresh_tenant_repos")


def _governed_clone(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A real `widget` repo in a peer root, with the fake `gh` first on PATH."""
    peer_root = tmp_path / "peers"
    peer_root.mkdir()
    dest = peer_root / "widget"
    dest.mkdir()
    _git(cwd=dest, args=["init", "-q", "-b", "master"])
    _git(cwd=dest, args=["config", "user.email", "t@example.com"])
    _git(cwd=dest, args=["config", "user.name", "Test"])
    _git(cwd=dest, args=["remote", "add", "origin", f"{_GITHUB}{_OWNER}/widget"])
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_path = bin_dir / "gh"
    gh_path.write_text(_FAKE_GH, encoding="utf-8")
    gh_path.chmod(gh_path.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    return dest


def _head(*, repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _conflicted(*, repo: Path, operation: str) -> None:
    """Leave `repo` GENUINELY mid-`operation`, stopped on a real conflict.

    Writing a marker file proves the probe reads it, but not that git would
    ever have left it there. Here git itself does: two branches rewrite the
    same line, and `git merge` / `git cherry-pick` stops with the operation
    open and the conflict unresolved.
    """
    (repo / "f.txt").write_text("base\n", encoding="utf-8")
    _git(cwd=repo, args=["add", "f.txt"])
    _git(cwd=repo, args=["commit", "-q", "-m", "base"])
    _git(cwd=repo, args=["switch", "-q", "-c", "side"])
    (repo / "f.txt").write_text("side\n", encoding="utf-8")
    _git(cwd=repo, args=["add", "f.txt"])
    _git(cwd=repo, args=["commit", "-q", "-m", "side"])
    _git(cwd=repo, args=["switch", "-q", "master"])
    (repo / "f.txt").write_text("main\n", encoding="utf-8")
    _git(cwd=repo, args=["add", "f.txt"])
    _git(cwd=repo, args=["commit", "-q", "-m", "main"])
    stopped = subprocess.run(
        ["git", "-C", str(repo), operation, "side"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert stopped.returncode != 0, f"`git {operation} side` did not conflict: {stopped.stdout}"


@pytest.mark.parametrize(
    ("operation", "marker"),
    [("cherry-pick", "CHERRY_PICK_HEAD"), ("merge", "MERGE_HEAD")],
)
def test_a_repo_left_mid_operation_is_told_in_words_to_choose_one_command(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    operation: str,
    marker: str,
) -> None:
    """A real mid-operation repo's EMITTED report presents the two as a choice.

    Git itself leaves this repository mid-operation, and what is asserted is
    the rendered line an operator reads: the continue, the abort, and the
    words that make them alternatives rather than a sequence. That labelling
    is the difference between a maintainer finishing the operation and a
    maintainer running `--continue` followed by `--abort` and discarding the
    resolution they had just completed — docstrings do not reach them, so it
    has to be in the output. Afterwards the operation is STILL open, which is
    how this case proves the refresher ran neither command itself.
    """
    module = _load_module()
    dest = _governed_clone(tmp_path=tmp_path, monkeypatch=monkeypatch)
    _conflicted(repo=dest, operation=operation)
    assert (dest / ".git" / marker).exists()
    before = _head(repo=dest)

    problem = module.process_target(
        target=module.RepoTarget(
            repo="widget",
            owner=_OWNER,
            github_url=f"{_GITHUB}{_OWNER}/widget",
            default_branch="master",
        ),
        peer_root=dest.parent,
        log=_render_to_stderr(),
    )

    assert problem is not None
    assert problem.state == "interrupted-operation"
    assert problem.markers == (marker,)

    stderr = capsys.readouterr().err
    assert f"CHOOSE ONE of the next two commands for the interrupted {operation}." in stderr
    assert "Do NOT run both:" in stderr
    assert "(1) finish it, keeping the conflict resolution already done:" in stderr
    assert "(2) OR abandon it, discarding that work:" in stderr
    assert f"git -C {dest} {operation} --continue" in stderr
    assert f"git -C {dest} {operation} --abort" in stderr
    assert (dest / ".git" / marker).exists()
    assert _head(repo=dest) == before
