"""reap_stale_worktrees — deterministic, idempotent reaper for merged worktrees.

Cross-repo dispatch (carried by the Beads/Dolt + Fabro Dispatcher since
the W6 dark-factory cutover) leaves self-managed worktrees + their
branches lingering after a sub-agent's PR rebase-merges. This tool is
the deterministic ACTION layer that mechanically cleans those orphans
up. It operates on ANY fleet repo path (`--repo <path>`).

DETECTION is delegated to the shared runtime seam
`livespec_runtime.hygiene_scan.detect_stale_worktrees(repo_path=...)`,
which returns the NON-PRIMARY stale-worktree CANDIDATE set — a SUPERSET
of "safe to remove" by any of three signals:

  - prunable (its gitdir is gone);
  - clean AND its HEAD is an ancestor of `origin/HEAD` (a normal
    fast-forward / merge-commit merge);
  - clean AND its branch was pushed AND its origin branch is now gone
    (the rebase-merge orphan signal — rebase rewrites SHAs so the HEAD
    is not a literal ancestor of `origin/HEAD`).

That seam is the SINGLE detection path: this reaper no longer carries
its own clean/pushed/done predicates. It EXCLUDES only the primary
checkout and applies NONE of the reaper's action-layer safety.

This module is that action layer. For each candidate it decides whether
to remove it RIGHT NOW, FROM WHERE THE PROCESS STANDS, by layering these
action-only safety skips on top of detection:

  - CURRENT-WORKING-DIRECTORY skip: the worktree the process is standing
    in is never removed (the seam excludes only the primary, so the
    current worktree can appear as a candidate).
  - DEFAULT-BRANCH skip: a candidate checked out ON the repo's default
    branch (`master`/`main`, resolved from `origin/HEAD`) is MAINLINE and
    is SKIPPED — a belt-and-suspenders guard so that even if detection
    ever regressed and flagged a default-branch worktree, the reaper
    never runs `git worktree remove` + `branch -D <default>` on it.
  - LIVE-PROCESS-LOCK skip: a locked worktree whose lock reason carries
    a `(pid N)` token for a LIVE pid is in use by another session and is
    SKIPPED. A stale (dead-pid) lock is unlocked, then reaped. A lock
    with no parseable pid is treated as LIVE (conservative) and SKIPPED.
  - NEVER-PUSHED skip: a non-prunable candidate whose branch carries NO
    local evidence of ever having been pushed is a dispatched agent's
    in-progress work (a fresh worktree at `origin/HEAD` is trivially
    "merged" but holds unlanded work). It is SKIPPED. The seam's own
    rebase-merge signal already requires pushed-ness; this guard
    additionally protects worktrees flagged ONLY by the trivial
    ancestor-of-`origin/HEAD` signal.
  - DETACHED / PRUNABLE handling: a candidate with no branch (detached)
    is removed without a branch delete; a prunable candidate is cleaned
    via `git worktree prune` (its working directory is already gone).

Safety + idempotency: the primary worktree is NEVER a candidate;
current, live-locked, and never-pushed worktrees are skipped.
`--dry-run` reports the would-reap set without mutating anything.

This is a maintainer/Dispatcher action tool, invoked via
`just reap-stale-worktrees repo=<path>` (NOT part of `just check` — it
is an action, not a check). Following the `dev-tooling/` house style it
is standalone: it shells out to git via its own `subprocess.run` calls
and does NOT import from `livespec/io/git.py`.

Output discipline: per spec, `print` (T20) and `sys.stderr.write`
(`check-no-write-direct`) are banned in dev-tooling/**. Diagnostics
flow through structlog (JSON to stderr); the vendored copy under
`.claude-plugin/scripts/_vendor/structlog` is added to `sys.path` at
module import time.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parent.parent / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

_DEV_TOOLING_DIR = Path(__file__).resolve().parent
if str(_DEV_TOOLING_DIR) not in sys.path:
    sys.path.insert(0, str(_DEV_TOOLING_DIR))

import structlog  # noqa: E402  — path-aware import after sys.path insert.
from claude_plugin_registry import prune_dead_project_plugin_entries  # noqa: E402
from livespec_runtime.hygiene_scan import (  # noqa: E402  — path-aware import after sys.path insert.
    GitWorktree,
    detect_stale_worktrees,
)
from reap_stale_worktrees_locks import _parse_locked_pid, _parse_worktrees  # noqa: E402

__all__: list[str] = ["main", "reap_worktrees"]


def _run_git(*, repo: Path, args: list[str], check: bool) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def _branch_was_pushed(*, repo: Path, branch: str) -> bool:
    """Return True if `branch` carries local evidence of ever having been pushed.

    Two signals, either sufficient:

      - upstream config (`branch.<name>.merge`), written by
        `git push -u` / `--set-upstream`; it persists after the
        remote branch is deleted and after `fetch --prune`;
      - a remote-tracking ref (`refs/remotes/origin/<name>`),
        written by a plain `git push origin <name>` (and by fetch)
        and lingering until `fetch --prune` removes it.

    This is the reaper's ACTION-layer never-pushed guard: a branch with
    NEITHER signal is local-only never-pushed work, so even when the
    detection seam flags its worktree (a fresh worktree at `origin/HEAD`
    is a trivial ancestor of `origin/HEAD`), the action layer treats it
    as a dispatched agent's in-progress work and SKIPS it.
    """
    upstream = _run_git(repo=repo, args=["config", "--get", f"branch.{branch}.merge"], check=False)
    if upstream.returncode == 0 and upstream.stdout.strip() != "":
        return True
    tracking = _run_git(
        repo=repo,
        args=["rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
        check=False,
    )
    return tracking.returncode == 0


def _resolve_default_branch(*, repo: Path) -> str | None:
    """Resolve `repo`'s default branch name from `refs/remotes/origin/HEAD`.

    Reads `git symbolic-ref refs/remotes/origin/HEAD` (e.g.
    `refs/remotes/origin/master`) and strips the `refs/remotes/origin/`
    prefix, yielding the short default-branch name (`master`/`main`).
    Returns None when `origin/HEAD` is unset (no origin, or a fresh clone
    that never resolved it), so the action-layer guard applies NO
    default-branch skip rather than guarding on a bogus name.
    """
    result = _run_git(
        repo=repo,
        args=["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"],
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip().removeprefix("refs/remotes/origin/")


def _candidate_on_default_branch(*, candidate: GitWorktree, default_branch: str | None) -> bool:
    """Return True if `candidate` is checked out ON the repo's default branch.

    A secondary worktree whose CURRENT BRANCH is the default branch
    (`master`/`main`) is MAINLINE, never a stale/merged feature branch, so
    it must NEVER be reaped — removing it runs `git worktree remove` +
    `branch -D <default>`, destroying a mainline worktree and its default
    branch. This is the action-layer belt-and-suspenders counterpart to the
    detection seam's own default-branch guard: even if detection ever
    regressed and surfaced such a worktree as a candidate, this skip stops
    the destructive removal. A detached worktree (`branch is None`) does not
    match — it holds no named branch to `branch -D`, so removing it is
    `git worktree remove` only. When the default branch is UNRESOLVED
    (`default_branch is None`) no candidate matches.
    """
    return (
        candidate.branch is not None
        and default_branch is not None
        and candidate.branch == default_branch
    )


def _pid_is_alive(*, pid: int) -> bool:
    """Return True if a process with `pid` currently exists."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


def _is_current_worktree(*, worktree_path: Path) -> bool:
    """Return True if the process cwd is at or inside `worktree_path`.

    The reaper must never remove the worktree it is standing in —
    removing it pulls the ground out from under the running process.
    `detect_stale_worktrees` deliberately excludes only the primary
    checkout and defers this current-directory guard to the action
    layer, so the current worktree CAN appear as a candidate.
    """
    return Path.cwd().resolve().is_relative_to(worktree_path.resolve())


def _lock_blocks_reap(
    *, locked_reason: str | None, path: str, log: structlog.stdlib.BoundLogger
) -> bool:
    """Return True if a worktree's live lock should block reaping."""
    if locked_reason is None:
        return False
    pid = _parse_locked_pid(reason=locked_reason)
    if pid is None:
        log.info(
            "worktree locked without parseable pid; treating as live",
            path=path,
            locked_reason=locked_reason,
        )
        return True
    if _pid_is_alive(pid=pid):
        log.info("worktree locked by live pid; skipping", path=path, pid=pid)
        return True
    log.info("worktree locked by dead pid; stale lock", path=path, pid=pid)
    return False


def _action_reapable(
    *,
    repo: Path,
    candidate: GitWorktree,
    default_branch: str | None,
    locked_reason: str | None,
    log: structlog.stdlib.BoundLogger,
) -> bool:
    """Return True if `candidate` should be reaped from where the process stands.

    Applies the action-layer safety the detection seam deliberately
    omits: the current-working-directory skip, the default-branch skip,
    the live-process-lock skip, and (for non-prunable candidates) the
    never-pushed skip. A prunable candidate is always reapable (its
    working directory is gone); a detached candidate with no branch is
    reapable when it survives the current/lock skips (the seam only flags
    a detached worktree when it is clean and its HEAD is merged).
    """
    path_str = str(candidate.path)
    if _is_current_worktree(worktree_path=candidate.path):
        log.info("worktree is the current working directory; skipping", path=path_str)
        return False
    if _candidate_on_default_branch(candidate=candidate, default_branch=default_branch):
        log.info(
            "worktree is checked out on the repo default branch; skipping "
            "(belt-and-suspenders guard: never `git worktree remove` + "
            "`branch -D <default>` a mainline worktree, even if detection regresses)",
            path=path_str,
            branch=candidate.branch,
        )
        return False
    if _lock_blocks_reap(locked_reason=locked_reason, path=path_str, log=log):
        return False
    if candidate.prunable_reason is not None:
        return True
    branch = candidate.branch
    if branch is not None and not _branch_was_pushed(repo=repo, branch=branch):
        log.info(
            "branch never pushed (no upstream config, no remote-tracking ref); "
            "in-progress work, skipping",
            path=path_str,
        )
        return False
    return True


def _remove_worktree(
    *,
    repo: Path,
    candidate: GitWorktree,
    locked_reason: str | None,
    log: structlog.stdlib.BoundLogger,
) -> None:
    """Remove `candidate`, delete its local branch (if any), and prune.

    A prunable candidate's working directory is already gone, so
    `git worktree remove` would refuse — `git worktree prune` cleans its
    stale administrative entry instead. For a live candidate, a stale
    (dead-pid) lock is unlocked first so `git worktree remove` does not
    refuse; the branch delete uses `-D` (force) because a rebase-merged
    branch is not fast-forward-merged into the local default and `-d`
    would refuse it. A detached candidate has no branch to delete.
    """
    path_str = str(candidate.path)
    if candidate.prunable_reason is not None:
        _ = _run_git(repo=repo, args=["worktree", "prune"], check=False)
        log.info("pruned stale worktree", path=path_str, prunable_reason=candidate.prunable_reason)
        return
    if locked_reason is not None:
        _ = _run_git(repo=repo, args=["worktree", "unlock", path_str], check=False)
    _ = _run_git(repo=repo, args=["worktree", "remove", "--force", path_str], check=True)
    if candidate.branch is not None:
        _ = _run_git(repo=repo, args=["branch", "-D", candidate.branch], check=False)
    _ = _run_git(repo=repo, args=["worktree", "prune"], check=False)
    log.info("reaped worktree", path=path_str, branch=candidate.branch)


def _resolve_repo_path(*, repo: Path) -> Path:
    """Resolve CLI repo paths using the justfile sibling-repo convention."""
    expanded = repo.expanduser()
    if expanded.is_absolute() or expanded.exists():
        return expanded.resolve()
    return (Path.cwd().parent / expanded).resolve(strict=False)


def reap_worktrees(*, repo: Path, dry_run: bool) -> list[str]:
    """Reap every action-reapable non-primary worktree in `repo`.

    Detection (which non-primary worktrees are stale candidates) is
    delegated to `detect_stale_worktrees`; this function layers the
    action-time safety skips on top and performs the removal. Returns
    the sorted list of worktree paths that were (or, under `dry_run`,
    WOULD be) reaped. Under `dry_run` no worktree is removed and no
    branch is deleted.
    """
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("reap_stale_worktrees")
    candidates = detect_stale_worktrees(repo_path=repo)
    default_branch = _resolve_default_branch(repo=repo)
    listing = _run_git(repo=repo, args=["worktree", "list", "--porcelain"], check=True)
    locked_by_path = {
        worktree.path: worktree.locked_reason
        for worktree in _parse_worktrees(porcelain=listing.stdout)
    }
    reaped: list[str] = []
    for candidate in candidates:
        locked_reason = locked_by_path.get(str(candidate.path))
        if not _action_reapable(
            repo=repo,
            candidate=candidate,
            default_branch=default_branch,
            locked_reason=locked_reason,
            log=log,
        ):
            continue
        if dry_run:
            log.info(
                "would reap worktree (dry-run)", path=str(candidate.path), branch=candidate.branch
            )
        else:
            _remove_worktree(repo=repo, candidate=candidate, locked_reason=locked_reason, log=log)
        reaped.append(str(candidate.path))
    return sorted(reaped)


def main(*, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reap_stale_worktrees", add_help=True)
    _ = parser.add_argument(
        "--repo",
        default=str(Path.cwd()),
        help="path to the target git repo (default: current working directory)",
    )
    _ = parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be reaped without removing anything",
    )
    namespace = parser.parse_args(argv)
    repo = _resolve_repo_path(repo=Path(str(namespace.repo)))
    dry_run = bool(namespace.dry_run)
    _ = reap_worktrees(repo=repo, dry_run=dry_run)
    _ = prune_dead_project_plugin_entries(dry_run=dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
