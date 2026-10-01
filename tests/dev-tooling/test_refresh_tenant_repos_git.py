"""Tests for `dev-tooling/refresh_tenant_repos_git.py` — git identity/cleanliness/currency.

Every case runs against REAL temporary git repositories: a bare repo
standing in for `origin` (so fetch and push resolve with no network) plus
real clones, linked worktrees, and nested directories. The bare repos are
laid out as `<remotes>/<owner>/<repo>.git` so a clone's `origin` URL
carries the same `owner/repo` tail the registry's GitHub URL does, which
is exactly what the identity check compares.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "dev-tooling" / "refresh_tenant_repos_git.py"
_OWNER = "acme"
_REPO = "widget"
_URL = f"https://github.com/{_OWNER}/{_REPO}"


def _load_module() -> ModuleType:
    """Import the git helper by file path (`dev-tooling/` is not a package)."""
    spec = importlib.util.spec_from_file_location("refresh_tenant_repos_git", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(*, cwd: Path, args: list[str]) -> None:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, f"git {' '.join(args)} failed: {result.stderr}"


def _origin(*, tmp_path: Path) -> Path:
    """A bare `origin` at `<tmp>/remotes/<owner>/<repo>.git` holding one commit."""
    origin = tmp_path / "remotes" / _OWNER / f"{_REPO}.git"
    origin.parent.mkdir(parents=True, exist_ok=True)
    _git(cwd=tmp_path, args=["init", "--bare", "-q", "-b", "master", str(origin)])
    seed = tmp_path / "seed"
    _git(cwd=tmp_path, args=["clone", "-q", str(origin), str(seed)])
    _git(cwd=seed, args=["config", "user.email", "t@example.com"])
    _git(cwd=seed, args=["config", "user.name", "Test"])
    _git(cwd=seed, args=["commit", "-q", "--allow-empty", "-m", "init"])
    _git(cwd=seed, args=["push", "-q", "origin", "master"])
    return origin


def _clone(*, tmp_path: Path, origin: Path, name: str) -> Path:
    """A real clone of `origin` at `<tmp>/<name>`, with a commit identity set."""
    dest = tmp_path / name
    _git(cwd=tmp_path, args=["clone", "-q", str(origin), str(dest)])
    _git(cwd=dest, args=["config", "user.email", "t@example.com"])
    _git(cwd=dest, args=["config", "user.name", "Test"])
    return dest


def _commit(*, repo: Path, name: str) -> None:
    (repo / name).write_text(name, encoding="utf-8")
    _git(cwd=repo, args=["add", name])
    _git(cwd=repo, args=["commit", "-q", "-m", f"add {name}"])


def test_primary_checkout_resolves_the_same_path_from_a_linked_worktree(*, tmp_path: Path) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    primary = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)
    worktree = tmp_path / "linked"
    _git(cwd=primary, args=["worktree", "add", "-q", str(worktree), "-b", "side"])

    assert module.primary_checkout(project_root=primary) == primary
    assert module.primary_checkout(project_root=worktree) == primary


def test_primary_checkout_is_none_outside_a_git_repository(*, tmp_path: Path) -> None:
    module = _load_module()
    plain = tmp_path / "plain"
    plain.mkdir()

    assert module.primary_checkout(project_root=plain) is None


def test_a_clean_clone_of_the_declared_repo_has_no_identity_problem(*, tmp_path: Path) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)

    assert module.identity_problem(dest=dest, github_url=_URL) is None
    # The same repository named with a `.git` suffix is the same repository.
    assert module.identity_problem(dest=dest, github_url=f"{_URL}.git") is None


def test_a_symlink_destination_is_an_identity_problem(*, tmp_path: Path) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    real = _clone(tmp_path=tmp_path, origin=origin, name="real")
    link = tmp_path / _REPO
    link.symlink_to(real, target_is_directory=True)

    assert module.identity_problem(dest=link, github_url=_URL) == "destination is a symlink"


def test_a_non_directory_destination_is_an_identity_problem(*, tmp_path: Path) -> None:
    module = _load_module()
    plain_file = tmp_path / _REPO
    plain_file.write_text("not a repo", encoding="utf-8")

    problem = module.identity_problem(dest=plain_file, github_url=_URL)

    assert problem == "destination exists but is not a directory"


def test_a_non_repository_destination_is_an_identity_problem(*, tmp_path: Path) -> None:
    module = _load_module()
    plain_dir = tmp_path / _REPO
    plain_dir.mkdir()

    problem = module.identity_problem(dest=plain_dir, github_url=_URL)

    assert problem == "destination is not a git repository"


def test_a_directory_nested_inside_another_repository_is_an_identity_problem(
    *, tmp_path: Path
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    outer = _clone(tmp_path=tmp_path, origin=origin, name="outer")
    nested = outer / _REPO
    nested.mkdir()

    problem = module.identity_problem(dest=nested, github_url=_URL)

    assert problem is not None
    assert problem.startswith("destination is nested inside the repository at")


def test_a_linked_worktree_destination_is_an_identity_problem(*, tmp_path: Path) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    primary = _clone(tmp_path=tmp_path, origin=origin, name="primary")
    worktree = tmp_path / _REPO
    _git(cwd=primary, args=["worktree", "add", "-q", str(worktree), "-b", "side"])

    problem = module.identity_problem(dest=worktree, github_url=_URL)

    assert problem == "destination is a linked worktree, not a primary checkout"


def test_a_destination_without_an_origin_remote_is_an_identity_problem(*, tmp_path: Path) -> None:
    module = _load_module()
    standalone = tmp_path / _REPO
    standalone.mkdir()
    _git(cwd=standalone, args=["init", "-q", "-b", "master"])

    problem = module.identity_problem(dest=standalone, github_url=_URL)

    assert problem == "destination has no `origin` remote"


def test_a_clone_of_a_different_origin_is_an_identity_problem(*, tmp_path: Path) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)

    problem = module.identity_problem(dest=dest, github_url="https://github.com/acme/other")

    assert problem is not None
    assert problem.endswith("which is not https://github.com/acme/other")


def test_sweep_ds_store_deletes_only_untracked_regular_droppings(*, tmp_path: Path) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)
    # A TRACKED .DS_Store, modified — never a candidate, because a
    # tracked file never appears in the untracked set.
    tracked = dest / "tracked"
    tracked.mkdir()
    (tracked / ".DS_Store").write_text("tracked", encoding="utf-8")
    _git(cwd=dest, args=["add", "tracked/.DS_Store"])
    _git(cwd=dest, args=["commit", "-q", "-m", "track a .DS_Store"])
    (tracked / ".DS_Store").write_text("modified", encoding="utf-8")
    # An untracked SYMLINK named .DS_Store — left in place.
    linked = dest / "linked"
    linked.mkdir()
    (linked / ".DS_Store").symlink_to(tracked / ".DS_Store")
    # An untracked file with another name — left in place.
    (dest / "notes.txt").write_text("keep me", encoding="utf-8")
    # The actual droppings.
    (dest / ".DS_Store").write_text("finder", encoding="utf-8")
    (dest / "sub").mkdir()
    (dest / "sub" / ".DS_Store").write_text("finder", encoding="utf-8")

    removed = module.sweep_ds_store(repo=dest)

    assert sorted(removed) == [".DS_Store", "sub/.DS_Store"]
    assert not (dest / ".DS_Store").exists()
    assert not (dest / "sub" / ".DS_Store").exists()
    assert (linked / ".DS_Store").is_symlink()
    assert (tracked / ".DS_Store").read_text(encoding="utf-8") == "modified"
    assert (dest / "notes.txt").exists()


def test_porcelain_status_is_empty_for_a_clean_clone(*, tmp_path: Path) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)

    assert module.porcelain_status(repo=dest) == []
    assert module.sweep_ds_store(repo=dest) == []


@pytest.mark.parametrize("marker", ["MERGE_HEAD", "rebase-merge"])
def test_in_progress_operation_reports_an_interrupted_operation(
    *, tmp_path: Path, marker: str
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)

    assert module.in_progress_operation(repo=dest) is None

    (dest / ".git" / marker).write_text("", encoding="utf-8")

    assert module.in_progress_operation(repo=dest) == marker


def test_unpushed_count_counts_commits_absent_from_every_origin_ref(*, tmp_path: Path) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)

    assert module.unpushed_count(repo=dest) == 0

    _git(cwd=dest, args=["switch", "-q", "-c", "feature"])
    _commit(repo=dest, name="local-only")

    assert module.unpushed_count(repo=dest) == 1


def test_default_branch_ahead_distinguishes_behind_from_ahead(*, tmp_path: Path) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)

    # A local branch that does not exist is ahead of nothing.
    assert module.default_branch_ahead(repo=dest, default_branch="absent") == 0
    assert module.default_branch_ahead(repo=dest, default_branch="master") == 0

    _commit(repo=dest, name="local-ahead")

    assert module.default_branch_ahead(repo=dest, default_branch="master") == 1


def test_fetch_origin_succeeds_against_a_reachable_origin(*, tmp_path: Path) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)
    other = _clone(tmp_path=tmp_path, origin=origin, name="other")
    _commit(repo=other, name="pushed")
    _git(cwd=other, args=["push", "-q", "origin", "master"])

    assert module.fetch_origin(repo=dest) is None
    assert module.default_branch_ahead(repo=dest, default_branch="master") == 0
    behind = module.run_git(
        repo=dest, args=["rev-list", "--count", "master..refs/remotes/origin/master"]
    )
    assert behind.stdout.strip() == "1"


def test_fetch_origin_reports_an_unreachable_origin(*, tmp_path: Path) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)
    _git(cwd=dest, args=["remote", "set-url", "origin", str(tmp_path / "gone" / "widget.git")])

    problem = module.fetch_origin(repo=dest)

    assert problem is not None
    assert problem.startswith("`git fetch --prune origin` failed:")


def test_fast_forward_switches_to_the_default_branch_and_advances_it(*, tmp_path: Path) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)
    other = _clone(tmp_path=tmp_path, origin=origin, name="other")
    _commit(repo=other, name="pushed")
    _git(cwd=other, args=["push", "-q", "origin", "master"])
    _git(cwd=dest, args=["switch", "-q", "-c", "parked"])
    assert module.fetch_origin(repo=dest) is None

    assert module.fast_forward(repo=dest, default_branch="master") is None

    branch = module.run_git(repo=dest, args=["rev-parse", "--abbrev-ref", "HEAD"])
    assert branch.stdout.strip() == "master"
    assert (dest / "pushed").is_file()


def test_fast_forward_reports_a_branch_it_cannot_switch_to(*, tmp_path: Path) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)

    problem = module.fast_forward(repo=dest, default_branch="no-such-branch")

    assert problem is not None
    assert problem.startswith("`git switch no-such-branch` failed:")


def test_fast_forward_refuses_a_non_fast_forward(*, tmp_path: Path) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)
    other = _clone(tmp_path=tmp_path, origin=origin, name="other")
    _commit(repo=other, name="pushed")
    _git(cwd=other, args=["push", "-q", "origin", "master"])
    _commit(repo=dest, name="diverged")
    assert module.fetch_origin(repo=dest) is None

    problem = module.fast_forward(repo=dest, default_branch="master")

    assert problem is not None
    assert problem.startswith("`git merge --ff-only origin/master` failed:")
