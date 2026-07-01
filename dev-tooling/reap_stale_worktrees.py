"""reap_stale_worktrees — deterministic, idempotent reaper for merged worktrees.

The Layer 3 orchestrator (per `.claude/skills/livespec-orchestrate/
SKILL.md`) dispatches sub-agents into family repos with worktree
isolation. When a sub-agent's PR rebase-merges, the remote branch is
deleted but the local self-managed worktree + its branch linger. The
doctor `no-stale-worktree` check only WARNS (detection); this tool is
the deterministic ACTION layer the orchestrator runs to mechanically
clean those orphans up.

It operates on ANY family repo path (the orchestrator is livespec-
resident and reaps each repo by `--repo <path>`). For every NON-primary
worktree (per `git worktree list --porcelain`), it reaps the worktree
(`git worktree remove` + `git branch -D <branch>` + `git worktree
prune`) IF AND ONLY IF ALL of the following hold:

  - The branch was PUSHED at some point: it carries upstream config
    (`branch.<name>.merge`, written by `git push -u` and surviving
    `fetch --prune`) OR a remote-tracking ref
    (`refs/remotes/origin/<name>`, written by plain push/fetch and
    surviving until `fetch --prune`). A local-only branch with
    NEITHER signal was never pushed: its worktree is a dispatched
    agent's in-progress work, NOT an orphan, and is SKIPPED —
    remote-absence alone is ambiguous between "merged then deleted"
    and "not pushed yet".
  - The branch is "done": its remote branch is ABSENT
    (`git ls-remote --heads origin <branch>` succeeds with empty
    output). Pushed-then-remote-gone is the reliable rebase-merge
    signal. If `ls-remote` errors (no `origin`, network failure),
    done-ness is UNDETERMINED and the worktree is SKIPPED — never
    reaped on an ambiguous signal.
  - The working tree is CLEAN (`git status --porcelain` empty).
  - It is NOT held by a LIVE process lock. A locked worktree's reason
    string may carry a `(pid N)` token; if pid N is still alive the
    worktree is in use by another session and is SKIPPED. A stale
    (dead-pid) lock is unlocked, then the worktree is reaped. A lock
    whose reason carries no parseable pid is treated as LIVE
    (conservative) and SKIPPED.

Safety + idempotency: the primary worktree is NEVER touched;
never-pushed, dirty, remote-present, live-locked, and detached-HEAD
worktrees are skipped.
`--dry-run` reports the would-reap set without mutating anything.

This is a maintainer/orchestrator action tool, invoked via
`just reap-stale-worktrees repo=<path>` (NOT part of `just check` —
it is an action, not a check). Following the `dev-tooling/` house
style it is standalone: it shells out to git via its own
`subprocess.run` calls and does NOT import from `livespec/io/git.py`.

Output discipline: per spec, `print` (T20) and `sys.stderr.write`
(`check-no-write-direct`) are banned in dev-tooling/**. Diagnostics
flow through structlog (JSON to stderr); the vendored copy under
`.claude-plugin/scripts/_vendor/structlog` is added to `sys.path` at
module import time.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parent.parent / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = ["main", "reap_worktrees"]


_PID_PATTERN = re.compile(r"\(pid (\d+)\)")


@dataclass(frozen=True, kw_only=True)
class Worktree:
    """One entry from `git worktree list --porcelain`.

    `path` is the absolute worktree path; `branch` is the short
    branch name (None for a detached-HEAD worktree); `is_primary`
    is True for the first entry (the main working tree, which is
    never reaped); `locked_reason` is the lock reason string when
    the worktree is locked, else None.
    """

    path: str
    branch: str | None
    is_primary: bool
    locked_reason: str | None


def _parse_worktrees(*, porcelain: str) -> list[Worktree]:
    """Parse `git worktree list --porcelain` output into `Worktree` records.

    Records are separated by a blank line. The first record is the
    primary (main) worktree. Each record has a `worktree <path>`
    line, an optional `branch refs/heads/<name>` line (absent for
    detached HEAD), and an optional `locked [<reason>]` line.
    """
    worktrees: list[Worktree] = []
    path: str | None = None
    branch: str | None = None
    locked_reason: str | None = None
    is_first = True

    def _flush() -> None:
        nonlocal path, branch, locked_reason, is_first
        if path is not None:
            worktrees.append(
                Worktree(
                    path=path,
                    branch=branch,
                    is_primary=is_first,
                    locked_reason=locked_reason,
                )
            )
            is_first = False
        path = None
        branch = None
        locked_reason = None

    for raw_line in porcelain.splitlines():
        line = raw_line.rstrip("\n")
        if line == "":
            _flush()
            continue
        if line.startswith("worktree "):
            path = line[len("worktree ") :]
        elif line.startswith("branch "):
            ref = line[len("branch ") :]
            branch = ref[len("refs/heads/") :] if ref.startswith("refs/heads/") else ref
        elif line.startswith("locked"):
            rest = line[len("locked") :].strip()
            locked_reason = rest
    _flush()
    return worktrees


def _parse_locked_pid(*, reason: str) -> int | None:
    """Extract the integer pid from a lock reason `(pid N)` token, else None."""
    match = _PID_PATTERN.search(reason)
    if match is None:
        return None
    return int(match.group(1))


def _pid_is_alive(*, pid: int) -> bool:
    """Return True if a process with `pid` currently exists.

    Uses `os.kill(pid, 0)` which sends no signal but performs the
    existence + permission check. A `ProcessLookupError` means the
    pid is dead; a `PermissionError` means the process exists but
    is owned by another user (alive). Any other OSError is treated
    conservatively as "alive" so a live session is never reaped.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return True
    return True


def _run_git(*, repo: Path, args: list[str], check: bool) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def _resolve_repo_path(*, repo_arg: str, cwd: Path) -> Path:
    """Resolve CLI repo arguments to an absolute path.

    `just reap-stale-worktrees <repo>` runs from this repo's justfile
    directory, while `<repo>` commonly names a sibling checkout under
    the workspace root. `.` keeps its current-repo meaning; other
    relative repo names resolve against the workspace parent.
    """
    repo = Path(repo_arg).expanduser()
    if repo.is_absolute():
        return repo.resolve()
    if repo == Path():
        return cwd.resolve()
    return (cwd.parent / repo).resolve()


def _worktree_is_clean(*, worktree_path: str) -> bool:
    """Return True if the worktree has no uncommitted changes."""
    result = subprocess.run(
        ["git", "-C", worktree_path, "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False
    return result.stdout.strip() == ""


def _branch_was_pushed(*, repo: Path, branch: str) -> bool:
    """Return True if `branch` carries local evidence of ever having been pushed.

    Two signals, either sufficient:

      - upstream config (`branch.<name>.merge`), written by
        `git push -u` / `--set-upstream`; it persists after the
        remote branch is deleted and after `fetch --prune`;
      - a remote-tracking ref (`refs/remotes/origin/<name>`),
        written by a plain `git push origin <name>` (and by fetch)
        and lingering until `fetch --prune` removes it.

    A branch with NEITHER signal is local-only never-pushed work:
    its absence from origin means "not pushed yet", not "merged and
    remote-deleted", so the caller must treat the worktree as a
    dispatched agent's in-progress work rather than as a reapable
    orphan.
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


def _branch_is_done(*, repo: Path, branch: str) -> bool:
    """Return True if `branch`'s remote-tracking head is ABSENT on origin.

    Remote-gone is the reliable rebase-merge signal (the remote
    branch is deleted on merge) — but ONLY once `_branch_was_pushed`
    has established the branch ever reached origin; the caller gates
    on that first. If `git ls-remote` errors (no `origin`
    configured, network failure), done-ness is UNDETERMINED and this
    returns False so the caller skips the worktree rather than
    reaping on an ambiguous signal.
    """
    result = _run_git(repo=repo, args=["ls-remote", "--heads", "origin", branch], check=False)
    if result.returncode != 0:
        return False
    return result.stdout.strip() == ""


def _lock_blocks_reap(*, worktree: Worktree, log: structlog.stdlib.BoundLogger) -> bool:
    """Return True if `worktree`'s lock should block reaping (live lock).

    Unlocked -> does not block. Locked by a parseable LIVE pid ->
    blocks. Locked by a parseable DEAD pid -> does not block (the
    caller unlocks then reaps). Locked with no parseable pid ->
    treated as LIVE (conservative) -> blocks.
    """
    if worktree.locked_reason is None:
        return False
    pid = _parse_locked_pid(reason=worktree.locked_reason)
    if pid is None:
        log.info(
            "worktree locked without parseable pid; treating as live",
            path=worktree.path,
            locked_reason=worktree.locked_reason,
        )
        return True
    if _pid_is_alive(pid=pid):
        log.info(
            "worktree locked by live pid; skipping",
            path=worktree.path,
            pid=pid,
        )
        return True
    log.info(
        "worktree locked by dead pid; stale lock",
        path=worktree.path,
        pid=pid,
    )
    return False


def _remove_worktree(
    *, repo: Path, worktree: Worktree, branch: str, log: structlog.stdlib.BoundLogger
) -> None:
    """Remove `worktree`, delete its local `branch`, and prune.

    A stale (dead-pid) lock is unlocked first so `git worktree
    remove` does not refuse. The branch delete uses `-D` (force)
    because a rebase-merged branch is not fast-forward-merged into
    the local default and `-d` would refuse it. `branch` is passed
    in explicitly because the caller (`reap_worktrees`) only reaches
    this path once `_should_reap` has guaranteed `worktree.branch`
    is not None.
    """
    if worktree.locked_reason is not None:
        _ = _run_git(repo=repo, args=["worktree", "unlock", worktree.path], check=False)
    _ = _run_git(repo=repo, args=["worktree", "remove", "--force", worktree.path], check=True)
    _ = _run_git(repo=repo, args=["branch", "-D", branch], check=False)
    _ = _run_git(repo=repo, args=["worktree", "prune"], check=False)
    log.info("reaped worktree", path=worktree.path, branch=branch)


def _reapable_branch(
    *, repo: Path, worktree: Worktree, log: structlog.stdlib.BoundLogger
) -> str | None:
    """Return the branch name if `worktree` is reapable, else None.

    Returns None (skip) for the primary worktree, detached-HEAD
    worktrees, dirty worktrees, worktrees whose branch was never
    pushed (no upstream config, no remote-tracking ref — a
    dispatched agent's in-progress work), worktrees whose branch is
    not "done" (remote-present or undetermined), and live-locked
    worktrees. Returning the narrowed branch name lets the caller
    delete it without re-narrowing `str | None`.
    """
    if worktree.is_primary:
        return None
    branch = worktree.branch
    if branch is None:
        return None
    skip_reason: str | None = None
    if not _worktree_is_clean(worktree_path=worktree.path):
        skip_reason = "worktree dirty; skipping"
    elif not _branch_was_pushed(repo=repo, branch=branch):
        skip_reason = (
            "branch never pushed (no upstream config, no remote-tracking ref); "
            "in-progress work, skipping"
        )
    elif not _branch_is_done(repo=repo, branch=branch):
        skip_reason = "branch not done (remote present or undetermined); skipping"
    if skip_reason is not None:
        log.info(skip_reason, path=worktree.path)
        return None
    if _lock_blocks_reap(worktree=worktree, log=log):
        return None
    return branch


def reap_worktrees(*, repo: Path, dry_run: bool) -> list[str]:
    """Reap every reapable non-primary worktree in `repo`.

    Returns the sorted list of worktree paths that were (or, under
    `dry_run`, WOULD be) reaped. Under `dry_run` no worktree is
    removed and no branch is deleted.
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
    listing = _run_git(repo=repo, args=["worktree", "list", "--porcelain"], check=True)
    worktrees = _parse_worktrees(porcelain=listing.stdout)
    reaped: list[str] = []
    for worktree in worktrees:
        branch = _reapable_branch(repo=repo, worktree=worktree, log=log)
        if branch is None:
            continue
        if dry_run:
            log.info("would reap worktree (dry-run)", path=worktree.path, branch=branch)
        else:
            _remove_worktree(repo=repo, worktree=worktree, branch=branch, log=log)
        reaped.append(worktree.path)
    return sorted(reaped)


def main(*, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reap_stale_worktrees", add_help=True)
    _ = parser.add_argument(
        "--repo",
        default=".",
        help="path to the target git repo (default: current working directory)",
    )
    _ = parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be reaped without removing anything",
    )
    namespace = parser.parse_args(argv)
    repo = _resolve_repo_path(repo_arg=str(namespace.repo), cwd=Path.cwd())
    dry_run = bool(namespace.dry_run)
    _ = reap_worktrees(repo=repo, dry_run=dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
