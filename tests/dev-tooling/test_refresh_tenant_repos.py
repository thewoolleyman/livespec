"""Tests for `dev-tooling/refresh_tenant_repos.py` — the refresher's whole arc.

Every case runs against REAL temporary git repositories and a FAKE `gh`
executable placed on `PATH`. The bare `origin` repos live at
`<tmp>/remotes/<owner>/<repo>.git` so a clone's `origin` URL carries the
same `owner/repo` tail the registry's GitHub URL does; the livespec
stand-in primary checkout lives at `<tmp>/peers/project`, which makes
`<tmp>/peers` the peer root every destination is placed in.

The fake `gh` records its argv to a log file, so a test can assert both
what WAS invoked (`gh repo view` resolved the canonical identity) and
what was NOT (nothing was asked of GitHub before the preflight refused).

Cloning and fetching are git's own HTTPS operations, not `gh`'s, so a
per-test `GIT_CONFIG_GLOBAL` carries a
`url.<remotes>/.insteadOf = https://github.com/` rewrite that resolves
every canonical GitHub URL to a local bare repo. Each existing clone's
`origin` is a real `https://github.com/...` URL, which is what lets the
suite exercise the host check that rejects a filesystem `origin`.
"""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "dev-tooling" / "refresh_tenant_repos.py"
_OWNER = "acme"
_GITHUB = "https://github.com/"
# The commands an operator is owed for each interrupted operation, spelled
# out here rather than read back from the report module: a test that
# derived them from the same table it is checking would pass whatever that
# table said. `rebase-apply` and `rebase-merge` are the two rebase
# backends, and are DIRECTORIES in a real repository rather than files.
_RECOVERY_VERBS: dict[str, tuple[str, ...]] = {
    "BISECT_LOG": ("bisect reset",),
    "CHERRY_PICK_HEAD": ("cherry-pick --continue", "cherry-pick --abort"),
    "MERGE_HEAD": ("merge --continue", "merge --abort"),
    "REVERT_HEAD": ("revert --continue", "revert --abort"),
    "rebase-apply": ("rebase --continue", "rebase --abort"),
    "rebase-merge": ("rebase --continue", "rebase --abort"),
}
_DIRECTORY_MARKERS = frozenset({"rebase-apply", "rebase-merge"})

_FAKE_GH = """#!/usr/bin/env bash
set -uo pipefail
printf '%s\\n' "$*" >> "$FAKE_GH_LOG"
if [[ "${1:-} ${2:-}" == "auth status" ]]; then
    exit "${FAKE_GH_AUTH_EXIT:-0}"
fi
if [[ "${1:-} ${2:-}" == "repo view" ]]; then
    printf '{"nameWithOwner":"%s","defaultBranchRef":{"name":"%s"}}\\n' \
        "${FAKE_GH_NAME_WITH_OWNER:-$3}" "${FAKE_GH_DEFAULT_BRANCH-master}"
    exit "${FAKE_GH_VIEW_EXIT:-0}"
fi
printf 'unexpected gh argv: %s\\n' "$*" >&2
exit 99
"""


def _load_module() -> ModuleType:
    """Import the refresher by file path (`dev-tooling/` is not a package)."""
    spec = importlib.util.spec_from_file_location("refresh_tenant_repos", _SCRIPT)
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


def _git_out(*, cwd: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, f"git {' '.join(args)} failed: {result.stderr}"
    return result.stdout.strip()


def _route_github_locally(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every `https://github.com/` URL resolve to `<tmp>/remotes/`."""
    config = tmp_path / "gitconfig"
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    remotes = tmp_path / "remotes"
    remotes.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "config", "--file", str(config), f"url.{remotes}/.insteadOf", _GITHUB],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _origin(*, tmp_path: Path, repo: str, owner: str = _OWNER) -> Path:
    """A bare `origin` at `<tmp>/remotes/<owner>/<repo>` holding one commit."""
    origin = tmp_path / "remotes" / owner / repo
    origin.parent.mkdir(parents=True, exist_ok=True)
    _git(cwd=tmp_path, args=["init", "--bare", "-q", "-b", "master", str(origin)])
    seed = tmp_path / f"seed-{repo}"
    _git(cwd=tmp_path, args=["clone", "-q", str(origin), str(seed)])
    _identify(repo=seed)
    _git(cwd=seed, args=["commit", "-q", "--allow-empty", "-m", "init"])
    _git(cwd=seed, args=["push", "-q", "origin", "master"])
    return origin


def _identify(*, repo: Path) -> None:
    _git(cwd=repo, args=["config", "user.email", "t@example.com"])
    _git(cwd=repo, args=["config", "user.name", "Test"])


def _clone(*, into: Path, origin: Path, name: str, slug: str | None = None) -> Path:
    """A clone of `origin` at `<into>/<name>` whose `origin` is a github.com URL."""
    dest = into / name
    _git(cwd=into, args=["clone", "-q", str(origin), str(dest)])
    _git(
        cwd=dest,
        args=["remote", "set-url", "origin", f"{_GITHUB}{slug or f'{_OWNER}/{name}'}"],
    )
    _identify(repo=dest)
    return dest


def _commit(*, repo: Path, name: str) -> None:
    (repo / name).write_text(name, encoding="utf-8")
    _git(cwd=repo, args=["add", name])
    _git(cwd=repo, args=["commit", "-q", "-m", f"add {name}"])


def _advance_origin(*, tmp_path: Path, origin: Path, name: str) -> None:
    """Push one new commit to `origin` from a throwaway clone."""
    pusher = tmp_path / f"pusher-{name}"
    _git(cwd=tmp_path, args=["clone", "-q", str(origin), str(pusher)])
    _identify(repo=pusher)
    _commit(repo=pusher, name=name)
    _git(cwd=pusher, args=["push", "-q", "origin", "master"])


def _origin_dirty_on_checkout(*, tmp_path: Path, repo: str) -> Path:
    """A bare `origin` whose every fresh clone has a modified file immediately.

    The CRLF blob is committed BEFORE the `eol=lf` attribute that governs
    it, so the stored blob keeps its carriage returns while a checkout
    writes the normalized LF form. `git status` in a brand-new clone
    therefore reports the file as modified without anybody touching it —
    which is the state a clone-then-verify step has to catch.
    """
    origin = tmp_path / "remotes" / _OWNER / repo
    origin.parent.mkdir(parents=True, exist_ok=True)
    _git(cwd=tmp_path, args=["init", "--bare", "-q", "-b", "master", str(origin)])
    seed = tmp_path / f"seed-{repo}"
    _git(cwd=tmp_path, args=["clone", "-q", str(origin), str(seed)])
    _identify(repo=seed)
    (seed / "crlf.txt").write_bytes(b"first\r\nsecond\r\n")
    _git(cwd=seed, args=["add", "crlf.txt"])
    _git(cwd=seed, args=["commit", "-q", "-m", "store a CRLF blob"])
    (seed / ".gitattributes").write_text("*.txt text eol=lf\n", encoding="utf-8")
    _git(cwd=seed, args=["add", ".gitattributes"])
    _git(cwd=seed, args=["commit", "-q", "-m", "normalize *.txt to LF"])
    _git(cwd=seed, args=["push", "-q", "origin", "master"])
    return origin


def _peer_root(*, tmp_path: Path) -> Path:
    peers = tmp_path / "peers"
    peers.mkdir(exist_ok=True)
    return peers


def _project(*, tmp_path: Path, repos: dict[str, str | None]) -> Path:
    """The livespec stand-in primary checkout, carrying both registries.

    `repos` maps a repo name to its declared default branch, or to None
    to leave the default branch undeclared so the refresher has to ask
    GitHub for it.
    """
    project = _peer_root(tmp_path=tmp_path) / "project"
    project.mkdir()
    _git(cwd=project, args=["init", "-q", "-b", "master"])
    _write_registries(project=project, repos=repos)
    return project


def _write_registries(*, project: Path, repos: dict[str, str | None]) -> None:
    targets: dict[str, dict[str, str]] = {}
    for name, branch in repos.items():
        entry = {"github_url": f"https://github.com/{_OWNER}/{name}"}
        if branch is not None:
            entry["default_branch"] = branch
        targets[name] = entry
    (project / ".livespec.jsonc").write_text(
        json.dumps({"cross_repo_targets": targets}), encoding="utf-8"
    )
    (project / ".livespec-fleet-manifest.jsonc").write_text(
        json.dumps({"owner": _OWNER, "fleet": [], "adopters": []}), encoding="utf-8"
    )


def _install_fake_gh(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put a recording fake `gh` first on PATH; return its argv log path."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_path = bin_dir / "gh"
    gh_path.write_text(_FAKE_GH, encoding="utf-8")
    gh_path.chmod(gh_path.stat().st_mode | stat.S_IXUSR)
    log = tmp_path / "gh-argv.log"
    log.write_text("", encoding="utf-8")
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_GH_LOG", str(log))
    _route_github_locally(tmp_path=tmp_path, monkeypatch=monkeypatch)
    return log


def test_justfile_declares_the_refresh_tenant_repos_recipe() -> None:
    body = (_REPO_ROOT / "justfile").read_text(encoding="utf-8")

    assert "refresh-tenant-repos:\n    uv run python3 dev-tooling/refresh_tenant_repos.py\n" in body


def test_a_missing_gh_binary_exits_2_before_any_clone_or_fetch(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    _ = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    monkeypatch.setenv("PATH", "")

    assert module.refresh_tenant_repos(project_root=project) == 2
    assert not (_peer_root(tmp_path=tmp_path) / "widget").exists()


def test_a_failing_gh_auth_status_exits_2_before_any_clone_or_fetch(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    _ = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    log = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    monkeypatch.setenv("FAKE_GH_AUTH_EXIT", "1")

    assert module.refresh_tenant_repos(project_root=project) == 2
    assert log.read_text(encoding="utf-8").strip() == "auth status"
    assert not (_peer_root(tmp_path=tmp_path) / "widget").exists()


def test_conflicting_registry_entries_exit_2_before_any_mutation(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    _ = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    log = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    (project / ".livespec-fleet-manifest.jsonc").write_text(
        json.dumps({"owner": "someone-else", "fleet": [{"repo": "widget"}], "adopters": []}),
        encoding="utf-8",
    )

    assert module.refresh_tenant_repos(project_root=project) == 2
    assert log.read_text(encoding="utf-8") == ""
    assert not (_peer_root(tmp_path=tmp_path) / "widget").exists()


def test_an_unsafe_repo_name_exits_2_before_any_mutation(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    project = _project(tmp_path=tmp_path, repos={})
    log = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    (project / ".livespec-fleet-manifest.jsonc").write_text(
        json.dumps({"owner": _OWNER, "fleet": [{"repo": "../escape"}], "adopters": []}),
        encoding="utf-8",
    )

    assert module.refresh_tenant_repos(project_root=project) == 2
    assert log.read_text(encoding="utf-8") == ""
    assert not (tmp_path / "escape").exists()


def test_a_missing_repo_is_cloned_into_the_peer_root_of_the_primary_checkout(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    _ = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    log = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _peer_root(tmp_path=tmp_path) / "widget"

    assert module.refresh_tenant_repos(project_root=project) == 0
    assert (dest / ".git").is_dir()
    assert f"repo view {_OWNER}/widget --json nameWithOwner,defaultBranchRef" in log.read_text(
        encoding="utf-8"
    )
    config = (dest / ".git" / "config").read_text(encoding="utf-8")
    assert f"url = {_GITHUB}{_OWNER}/widget" in config
    assert "credential" not in config


def test_a_clone_run_from_a_linked_worktree_still_uses_the_primary_peer_root(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The peer root is the PRIMARY checkout's parent, not the worktree's.

    A linked worktree lives wherever its operator put it, so deriving the
    destination from the worktree's own parent would scatter clones. The
    registries are committed here, as they are in a real checkout, so the
    worktree carries them.
    """
    module = _load_module()
    _ = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    _identify(repo=project)
    _git(cwd=project, args=["add", "--all"])
    _git(cwd=project, args=["commit", "-q", "-m", "commit the registries"])
    worktree = tmp_path / "elsewhere"
    _git(cwd=project, args=["worktree", "add", "-q", str(worktree), "-b", "side"])

    assert module.refresh_tenant_repos(project_root=worktree) == 0
    assert (_peer_root(tmp_path=tmp_path) / "widget" / ".git").is_dir()
    assert not (tmp_path / "widget").exists()


def test_a_failing_clone_is_reported_and_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    project = _project(tmp_path=tmp_path, repos={"never-created": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)

    assert module.refresh_tenant_repos(project_root=project) == 1
    assert not (_peer_root(tmp_path=tmp_path) / "never-created").exists()


def test_a_project_root_outside_a_git_repository_exits_2(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    plain = tmp_path / "plain"
    plain.mkdir()
    _write_registries(project=plain, repos={})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)

    assert module.refresh_tenant_repos(project_root=plain) == 2


def test_a_symlinked_destination_is_left_unmodified_and_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    real = _clone(into=tmp_path, origin=origin, name="real")
    link = _peer_root(tmp_path=tmp_path) / "widget"
    link.symlink_to(real, target_is_directory=True)
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")
    before = _git_out(cwd=real, args=["rev-parse", "HEAD"])

    assert module.refresh_tenant_repos(project_root=project) == 1
    assert link.is_symlink()
    assert _git_out(cwd=real, args=["rev-parse", "HEAD"]) == before


def test_a_linked_worktree_destination_is_left_unmodified_and_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    primary = _clone(into=tmp_path, origin=origin, name="primary")
    dest = _peer_root(tmp_path=tmp_path) / "widget"
    _git(cwd=primary, args=["worktree", "add", "-q", str(dest), "-b", "side"])

    assert module.refresh_tenant_repos(project_root=project) == 1
    assert _git_out(cwd=dest, args=["rev-parse", "--abbrev-ref", "HEAD"]) == "side"


def test_a_destination_nested_in_another_repository_is_left_unmodified_and_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    outer = _clone(into=tmp_path, origin=origin, name="outer")
    project = outer / "peers" / "project"
    project.parent.mkdir()
    project.mkdir()
    _git(cwd=project, args=["init", "-q", "-b", "master"])
    _write_registries(project=project, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = outer / "peers" / "widget"
    dest.mkdir()
    (dest / "keep.txt").write_text("keep", encoding="utf-8")

    assert module.refresh_tenant_repos(project_root=project) == 1
    assert (dest / "keep.txt").read_text(encoding="utf-8") == "keep"
    assert not (dest / ".git").exists()


def test_a_clone_of_a_different_origin_is_left_unmodified_and_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    other_origin = _origin(tmp_path=tmp_path, repo="impostor")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(
        into=_peer_root(tmp_path=tmp_path),
        origin=other_origin,
        name="widget",
        slug=f"{_OWNER}/impostor",
    )
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")
    before = _git_out(cwd=dest, args=["rev-parse", "HEAD"])

    assert module.refresh_tenant_repos(project_root=project) == 1
    assert _git_out(cwd=dest, args=["rev-parse", "HEAD"]) == before


@pytest.mark.parametrize("marker", sorted(_RECOVERY_VERBS))
def test_an_interrupted_git_operation_is_preserved_still_in_progress_and_exits_1(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    marker: str,
) -> None:
    """Every interrupted operation survives the run, and is handed BOTH ways out.

    The marker is still there afterwards, which is the assertion that the
    refresher ran no continue, no abort and no reset of its own: finishing
    the operation would have consumed it and abandoning it would have
    deleted it. What the maintainer gets instead is the pair of commands
    for THAT operation — a `merge --abort` is no use to a half-finished
    cherry-pick — so the choice between keeping the work and discarding it
    is theirs to make.
    """
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    if marker in _DIRECTORY_MARKERS:
        (dest / ".git" / marker).mkdir()
    else:
        (dest / ".git" / marker).write_text("", encoding="utf-8")
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")
    before = _git_out(cwd=dest, args=["rev-parse", "HEAD"])

    assert module.refresh_tenant_repos(project_root=project) == 1

    stderr = capsys.readouterr().err
    assert _git_out(cwd=dest, args=["rev-parse", "HEAD"]) == before
    assert (dest / ".git" / marker).exists()
    assert not (dest / "upstream").exists()
    assert "interrupted-operation" in stderr
    for verb in _RECOVERY_VERBS[marker]:
        assert f"git -C {dest} {verb}" in stderr


def test_an_unreachable_canonical_remote_leaves_the_repo_unmodified_and_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A fetch that fails stops the refresh instead of deciding without it.

    The fetch addresses the CANONICAL URL, so making the fetch the thing
    that fails means pointing the canonical identity at a repository that
    is not there while leaving `origin` naming the registered one — the
    identity check accepts the registered URL, so the run gets as far as
    the fetch. Every later decision depends on refs this run fetched, so
    the repo is preserved rather than judged against stale ones.
    """
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    monkeypatch.setenv("FAKE_GH_NAME_WITH_OWNER", f"{_OWNER}/moved")
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")

    assert module.refresh_tenant_repos(project_root=project) == 1
    assert not (dest / "upstream").exists()
    assert "fetch-failed" in capsys.readouterr().err


def test_a_dirty_repo_is_preserved_with_concrete_manual_cleanup_commands(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    (dest / "scratch.txt").write_text("unsaved work", encoding="utf-8")
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")
    before = _git_out(cwd=dest, args=["rev-parse", "HEAD"])

    assert module.refresh_tenant_repos(project_root=project) == 1

    stderr = capsys.readouterr().err
    assert (dest / "scratch.txt").read_text(encoding="utf-8") == "unsaved work"
    assert _git_out(cwd=dest, args=["rev-parse", "HEAD"]) == before
    assert f"git -C {dest} stash push --include-untracked" in stderr
    assert f"git -C {dest} merge --ff-only origin/master" in stderr
    assert "uncommitted-changes" in stderr


def test_a_branch_with_unpushed_commits_is_left_unmodified_and_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    _git(cwd=dest, args=["switch", "-q", "-c", "feature"])
    _commit(repo=dest, name="local-only")
    before = _git_out(cwd=dest, args=["rev-parse", "HEAD"])

    assert module.refresh_tenant_repos(project_root=project) == 1
    assert _git_out(cwd=dest, args=["rev-parse", "--abbrev-ref", "HEAD"]) == "feature"
    assert _git_out(cwd=dest, args=["rev-parse", "HEAD"]) == before


def test_a_diverged_default_branch_is_left_unmodified_and_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Divergence is its own refusal, distinct from "the branch is unpushed".

    The local commit is pushed to a SIDE ref on origin, so it is present
    on the remote and the unpushed guard passes; `origin/master` then
    moves on independently, which leaves local `master` ahead of — and
    diverged from — the remote default branch with nothing unpushed.
    """
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    _commit(repo=dest, name="local-ahead")
    _git(cwd=dest, args=["push", "-q", "origin", "master:refs/heads/sidecar"])
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")
    before = _git_out(cwd=dest, args=["rev-parse", "HEAD"])

    assert module.refresh_tenant_repos(project_root=project) == 1
    assert "is ahead of or diverged from origin/master" in capsys.readouterr().err
    assert _git_out(cwd=dest, args=["rev-parse", "HEAD"]) == before


def test_unpushed_and_divergence_are_judged_against_refs_the_run_itself_fetched(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stale `origin/master` must not make pushed work look unpushed.

    The destination's commit IS on origin, but its remote-tracking ref
    lags one commit behind — exactly the state a repo is left in when
    another clone pushed, or when a session was interrupted. Judged
    against that stale ref the repo looks both unpushed and ahead, and
    would be preserved; judged against refs the run fetches for itself it
    is merely current, and is refreshed.
    """
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    _commit(repo=dest, name="pushed")
    _git(cwd=dest, args=["push", "-q", "origin", "master"])
    stale = _git_out(cwd=dest, args=["rev-parse", "HEAD~1"])
    head = _git_out(cwd=dest, args=["rev-parse", "HEAD"])
    _git(cwd=dest, args=["update-ref", "refs/remotes/origin/master", stale])

    assert module.refresh_tenant_repos(project_root=project) == 0
    assert _git_out(cwd=dest, args=["rev-parse", "HEAD"]) == head
    assert _git_out(cwd=dest, args=["rev-parse", "refs/remotes/origin/master"]) == head


def test_a_clean_repo_behind_origin_is_switched_to_default_and_fast_forwarded(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    _git(cwd=dest, args=["switch", "-q", "-c", "parked"])
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")

    assert module.refresh_tenant_repos(project_root=project) == 0
    assert _git_out(cwd=dest, args=["rev-parse", "--abbrev-ref", "HEAD"]) == "master"
    assert (dest / "upstream").is_file()


def test_an_undeclared_default_branch_is_resolved_through_gh_repo_view(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": None})
    log = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")

    assert module.refresh_tenant_repos(project_root=project) == 0
    assert f"repo view {_OWNER}/widget" in log.read_text(encoding="utf-8")
    assert (dest / "upstream").is_file()


def test_an_unresolvable_default_branch_leaves_the_repo_unmodified_and_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": None})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    monkeypatch.setenv("FAKE_GH_VIEW_EXIT", "1")
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")

    assert module.refresh_tenant_repos(project_root=project) == 1
    assert not (dest / "upstream").exists()


def test_untracked_ds_store_droppings_are_deleted_and_the_repo_is_then_refreshed(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    (dest / ".DS_Store").write_text("finder", encoding="utf-8")
    (dest / "sub").mkdir()
    (dest / "sub" / ".DS_Store").write_text("finder", encoding="utf-8")
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")

    assert module.refresh_tenant_repos(project_root=project) == 0
    assert not (dest / ".DS_Store").exists()
    assert not (dest / "sub" / ".DS_Store").exists()
    assert (dest / "upstream").is_file()


def test_a_symlink_named_ds_store_is_never_deleted(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A symlink is operator intent, not a Finder dropping, so it survives.

    It is also untracked, so it keeps the tree dirty and the repo is
    preserved — which is the point: the sweep is narrow enough that it
    never reaches for something it was not asked to delete.
    """
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    (dest / "nested").mkdir()
    (dest / "nested" / ".DS_Store").symlink_to(dest / "nested" / "absent")
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")

    assert module.refresh_tenant_repos(project_root=project) == 1
    assert (dest / "nested" / ".DS_Store").is_symlink()
    assert not (dest / "upstream").exists()


def test_a_tracked_ds_store_is_never_deleted_and_the_repo_is_refreshed(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    pusher = tmp_path / "pusher-tracked"
    _git(cwd=tmp_path, args=["clone", "-q", str(origin), str(pusher)])
    _identify(repo=pusher)
    (pusher / ".DS_Store").write_text("tracked", encoding="utf-8")
    _git(cwd=pusher, args=["add", "-f", ".DS_Store"])
    _git(cwd=pusher, args=["commit", "-q", "-m", "track a .DS_Store"])
    _git(cwd=pusher, args=["push", "-q", "origin", "master"])
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    (dest / "sub").mkdir()
    (dest / "sub" / ".DS_Store").write_text("finder", encoding="utf-8")
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")

    assert module.refresh_tenant_repos(project_root=project) == 0
    assert not (dest / "sub" / ".DS_Store").exists()
    assert (dest / ".DS_Store").read_text(encoding="utf-8") == "tracked"
    assert (dest / "upstream").is_file()


def test_main_refreshes_the_project_root_named_on_the_command_line(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")
    monkeypatch.chdir(tmp_path)

    assert module.main(argv=["--project-root", str(project)]) == 0
    assert (_peer_root(tmp_path=tmp_path) / "widget" / "upstream").is_file()


def test_a_transferred_repo_is_cloned_from_and_named_by_its_canonical_identity(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The clone comes from the canonical pair; the DIRECTORY keeps the registered name.

    The live case: `thewoolleyman/homelab` redirects to
    `mi-homelab/homelab`. The peer layout is the maintainer's, so the
    directory stays `homelab` even when the canonical NAME differs too.
    """
    module = _load_module()
    _ = _origin(tmp_path=tmp_path, repo="renamed-widget", owner="renamed-org")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    monkeypatch.setenv("FAKE_GH_NAME_WITH_OWNER", "renamed-org/renamed-widget")
    dest = _peer_root(tmp_path=tmp_path) / "widget"

    assert module.refresh_tenant_repos(project_root=project) == 0
    assert (dest / ".git").is_dir()
    assert not (_peer_root(tmp_path=tmp_path) / "renamed-widget").exists()
    assert f"url = {_GITHUB}renamed-org/renamed-widget" in (dest / ".git" / "config").read_text(
        encoding="utf-8"
    )


def test_a_clone_already_carrying_the_canonical_url_is_refreshed_not_preserved(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The defect this corrects: every host preserved `homelab` after its transfer."""
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget", owner="renamed-org")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    monkeypatch.setenv("FAKE_GH_NAME_WITH_OWNER", "renamed-org/widget")
    dest = _clone(
        into=_peer_root(tmp_path=tmp_path),
        origin=origin,
        name="widget",
        slug="renamed-org/widget",
    )
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")

    assert module.refresh_tenant_repos(project_root=project) == 0
    assert (dest / "upstream").is_file()


@pytest.mark.parametrize(
    "origin_url",
    ["https://gitlab.com/acme/widget", "https://github.com/acme/impostor"],
)
def test_an_unrecognized_origin_is_untouched_before_any_fetch_or_cleanup(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, origin_url: str
) -> None:
    """Neither the registered nor the canonical repo — and not even swept.

    The surviving `.DS_Store` is the evidence that the refusal landed
    BEFORE the cleanup leg, not merely before the fast-forward.
    """
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    _git(cwd=dest, args=["remote", "set-url", "origin", origin_url])
    (dest / ".DS_Store").write_text("finder", encoding="utf-8")
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")

    assert module.refresh_tenant_repos(project_root=project) == 1
    assert (dest / ".DS_Store").is_file()
    assert not (dest / "upstream").exists()


def test_an_unreadable_index_is_reported_as_an_inspection_failure_and_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A failed `git status` must not read as a clean tree and get refreshed."""
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    (dest / ".git" / "index").unlink()
    (dest / ".git" / "index").mkdir()
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")

    assert module.refresh_tenant_repos(project_root=project) == 1

    stderr = capsys.readouterr().err
    assert "inspection-failed" in stderr
    assert not (dest / "upstream").exists()


def test_an_ssh_origin_still_fetches_over_https_and_keeps_its_git_config(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The fetch addresses the canonical HTTPS URL and writes nothing to config."""
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    _git(cwd=dest, args=["remote", "set-url", "origin", f"git@github.com:{_OWNER}/widget.git"])
    before = (dest / ".git" / "config").read_text(encoding="utf-8")
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")

    assert module.refresh_tenant_repos(project_root=project) == 0
    assert (dest / "upstream").is_file()
    assert (dest / ".git" / "config").read_text(encoding="utf-8") == before


def test_a_fresh_clone_is_landed_on_the_declared_default_branch_and_proved_clean(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GitHub's default is not necessarily the branch a registry declared."""
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    pusher = tmp_path / "pusher-trunk"
    _git(cwd=tmp_path, args=["clone", "-q", str(origin), str(pusher)])
    _identify(repo=pusher)
    _git(cwd=pusher, args=["switch", "-q", "-c", "trunk"])
    _commit(repo=pusher, name="on-trunk")
    _git(cwd=pusher, args=["push", "-q", "origin", "trunk"])
    project = _project(tmp_path=tmp_path, repos={"widget": "trunk"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _peer_root(tmp_path=tmp_path) / "widget"

    assert module.refresh_tenant_repos(project_root=project) == 0
    assert _git_out(cwd=dest, args=["rev-parse", "--abbrev-ref", "HEAD"]) == "trunk"
    assert _git_out(cwd=dest, args=["status", "--porcelain"]) == ""
    assert (dest / "on-trunk").is_file()


def test_a_fresh_clone_that_cannot_reach_its_declared_branch_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    _ = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "absent-branch"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)

    assert module.refresh_tenant_repos(project_root=project) == 1


def test_an_unpushed_branch_is_reported_with_push_commands_not_stash_commands(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Cleanup advice is state-specific: a stash would not help here."""
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    _git(cwd=dest, args=["switch", "-q", "-c", "feature"])
    _commit(repo=dest, name="local-only")

    assert module.refresh_tenant_repos(project_root=project) == 1

    stderr = capsys.readouterr().err
    assert "unpushed-commits" in stderr
    assert f"git -C {dest} push origin HEAD" in stderr
    assert "stash push" not in stderr


def test_a_diverged_default_branch_is_reported_with_rebase_commands(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    _commit(repo=dest, name="local-ahead")
    _git(cwd=dest, args=["push", "-q", "origin", "master:refs/heads/sidecar"])
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")

    assert module.refresh_tenant_repos(project_root=project) == 1

    stderr = capsys.readouterr().err
    assert "diverged-default-branch" in stderr
    assert f"git -C {dest} rebase origin/master" in stderr
    assert "stash push" not in stderr


def test_an_unwalkable_unpushed_probe_leaves_the_repo_unmodified_and_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An unborn HEAD cannot be walked, and zero would read as "nothing unpushed".

    The destination is a real primary checkout naming the registered
    repository, so identity, the interrupted-operation probe, the
    cleanliness verdict and the fetch all pass; the unpushed walk is the
    first thing that cannot answer. Counting that as zero would refresh a
    repository whose commits nobody managed to enumerate.
    """
    module = _load_module()
    _ = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _peer_root(tmp_path=tmp_path) / "widget"
    dest.mkdir()
    _git(cwd=dest, args=["init", "-q", "-b", "master"])
    _identify(repo=dest)
    _git(cwd=dest, args=["remote", "add", "origin", f"{_GITHUB}{_OWNER}/widget"])

    assert module.refresh_tenant_repos(project_root=project) == 1

    stderr = capsys.readouterr().err
    assert "inspection-failed" in stderr
    assert "git rev-list --count HEAD" in stderr


def test_an_unwalkable_divergence_probe_leaves_the_repo_unmodified_and_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A local default branch with no fetched counterpart cannot be compared.

    `refs/heads/trunk` exists, so the ref probe succeeds and the walk is
    reached — but the fetch brought no `refs/remotes/origin/trunk`, so the
    walk itself fails. Reading that as "ahead of nothing" would fast-
    forward against a comparison that never happened.
    """
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "trunk"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    _git(cwd=dest, args=["branch", "trunk"])
    before = _git_out(cwd=dest, args=["rev-parse", "HEAD"])

    assert module.refresh_tenant_repos(project_root=project) == 1
    assert _git_out(cwd=dest, args=["rev-parse", "HEAD"]) == before

    stderr = capsys.readouterr().err
    assert "inspection-failed" in stderr
    assert "git rev-list --count --left-right" in stderr


def test_a_default_branch_that_cannot_be_landed_leaves_the_repo_unmodified_and_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A declared default branch absent both locally and on origin cannot be landed.

    The ref probe exits 1 — genuinely absent, so "ahead of nothing" is the
    right answer — and the switch that would create it from
    `origin/trunk` has nothing to create it from. That refusal is
    reported rather than swallowed.
    """
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "trunk"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    before = _git_out(cwd=dest, args=["rev-parse", "HEAD"])

    assert module.refresh_tenant_repos(project_root=project) == 1
    assert _git_out(cwd=dest, args=["rev-parse", "HEAD"]) == before

    stderr = capsys.readouterr().err
    assert "default-branch-unresolved" in stderr
    assert "git switch trunk" in stderr


def test_a_default_branch_named_by_neither_registry_nor_github_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A repository with no branches yet leaves nothing to land on.

    `gh repo view` succeeds — the canonical identity IS resolved — but
    reports an empty `defaultBranchRef`, and no registry declares one
    either, so there is no branch to refresh onto and the repo is left
    alone instead of being guessed at.
    """
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": None})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    monkeypatch.setenv("FAKE_GH_DEFAULT_BRANCH", "")
    dest = _clone(into=_peer_root(tmp_path=tmp_path), origin=origin, name="widget")
    _advance_origin(tmp_path=tmp_path, origin=origin, name="upstream")

    assert module.refresh_tenant_repos(project_root=project) == 1
    assert not (dest / "upstream").exists()
    assert "default-branch-unresolved" in capsys.readouterr().err


def test_a_fresh_clone_that_checks_out_unclean_is_reported_and_exits_1(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A clone is not "refreshed" until the tree it produced is proved clean.

    The origin's stored blob disagrees with what its own `eol=lf`
    attribute checks out, so the clone lands dirty through no fault of the
    operator. Reporting it is the point: a clone verified only by its exit
    status would call this repository done.
    """
    module = _load_module()
    _ = _origin_dirty_on_checkout(tmp_path=tmp_path, repo="widget")
    project = _project(tmp_path=tmp_path, repos={"widget": "master"})
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _peer_root(tmp_path=tmp_path) / "widget"

    assert module.refresh_tenant_repos(project_root=project) == 1
    assert (dest / "crlf.txt").is_file()
    assert "uncommitted-changes" in capsys.readouterr().err
