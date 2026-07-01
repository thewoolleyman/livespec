"""Outside-in test for `dev-tooling/reap_stale_worktrees.py` — worktree reaper.

The reaper is the orchestrator-side janitor action (the doctor-side
detection-only `no-stale-worktree` check was retired at v105 —
cleanup discipline is Dispatcher territory). For every NON-primary worktree in a
target repo it removes the worktree + deletes its local branch +
prunes, IF AND ONLY IF the branch is "done" (it was PUSHED at some
point — upstream config or a remote-tracking ref survives as local
evidence — and the remote branch is now absent, the reliable
rebase-merge signal), the working tree is clean, and the worktree
is not held by a LIVE process lock. A local-only branch that was
NEVER pushed is a dispatched agent's in-progress work, not an
orphan: remote-absence alone must not reap it. The reaper is
idempotent and safe-by-default: it skips never-pushed, dirty,
remote-present, live-locked, and primary worktrees, and
`--dry-run` mutates nothing.

These tests construct real tmp git repos (with a local bare repo
standing in for `origin` so `git ls-remote` resolves without the
network) and exercise the reaper's importable helpers + its
filesystem-mutating reap path. PID-liveness is monkeypatched so a
"live lock" fixture is deterministic without spawning a real
process. No real network and no mutation against the live livespec
repo occurs.
"""

from __future__ import annotations

import importlib.util
import os
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


def test_worktree_is_clean_false_when_status_errors(*, tmp_path: Path) -> None:
    """`_worktree_is_clean` returns False when `git status` errors (non-git path).

    A non-zero status exit means cleanliness is undetermined; the
    conservative answer is "not clean" so the caller skips reaping.
    """
    module = _load_module()
    not_a_repo = tmp_path / "plain-dir"
    not_a_repo.mkdir()
    assert module._worktree_is_clean(worktree_path=str(not_a_repo)) is False  # noqa: SLF001


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


def test_main_resolves_relative_sibling_repo_from_justfile_dir(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`main` accepts a sibling repo name when invoked from the livespec checkout dir."""
    module = _load_module()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    justfile_dir = workspace / "livespec"
    justfile_dir.mkdir()
    primary, _origin = _init_primary_with_origin(tmp_path=workspace)
    sibling = workspace / "livespec-orchestrator-beads-fabro"
    primary.rename(sibling)
    monkeypatch.chdir(justfile_dir)

    rc = module.main(argv=["--repo", sibling.name, "--dry-run"])

    assert rc == 0


def test_main_defaults_repo_to_cwd(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`main([])` defaults `--repo` to the current working directory."""
    module = _load_module()
    primary, _origin = _init_primary_with_origin(tmp_path=tmp_path)
    monkeypatch.chdir(primary)

    rc = module.main(argv=["--dry-run"])

    assert rc == 0
