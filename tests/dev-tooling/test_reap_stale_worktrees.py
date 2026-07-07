"""Outside-in test for `dev-tooling/reap_stale_worktrees.py` — worktree reaper.

The reaper is the Dispatcher-side janitor ACTION layer. DETECTION of
which non-primary worktrees are stale candidates is delegated to the
shared runtime seam
`livespec_runtime.hygiene_scan.detect_stale_worktrees`, which returns a
SUPERSET of "safe to remove": prunable worktrees, clean worktrees whose
HEAD is an ancestor of `origin/HEAD` (fast-forward / merge-commit
merges), and clean worktrees whose pushed branch is now remote-gone
(rebase-merge orphans). The reaper layers the action-only safety the
seam omits: it skips the current worktree, live-locked worktrees, and
non-prunable never-pushed worktrees (dispatched agents' in-progress
work), removes the rest, deletes any local branch, and prunes.
`--dry-run` mutates nothing.

These tests construct real tmp git repos (with a local bare repo
standing in for `origin` so `git ls-remote` resolves without the
network) and exercise the reaper's importable helpers + its
filesystem-mutating reap path against the real runtime seam. Tests that
exercise the clean+merged ancestor-of-`origin/HEAD` signal set
`refs/remotes/origin/HEAD` explicitly (a fresh local bare clone leaves
it unset). PID-liveness is monkeypatched so a "live lock" fixture is
deterministic without spawning a real process. No real network and no
mutation against the live livespec repo occurs.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "dev-tooling" / "reap_stale_worktrees.py"


def _load_module() -> ModuleType:
    """Import the reaper script as a module by file path.

    The script lives at `dev-tooling/reap_stale_worktrees.py` (a
    top-level dev-tooling tool, not an importable package member),
    so it is loaded via `importlib.util.spec_from_file_location`.
    """
    spec = importlib.util.spec_from_file_location("reap_stale_worktrees", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register in sys.modules before exec so the module's
    # `@dataclass` decorator can resolve `cls.__module__` (the
    # dataclasses machinery looks the module up by name to resolve
    # type hints / InitVar).
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(*, cwd: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )


def _init_primary_with_origin(*, tmp_path: Path) -> tuple[Path, Path]:
    """Create a bare `origin` + a primary clone with one commit on master.

    Returns `(primary_path, origin_path)`. The primary has
    `origin` configured as a remote so the reaper's
    `git ls-remote --heads origin <branch>` resolves locally.
    """
    origin = tmp_path / "origin.git"
    _ = _git(cwd=tmp_path, args=["init", "--bare", "-q", "-b", "master", str(origin)])
    primary = tmp_path / "primary"
    _ = _git(cwd=tmp_path, args=["clone", "-q", str(origin), str(primary)])
    _ = _git(cwd=primary, args=["config", "user.email", "t@example.com"])
    _ = _git(cwd=primary, args=["config", "user.name", "Test"])
    _ = _git(cwd=primary, args=["commit", "-q", "--allow-empty", "-m", "init"])
    _ = _git(cwd=primary, args=["push", "-q", "origin", "master"])
    return primary, origin


def _add_worktree(*, primary: Path, name: str, branch: str) -> Path:
    wt = primary.parent / name
    _ = _git(cwd=primary, args=["worktree", "add", "-q", str(wt), "-b", branch])
    return wt


def _push_branch(*, cwd: Path, branch: str, set_upstream: bool) -> None:
    """Push `branch` to origin, optionally recording upstream config (`-u`)."""
    if set_upstream:
        _ = _git(cwd=cwd, args=["push", "-q", "-u", "origin", branch])
    else:
        _ = _git(cwd=cwd, args=["push", "-q", "origin", branch])


def _delete_on_origin(*, origin: Path, branch: str) -> None:
    """Delete `branch` directly in the bare origin (as the forge does on rebase-merge).

    Deleting in the bare repo — rather than via `git push --delete`
    from the clone — leaves the clone's remote-tracking state
    untouched, faithfully simulating a server-side delete the local
    repo has not yet observed.
    """
    _ = _git(cwd=origin, args=["branch", "-D", branch])


def _make_branch_done(*, primary: Path, push_from: Path, origin: Path, branch: str) -> None:
    """Give `branch` the full merged-PR lifecycle signal.

    Pushed with upstream (`-u`), remote branch deleted server-side
    (directly in the bare origin), remote-tracking refs pruned. The
    surviving upstream config (`branch.<name>.merge`) is the local
    "was pushed" evidence that lets remote-absence mean merged
    rather than never-pushed.
    """
    _push_branch(cwd=push_from, branch=branch, set_upstream=True)
    _delete_on_origin(origin=origin, branch=branch)
    _ = _git(cwd=primary, args=["fetch", "-q", "--prune", "origin"])


def _set_origin_head(*, primary: Path) -> None:
    """Point `refs/remotes/origin/HEAD` at `origin/master`.

    A fresh clone of an empty bare repo leaves `refs/remotes/origin/HEAD`
    unset, so the runtime seam's `ancestor-of-origin/HEAD` merged signal
    cannot resolve. Setting it explicitly (offline symbolic-ref) lets the
    clean+merged detection path fire in tests. `refs/remotes/origin/master`
    exists once the primary has pushed master.
    """
    _ = _git(
        cwd=primary,
        args=["symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/master"],
    )


def test_parse_worktrees_extracts_primary_branch_and_lock() -> None:
    """`_parse_worktrees` flags the first worktree as primary and parses branch + lock reason."""
    module = _load_module()
    porcelain = (
        "worktree /repo/primary\n"
        "HEAD aaaa\n"
        "branch refs/heads/master\n"
        "\n"
        "worktree /repo/wt1\n"
        "HEAD bbbb\n"
        "branch refs/heads/feature1\n"
        "locked session=x (pid 4242)\n"
        "\n"
    )
    parsed = module._parse_worktrees(porcelain=porcelain)  # noqa: SLF001
    assert len(parsed) == 2
    primary, secondary = parsed
    assert primary.is_primary is True
    assert primary.branch == "master"
    assert primary.locked_reason is None
    assert secondary.is_primary is False
    assert secondary.branch == "feature1"
    assert secondary.locked_reason == "session=x (pid 4242)"


def test_parse_worktrees_handles_detached_head() -> None:
    """A detached-HEAD worktree (no `branch` line) parses with `branch=None`."""
    module = _load_module()
    porcelain = "worktree /repo/primary\nHEAD aaaa\ndetached\n\n"
    parsed = module._parse_worktrees(porcelain=porcelain)  # noqa: SLF001
    assert len(parsed) == 1
    assert parsed[0].branch is None
    assert parsed[0].locked_reason is None


def test_parse_locked_pid_extracts_and_handles_absence() -> None:
    """`_parse_locked_pid` returns the int pid when present, else None."""
    module = _load_module()
    assert module._parse_locked_pid(reason="orchestrator session (pid 9871)") == 9871  # noqa: SLF001
    assert module._parse_locked_pid(reason="manual hold, no pid here") is None  # noqa: SLF001


def test_pid_is_alive_true_for_self_false_for_dead() -> None:
    """`_pid_is_alive` is True for the current process, False for a never-allocated pid."""
    module = _load_module()
    assert module._pid_is_alive(pid=os.getpid()) is True  # noqa: SLF001
    # PID 2**31-1 is effectively never allocated on Linux.
    assert module._pid_is_alive(pid=2**31 - 1) is False  # noqa: SLF001


def test_pid_is_alive_treats_permission_and_other_oserror_as_alive(
    *, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A PermissionError (or any other OSError) from os.kill means the pid is ALIVE.

    `os.kill(pid, 0)` raising `PermissionError` means the process
    exists but is owned by another user; any other `OSError` is
    treated conservatively as alive so a live session is never
    reaped on an ambiguous probe.
    """
    module = _load_module()

    def _raise_permission(_pid: int, _sig: int) -> None:
        raise PermissionError

    def _raise_oserror(_pid: int, _sig: int) -> None:
        raise OSError

    monkeypatch.setattr(module.os, "kill", _raise_permission)
    assert module._pid_is_alive(pid=1234) is True  # noqa: SLF001
    monkeypatch.setattr(module.os, "kill", _raise_oserror)
    assert module._pid_is_alive(pid=1234) is True  # noqa: SLF001


def test_skips_detached_head_secondary(*, tmp_path: Path) -> None:
    """A non-primary detached-HEAD worktree (branch is None) is SKIPPED."""
    module = _load_module()
    primary, _origin = _init_primary_with_origin(tmp_path=tmp_path)
    wt = primary.parent / "wt-detached"
    head = _git(cwd=primary, args=["rev-parse", "HEAD"]).stdout.strip()
    _ = _git(cwd=primary, args=["worktree", "add", "-q", "--detach", str(wt), head])

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(wt) not in reaped
    assert wt.is_dir()


def test_reaps_pushed_then_remote_deleted_worktree(*, tmp_path: Path) -> None:
    """A clean worktree whose branch was pushed (`-u`) and is now remote-gone IS reaped.

    Simulates the full rebase-merge lifecycle: push with upstream,
    server-side remote-branch delete, `fetch --prune` (so even the
    remote-tracking ref is gone). The surviving upstream config
    (`branch.<name>.merge`) is the "was pushed" evidence that makes
    remote-absence mean merged rather than never-pushed.
    """
    module = _load_module()
    primary, origin = _init_primary_with_origin(tmp_path=tmp_path)
    wt = _add_worktree(primary=primary, name="wt-done", branch="feat-done")
    _make_branch_done(primary=primary, push_from=wt, origin=origin, branch="feat-done")
    assert wt.is_dir()

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(wt) in reaped
    assert not wt.exists()
    branches = _git(cwd=primary, args=["branch", "--list", "feat-done"]).stdout
    assert branches.strip() == ""


def test_skips_clean_never_pushed_worktree(*, tmp_path: Path) -> None:
    """A clean worktree on a local-only NEVER-PUSHED branch is SKIPPED (in-progress work).

    Regression for the dispatch race: a dispatched agent's worktree
    starts clean on a local-only branch with no upstream config and
    no remote-tracking ref. `git ls-remote` reports the branch
    absent from origin — the same raw signal as a merged-then-
    deleted branch — but absent-because-never-pushed means the work
    has not landed yet. Reaping here deletes the branch + worktree
    out from under the live agent.
    """
    module = _load_module()
    primary, _origin = _init_primary_with_origin(tmp_path=tmp_path)
    wt = _add_worktree(primary=primary, name="wt-inprogress", branch="feat-inprogress")

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(wt) not in reaped
    assert wt.is_dir()
    branches = _git(cwd=primary, args=["branch", "--list", "feat-inprogress"]).stdout
    assert branches.strip() != ""


def test_reaps_remote_gone_worktree_with_lingering_tracking_ref(*, tmp_path: Path) -> None:
    """A branch pushed WITHOUT `-u` (tracking ref only) that is now remote-gone IS reaped.

    A plain `git push origin <branch>` writes the remote-tracking
    ref but no upstream config; until `fetch --prune` runs, that
    ref is the only local "was pushed" evidence after the server
    deletes the branch. Either pushed-signal alone must qualify.
    """
    module = _load_module()
    primary, origin = _init_primary_with_origin(tmp_path=tmp_path)
    wt = _add_worktree(primary=primary, name="wt-tracked", branch="feat-tracked")
    _push_branch(cwd=wt, branch="feat-tracked", set_upstream=False)
    _delete_on_origin(origin=origin, branch="feat-tracked")

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(wt) in reaped
    assert not wt.exists()


def test_skips_dirty_worktree(*, tmp_path: Path) -> None:
    """A worktree with uncommitted changes is SKIPPED even when its branch is done."""
    module = _load_module()
    primary, origin = _init_primary_with_origin(tmp_path=tmp_path)
    wt = _add_worktree(primary=primary, name="wt-dirty", branch="feat-dirty")
    _make_branch_done(primary=primary, push_from=wt, origin=origin, branch="feat-dirty")
    _ = (wt / "dirty.txt").write_text("uncommitted\n", encoding="utf-8")

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(wt) not in reaped
    assert wt.is_dir()


def test_skips_worktree_whose_remote_branch_exists(*, tmp_path: Path) -> None:
    """A worktree whose branch is still present on origin is SKIPPED (not done)."""
    module = _load_module()
    primary, _origin = _init_primary_with_origin(tmp_path=tmp_path)
    wt = _add_worktree(primary=primary, name="wt-live", branch="feat-live")
    _ = _git(cwd=wt, args=["commit", "-q", "--allow-empty", "-m", "wip"])
    _ = _git(cwd=wt, args=["push", "-q", "origin", "feat-live"])

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(wt) not in reaped
    assert wt.is_dir()


def test_skips_live_locked_worktree(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A worktree locked by a LIVE pid is SKIPPED even when its branch is done."""
    module = _load_module()
    primary, origin = _init_primary_with_origin(tmp_path=tmp_path)
    wt = _add_worktree(primary=primary, name="wt-locked", branch="feat-locked")
    _make_branch_done(primary=primary, push_from=wt, origin=origin, branch="feat-locked")
    _ = _git(cwd=primary, args=["worktree", "lock", str(wt), "--reason", "session (pid 4242)"])

    # Treat pid 4242 as alive -> reaper must skip.
    def _alive_4242(*, pid: int) -> bool:
        return pid == 4242

    monkeypatch.setattr(module, "_pid_is_alive", _alive_4242)

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(wt) not in reaped
    assert wt.is_dir()


def test_dead_locked_worktree_is_unlocked_and_reaped(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A done-branch worktree locked by a DEAD pid is unlocked and reaped."""
    module = _load_module()
    primary, origin = _init_primary_with_origin(tmp_path=tmp_path)
    wt = _add_worktree(primary=primary, name="wt-deadlock", branch="feat-deadlock")
    _make_branch_done(primary=primary, push_from=wt, origin=origin, branch="feat-deadlock")
    _ = _git(cwd=primary, args=["worktree", "lock", str(wt), "--reason", "session (pid 4242)"])

    # No pid is alive -> dead lock -> unlock + reap.
    def _never_alive(*, pid: int) -> bool:
        return pid < 0

    monkeypatch.setattr(module, "_pid_is_alive", _never_alive)

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(wt) in reaped
    assert not wt.exists()


def test_locked_without_pid_is_treated_as_live_and_skipped(*, tmp_path: Path) -> None:
    """A lock whose reason carries no parseable pid is treated as LIVE and SKIPPED."""
    module = _load_module()
    primary, origin = _init_primary_with_origin(tmp_path=tmp_path)
    wt = _add_worktree(primary=primary, name="wt-nopid", branch="feat-nopid")
    _make_branch_done(primary=primary, push_from=wt, origin=origin, branch="feat-nopid")
    _ = _git(cwd=primary, args=["worktree", "lock", str(wt), "--reason", "manual hold"])

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(wt) not in reaped
    assert wt.is_dir()


def test_never_reaps_primary(*, tmp_path: Path) -> None:
    """The primary worktree is never reaped even alongside an actively-reaped secondary.

    The primary sits on a branch (`work`) carrying the full "done"
    signal — pushed with upstream, then remote-deleted — the same
    signal that marks a secondary reapable, proving the primary is
    excluded by the is-primary guard alone. A reapable secondary is
    reaped in the same pass to show reaping is live.
    """
    module = _load_module()
    primary, origin = _init_primary_with_origin(tmp_path=tmp_path)
    # Move the primary onto a pushed-then-remote-deleted branch.
    _ = _git(cwd=primary, args=["checkout", "-q", "-b", "work"])
    _make_branch_done(primary=primary, push_from=primary, origin=origin, branch="work")
    secondary = _add_worktree(primary=primary, name="wt-sec", branch="feat-sec")
    _make_branch_done(primary=primary, push_from=secondary, origin=origin, branch="feat-sec")

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(primary) not in reaped
    assert primary.is_dir()
    assert str(secondary) in reaped
    assert not secondary.exists()


def test_dry_run_mutates_nothing(*, tmp_path: Path) -> None:
    """`dry_run=True` reports the would-reap set but removes no worktree and deletes no branch."""
    module = _load_module()
    primary, origin = _init_primary_with_origin(tmp_path=tmp_path)
    wt = _add_worktree(primary=primary, name="wt-dry", branch="feat-dry")
    _make_branch_done(primary=primary, push_from=wt, origin=origin, branch="feat-dry")

    reaped = module.reap_worktrees(repo=primary, dry_run=True)

    assert str(wt) in reaped
    assert wt.is_dir()
    branches = _git(cwd=primary, args=["branch", "--list", "feat-dry"]).stdout
    assert branches.strip() != ""


def test_skips_when_ls_remote_errors(*, tmp_path: Path) -> None:
    """When `git ls-remote origin` errors (unreachable origin), the worktree is SKIPPED.

    A failing ls-remote means done-ness is UNDETERMINED; the safe
    default is to skip rather than reap on an ambiguous signal. The
    branch carries upstream config (the "was pushed" evidence) so
    the skip is attributable to the ls-remote error, not to the
    never-pushed guard.
    """
    module = _load_module()
    primary = tmp_path / "no-origin"
    _ = _git(cwd=tmp_path, args=["init", "-q", "-b", "master", str(primary)])
    _ = _git(cwd=primary, args=["config", "user.email", "t@example.com"])
    _ = _git(cwd=primary, args=["config", "user.name", "Test"])
    _ = _git(cwd=primary, args=["commit", "-q", "--allow-empty", "-m", "init"])
    _ = _git(cwd=primary, args=["remote", "add", "origin", str(tmp_path / "missing-origin.git")])
    wt = _add_worktree(primary=primary, name="wt-noremote", branch="feat-noremote")
    _ = _git(cwd=primary, args=["config", "branch.feat-noremote.remote", "origin"])
    _ = _git(cwd=primary, args=["config", "branch.feat-noremote.merge", "refs/heads/feat-noremote"])

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(wt) not in reaped
    assert wt.is_dir()


def test_main_dry_run_against_repo_returns_zero(*, tmp_path: Path) -> None:
    """`main(['--repo', <path>, '--dry-run'])` exits 0 and mutates nothing."""
    module = _load_module()
    primary, _origin = _init_primary_with_origin(tmp_path=tmp_path)
    wt = _add_worktree(primary=primary, name="wt-main", branch="feat-main")

    rc = module.main(argv=["--repo", str(primary), "--dry-run"])

    assert rc == 0
    assert wt.is_dir()


def test_main_resolves_bare_repo_name_against_workspace_parent(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--repo <name>` resolves to a sibling repo of the current checkout."""
    module = _load_module()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    justfile_repo = workspace / "livespec"
    justfile_repo.mkdir()
    primary, _origin = _init_primary_with_origin(tmp_path=workspace)
    target = workspace / "sibling-repo"
    primary.rename(target)
    wt = _add_worktree(primary=target, name="wt-sibling", branch="feat-sibling")
    monkeypatch.chdir(justfile_repo)

    rc = module.main(argv=["--repo", target.name, "--dry-run"])

    assert rc == 0
    assert wt.is_dir()


def test_main_defaults_repo_to_cwd(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`main([])` defaults `--repo` to the current working directory."""
    module = _load_module()
    primary, _origin = _init_primary_with_origin(tmp_path=tmp_path)
    monkeypatch.chdir(primary)

    rc = module.main(argv=["--dry-run"])

    assert rc == 0


def test_main_prunes_dead_project_scope_plugin_entries_and_backs_up_registry(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The end-of-run plugin sweep removes only project entries whose paths are gone.

    The registry is synthetic under a temp HOME so the test never
    reads or writes the real `~/.claude/plugins/installed_plugins.json`.
    """
    module = _load_module()
    primary, _origin = _init_primary_with_origin(tmp_path=tmp_path)
    home = tmp_path / "home"
    registry = home / ".claude" / "plugins" / "installed_plugins.json"
    registry.parent.mkdir(parents=True)
    live_project = tmp_path / "live-project"
    live_project.mkdir()
    missing_project = tmp_path / "missing-project"
    registry.write_text(
        json.dumps(
            {
                "version": 2,
                "plugins": {
                    "livespec@livespec": [
                        {"scope": "project", "projectPath": str(missing_project), "enabled": True},
                        {"scope": "project", "projectPath": str(live_project), "enabled": True},
                        {"scope": "user", "enabled": True},
                    ],
                    "other@marketplace": [
                        {"scope": "project", "enabled": True},
                    ],
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(home))

    rc = module.main(argv=["--repo", str(primary)])

    assert rc == 0
    pruned = json.loads(registry.read_text(encoding="utf-8"))
    assert pruned == {
        "version": 2,
        "plugins": {
            "livespec@livespec": [
                {"scope": "project", "projectPath": str(live_project), "enabled": True},
                {"scope": "user", "enabled": True},
            ],
            "other@marketplace": [
                {"scope": "project", "enabled": True},
            ],
        },
    }
    backups = sorted(registry.parent.glob("installed_plugins.json.*.bak"))
    assert len(backups) == 1
    backed_up = json.loads(backups[0].read_text(encoding="utf-8"))
    assert backed_up["plugins"]["livespec@livespec"][0]["projectPath"] == str(missing_project)


def test_reaps_clean_merged_worktree(*, tmp_path: Path) -> None:
    """A clean worktree whose HEAD is an ancestor of `origin/HEAD` IS reaped.

    This is the clean+merged expansion the old reaper MISSED: it required
    the remote branch to be GONE, so a merged branch whose remote head
    still exists was skipped. The new detection seam flags it via the
    ancestor-of-`origin/HEAD` signal. The branch is pushed (so the
    action-layer never-pushed guard passes) and its remote head is left
    in place, proving it is the merged signal — not the rebase-merge
    remote-gone signal — that reaps it.
    """
    module = _load_module()
    primary, _origin = _init_primary_with_origin(tmp_path=tmp_path)
    _set_origin_head(primary=primary)
    wt = _add_worktree(primary=primary, name="wt-merged", branch="feat-merged")
    # HEAD == master == origin/master (no new commits): an ancestor of
    # origin/HEAD. Push with upstream but leave the remote branch present.
    _push_branch(cwd=wt, branch="feat-merged", set_upstream=True)
    remote_heads = _git(cwd=primary, args=["ls-remote", "--heads", "origin", "feat-merged"]).stdout
    assert remote_heads.strip() != ""  # remote branch is still present

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(wt) in reaped
    assert not wt.exists()
    branches = _git(cwd=primary, args=["branch", "--list", "feat-merged"]).stdout
    assert branches.strip() == ""


def test_reaps_clean_merged_detached_worktree(*, tmp_path: Path) -> None:
    """A clean DETACHED worktree whose HEAD is merged IS reaped (no branch delete).

    The detection seam flags a clean detached worktree when its HEAD is an
    ancestor of `origin/HEAD`; the action layer removes it with no branch
    delete (a detached worktree carries no branch).
    """
    module = _load_module()
    primary, _origin = _init_primary_with_origin(tmp_path=tmp_path)
    _set_origin_head(primary=primary)
    wt = primary.parent / "wt-detached-merged"
    head = _git(cwd=primary, args=["rev-parse", "HEAD"]).stdout.strip()
    _ = _git(cwd=primary, args=["worktree", "add", "-q", "--detach", str(wt), head])

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(wt) in reaped
    assert not wt.exists()


def test_reaps_prunable_worktree(*, tmp_path: Path) -> None:
    """A prunable worktree (its working directory deleted) is pruned.

    Deleting the worktree's directory out from under git makes
    `git worktree list --porcelain` mark it `prunable`. The detection
    seam flags it and the action layer cleans its stale administrative
    entry via `git worktree prune` (there is no directory to `remove`).
    """
    module = _load_module()
    primary, _origin = _init_primary_with_origin(tmp_path=tmp_path)
    wt = _add_worktree(primary=primary, name="wt-prunable", branch="feat-prunable")
    shutil.rmtree(wt)

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(wt) in reaped
    listing = _git(cwd=primary, args=["worktree", "list", "--porcelain"]).stdout
    assert str(wt) not in listing


def test_skips_current_working_directory(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The worktree the process is standing in is SKIPPED even when reapable.

    The detection seam excludes only the primary checkout, so the current
    worktree can surface as a candidate; the action layer must never
    remove the ground the process stands on.
    """
    module = _load_module()
    primary, origin = _init_primary_with_origin(tmp_path=tmp_path)
    wt = _add_worktree(primary=primary, name="wt-cwd", branch="feat-cwd")
    _make_branch_done(primary=primary, push_from=wt, origin=origin, branch="feat-cwd")
    monkeypatch.chdir(wt)

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(wt) not in reaped
    assert wt.is_dir()


def test_skips_clean_merged_never_pushed_worktree(*, tmp_path: Path) -> None:
    """A clean NEVER-PUSHED worktree at `origin/HEAD` is SKIPPED by the action guard.

    With `refs/remotes/origin/HEAD` set, a fresh clean worktree at master
    is a trivial ancestor of `origin/HEAD`, so the detection seam flags it
    as merged. It is nonetheless a dispatched agent's in-progress work
    (never pushed), so the reaper's action-layer never-pushed guard skips
    it — protecting live work the trivial merged signal would otherwise
    reap.
    """
    module = _load_module()
    primary, _origin = _init_primary_with_origin(tmp_path=tmp_path)
    _set_origin_head(primary=primary)
    wt = _add_worktree(primary=primary, name="wt-fresh", branch="feat-fresh")

    reaped = module.reap_worktrees(repo=primary, dry_run=False)

    assert str(wt) not in reaped
    assert wt.is_dir()
    branches = _git(cwd=primary, args=["branch", "--list", "feat-fresh"]).stdout
    assert branches.strip() != ""
