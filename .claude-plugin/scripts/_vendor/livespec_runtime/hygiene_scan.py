"""Git-level hygiene scanner normalized to attention items."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TextIO, cast

from livespec_runtime.attention_item import AttentionItem
from livespec_runtime.needs_attention import HygieneScanFinding, compose_needs_attention

__all__: list[str] = [
    "CommandResult",
    "GitWorktree",
    "detect_stale_worktrees",
    "main",
    "run",
    "scan_hygiene",
    "stale_worktree_findings",
]

_DEFAULT_STALE_DAYS = 30
_GH_PR_FIELDS = "number,headRefName,updatedAt,title,url"
CommandRunner = Callable[..., "CommandResult"]


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandResult:
    """Captured command result for injectable git/gh reads."""

    stdout: str = ""
    stderr: str = ""
    returncode: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class GitWorktree:
    """Parsed `git worktree list --porcelain` record."""

    path: Path
    head: str | None = None
    branch: str | None = None
    detached: bool = False
    prunable_reason: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _ScanContext:
    repo_path: Path
    repo_name: str
    primary_path: Path
    current_path: Path
    base_ref: str
    default_branch: str
    now: datetime
    stale_after: timedelta
    runner: CommandRunner


def scan_hygiene(
    *,
    repo_path: Path,
    repo_name: str | None = None,
    now: datetime | None = None,
    stale_days: int = _DEFAULT_STALE_DAYS,
    include_prs: bool = True,
    runner: CommandRunner | None = None,
) -> list[AttentionItem]:
    """Return current repo hygiene findings as normalized attention items."""
    context = _build_context(
        repo_path=repo_path,
        repo_name=repo_name,
        now=now,
        stale_days=stale_days,
        runner=runner or _run_command,
    )
    findings = [
        *stale_worktree_findings(context=context),
        *_primary_health_findings(context=context),
        *_stale_branch_findings(context=context),
    ]
    if include_prs:
        findings.extend(_stale_pr_findings(context=context))
    return compose_needs_attention(repo=context.repo_name, hygiene_scan=findings)


def stale_worktree_findings(*, context: _ScanContext) -> list[HygieneScanFinding]:
    """Detect worktrees the reaper can prune/remove without force."""
    findings: list[HygieneScanFinding] = []
    for worktree in _worktrees(context=context):
        if worktree.path in (context.primary_path, context.current_path):
            continue
        finding = _stale_worktree_finding(context=context, worktree=worktree)
        if finding is not None:
            findings.append(finding)
    return findings


def detect_stale_worktrees(
    *,
    repo_path: Path,
    runner: CommandRunner | None = None,
) -> list[GitWorktree]:
    """Return the stale worktree CANDIDATE set for `repo_path`.

    This is the shared DETECTION seam a cross-repo reaper consumes.
    Unlike `scan_hygiene`, it runs ONLY the stale-worktree predicate —
    never the primary-health, stale-branch, or stale-PR findings — and
    it does not require the caller to build the private `_ScanContext`.

    A candidate is a NON-PRIMARY worktree that is safe to remove by ANY
    of three signals (a true SUPERSET of "safe to remove"):

      * prunable — its gitdir is gone (the `prunable` marker in
        `git worktree list --porcelain`);
      * clean AND its HEAD is an ancestor of `origin/HEAD` — a normal
        fast-forward / merge-commit merge;
      * clean AND its branch was pushed (upstream config or a
        remote-tracking ref) AND its origin branch is now gone
        (`git ls-remote --heads origin <branch>` empty) — the
        rebase-merge orphan signal this fleet needs, since rebase
        rewrites SHAs so a rebase-merged HEAD is not a literal ancestor
        of `origin/HEAD`. If `ls-remote` errors (no origin, network
        failure) done-ness is UNDETERMINED and the worktree is NOT a
        candidate (conservative, matching the reaper).

    The returned records are `GitWorktree`s (path, head, branch,
    detached, prunable_reason) in `git worktree list` order.

    Detection vs. action boundary: this returns the CANDIDATE set and
    EXCLUDES only the primary checkout. It deliberately does NOT apply
    the reaper's action-layer safety — no live-process-lock skip, no
    current-working-directory skip, no detached-HEAD skip. Detection
    answers "is this worktree safe to remove?"; the consuming reaper
    layers "should I remove it right now, from where I stand?" on top.
    """
    context = _build_context(
        repo_path=repo_path,
        repo_name=None,
        now=None,
        stale_days=_DEFAULT_STALE_DAYS,
        runner=runner or _run_command,
    )
    candidates: list[GitWorktree] = []
    for worktree in _worktrees(context=context):
        if worktree.path == context.primary_path:
            continue
        if _stale_worktree_finding(context=context, worktree=worktree) is not None:
            candidates.append(worktree)
    return candidates


def _build_context(
    *,
    repo_path: Path,
    repo_name: str | None,
    now: datetime | None,
    stale_days: int,
    runner: CommandRunner,
) -> _ScanContext:
    worktrees = _parse_worktrees(
        output=_git(
            repo_path=repo_path,
            argv=["worktree", "list", "--porcelain"],
            runner=runner,
        ).stdout
    )
    primary_path = worktrees[0].path if worktrees else repo_path
    current_path = _git(repo_path=repo_path, argv=["rev-parse", "--show-toplevel"], runner=runner)
    current = Path(current_path.stdout.strip() or str(repo_path))
    base_ref = _origin_head(repo_path=primary_path, runner=runner)
    return _ScanContext(
        repo_path=repo_path,
        repo_name=repo_name or primary_path.name,
        primary_path=primary_path,
        current_path=current,
        base_ref=base_ref,
        default_branch=base_ref.removeprefix("origin/"),
        now=now or datetime.now(tz=timezone.utc),
        stale_after=timedelta(days=stale_days),
        runner=runner,
    )


def _origin_head(*, repo_path: Path, runner: CommandRunner) -> str:
    result = _git(
        repo_path=repo_path,
        argv=["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"],
        runner=runner,
    )
    ref = result.stdout.strip().removeprefix("refs/remotes/")
    return ref or "origin/HEAD"


def _worktrees(*, context: _ScanContext) -> list[GitWorktree]:
    return _parse_worktrees(
        output=_git(
            repo_path=context.primary_path,
            argv=["worktree", "list", "--porcelain"],
            runner=context.runner,
        ).stdout
    )


def _parse_worktrees(*, output: str) -> list[GitWorktree]:
    records: list[GitWorktree] = []
    current: dict[str, str | bool] = {}
    for line in output.splitlines():
        if line.startswith("worktree "):
            _append_worktree(records=records, payload=current)
            current = {"path": line.removeprefix("worktree ")}
        elif line.startswith("HEAD "):
            current["head"] = line.removeprefix("HEAD ")
        elif line.startswith("branch "):
            current["branch"] = line.removeprefix("branch ").removeprefix("refs/heads/")
        elif line == "detached":
            current["detached"] = True
        elif line.startswith("prunable"):
            reason = line.removeprefix("prunable").strip() or "gone"
            current["prunable_reason"] = reason
    _append_worktree(records=records, payload=current)
    return records


def _append_worktree(*, records: list[GitWorktree], payload: Mapping[str, str | bool]) -> None:
    raw_path = payload.get("path")
    if not isinstance(raw_path, str):
        return
    head = payload.get("head")
    branch = payload.get("branch")
    prunable_reason = payload.get("prunable_reason")
    records.append(
        GitWorktree(
            path=Path(raw_path),
            head=head if isinstance(head, str) else None,
            branch=branch if isinstance(branch, str) else None,
            detached=payload.get("detached") is True,
            prunable_reason=prunable_reason if isinstance(prunable_reason, str) else None,
        )
    )


def _stale_worktree_finding(
    *,
    context: _ScanContext,
    worktree: GitWorktree,
) -> HygieneScanFinding | None:
    label = str(worktree.path)
    if worktree.prunable_reason is not None:
        return HygieneScanFinding(
            type="stale-worktree",
            resource=label,
            path=label,
            summary=f"Prune stale worktree metadata for {label} ({worktree.prunable_reason}).",
            command=f"git -C {_quote(context.primary_path)} worktree prune -v",
        )
    if not _worktree_is_clean(worktree=worktree, runner=context.runner):
        return None
    remove_command = (
        f"git -C {_quote(context.primary_path)} worktree remove {_quote(worktree.path)}"
    )
    if _head_is_merged(context=context, head=worktree.head):
        return HygieneScanFinding(
            type="stale-worktree",
            resource=label,
            path=label,
            summary=f"Remove clean worktree {label}; its HEAD is merged into {context.base_ref}.",
            command=remove_command,
        )
    if _branch_was_rebase_merged(context=context, worktree=worktree):
        return HygieneScanFinding(
            type="stale-worktree",
            resource=label,
            path=label,
            summary=(
                f"Remove clean worktree {label}; its branch {worktree.branch} was pushed and "
                f"its origin branch is gone (rebase-merged, so its HEAD is not an ancestor of "
                f"{context.base_ref})."
            ),
            command=remove_command,
        )
    return None


def _branch_was_rebase_merged(*, context: _ScanContext, worktree: GitWorktree) -> bool:
    """Return True if `worktree`'s branch shows the rebase-merge orphan signal.

    The signal (ported faithfully from the core reaper's
    `dev-tooling/reap_stale_worktrees.py`) is: the branch carries local
    evidence of ever having been pushed AND its remote branch is now
    absent. This fleet merges by rebase, which rewrites SHAs, so a
    rebase-merged branch's HEAD is NOT a literal ancestor of
    `origin/HEAD` and the ancestor test (`_head_is_merged`) misses it.
    Pushed-then-remote-gone is the reliable substitute. A detached
    worktree (no branch) can never match.
    """
    branch = worktree.branch
    if branch is None:
        return False
    if not _branch_was_pushed(context=context, branch=branch):
        return False
    return _branch_is_done(context=context, branch=branch)


def _branch_was_pushed(*, context: _ScanContext, branch: str) -> bool:
    """Return True if `branch` carries local evidence of ever having been pushed.

    Either signal suffices: upstream config (`branch.<name>.merge`,
    written by `git push -u` and surviving `fetch --prune`) or a
    remote-tracking ref (`refs/remotes/origin/<name>`, written by a
    plain push and lingering until `fetch --prune`). A branch with
    NEITHER signal was never pushed — its worktree is in-progress work,
    not a rebase-merged orphan.
    """
    upstream = _git(
        repo_path=context.primary_path,
        argv=["config", "--get", f"branch.{branch}.merge"],
        runner=context.runner,
    )
    if upstream.returncode == 0 and upstream.stdout.strip() != "":
        return True
    tracking = _git(
        repo_path=context.primary_path,
        argv=["rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
        runner=context.runner,
    )
    return tracking.returncode == 0


def _branch_is_done(*, context: _ScanContext, branch: str) -> bool:
    """Return True if `branch`'s remote head is ABSENT on origin.

    Pushed-then-remote-gone is the reliable rebase-merge signal (the
    remote branch is deleted on merge). If `git ls-remote` errors (no
    `origin`, network failure) done-ness is UNDETERMINED and this
    returns False so the caller never flags on an ambiguous signal.
    """
    result = _git(
        repo_path=context.primary_path,
        argv=["ls-remote", "--heads", "origin", branch],
        runner=context.runner,
    )
    if result.returncode != 0:
        return False
    return result.stdout.strip() == ""


def _worktree_is_clean(*, worktree: GitWorktree, runner: CommandRunner) -> bool:
    result = _git(repo_path=worktree.path, argv=["status", "--porcelain"], runner=runner)
    return result.returncode == 0 and result.stdout == ""


def _head_is_merged(*, context: _ScanContext, head: str | None) -> bool:
    if head is None:
        return False
    return (
        _git(
            repo_path=context.primary_path,
            argv=["merge-base", "--is-ancestor", head, context.base_ref],
            runner=context.runner,
        ).returncode
        == 0
    )


def _primary_health_findings(*, context: _ScanContext) -> list[HygieneScanFinding]:
    findings: list[HygieneScanFinding] = []
    primary = str(context.primary_path)
    status = _git(
        repo_path=context.primary_path,
        argv=["status", "--porcelain"],
        runner=context.runner,
    )
    if status.returncode == 0 and status.stdout != "":
        findings.append(
            HygieneScanFinding(
                type="primary-dirty",
                resource=primary,
                path=primary,
                summary=f"Primary checkout {primary} has uncommitted changes.",
                command=f"git -C {_quote(context.primary_path)} status --short",
                urgency="medium",
            )
        )
    branch_result = _git(
        repo_path=context.primary_path,
        argv=["symbolic-ref", "--quiet", "--short", "HEAD"],
        runner=context.runner,
    )
    branch = branch_result.stdout.strip()
    if branch_result.returncode != 0:
        findings.append(_primary_detached_finding(context=context))
    elif branch != context.default_branch:
        findings.append(_primary_off_default_finding(context=context, branch=branch))
    return findings


def _primary_detached_finding(*, context: _ScanContext) -> HygieneScanFinding:
    primary = str(context.primary_path)
    return HygieneScanFinding(
        type="primary-detached",
        resource=primary,
        path=primary,
        summary=f"Primary checkout {primary} is detached instead of on {context.default_branch}.",
        command=(
            f"git -C {_quote(context.primary_path)} "
            f"switch {shlex.quote(context.default_branch)}"
        ),
        urgency="medium",
    )


def _primary_off_default_finding(*, context: _ScanContext, branch: str) -> HygieneScanFinding:
    primary = str(context.primary_path)
    return HygieneScanFinding(
        type="primary-off-default",
        resource=primary,
        path=primary,
        summary=f"Primary checkout {primary} is on {branch}, expected {context.default_branch}.",
        command=(
            f"git -C {_quote(context.primary_path)} "
            f"switch {shlex.quote(context.default_branch)}"
        ),
        urgency="medium",
    )


def _stale_branch_findings(*, context: _ScanContext) -> list[HygieneScanFinding]:
    worktree_branches = frozenset(
        worktree.branch for worktree in _worktrees(context=context) if worktree.branch is not None
    )
    findings: list[HygieneScanFinding] = []
    result = _git(
        repo_path=context.primary_path,
        argv=["for-each-ref", "--format=%(refname:short)%00%(objectname)", "refs/heads"],
        runner=context.runner,
    )
    if result.returncode != 0:
        return findings
    for branch, head in _branch_rows(output=result.stdout):
        if branch == context.default_branch or branch in worktree_branches:
            continue
        if _head_is_merged(context=context, head=head):
            findings.append(_stale_branch_finding(context=context, branch=branch))
    return findings


def _branch_rows(*, output: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in output.splitlines():
        branch, separator, head = line.partition("\x00")
        if separator != "" and branch != "" and head != "":
            rows.append((branch, head))
    return rows


def _stale_branch_finding(*, context: _ScanContext, branch: str) -> HygieneScanFinding:
    ref = f"refs/heads/{branch}"
    return HygieneScanFinding(
        type="stale-branch",
        resource=ref,
        path=f".git/refs/heads/{branch}",
        summary=f"Delete local branch {branch}; it is merged into {context.base_ref}.",
        command=f"git -C {_quote(context.primary_path)} branch -d {shlex.quote(branch)}",
    )


def _stale_pr_findings(*, context: _ScanContext) -> list[HygieneScanFinding]:
    argv = ["pr", "list", "--state", "open", "--json", _GH_PR_FIELDS]
    origin = _git(
        repo_path=context.primary_path,
        argv=["config", "--get", "remote.origin.url"],
        runner=context.runner,
    ).stdout.strip()
    if origin != "":
        argv.extend(["--repo", origin])
    result = context.runner(argv=["gh", *argv], cwd=context.primary_path)
    if result.returncode != 0:
        return []
    try:
        payload: object = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    entries = cast(list[object], payload)
    return [finding for entry in entries for finding in _pr_finding(context=context, entry=entry)]


def _pr_finding(*, context: _ScanContext, entry: object) -> tuple[HygieneScanFinding, ...]:
    if not isinstance(entry, dict):
        return ()
    entry_map = cast(Mapping[str, object], entry)
    number = entry_map.get("number")
    updated_at = entry_map.get("updatedAt")
    if not isinstance(number, int) or not isinstance(updated_at, str):
        return ()
    updated = _parse_github_datetime(value=updated_at)
    if updated is None or context.now - updated <= context.stale_after:
        return ()
    title = entry_map.get("title")
    url = entry_map.get("url")
    head_ref = entry_map.get("headRefName")
    summary_title = title if isinstance(title, str) and title != "" else f"PR #{number}"
    branch = head_ref if isinstance(head_ref, str) and head_ref != "" else "unknown branch"
    path = url if isinstance(url, str) else ""
    return (
        HygieneScanFinding(
            type="stale-pr",
            resource=f"pr-{number}",
            path=path,
            summary=f"Open PR #{number} ({summary_title}) on {branch} has gone stale.",
            command=f"gh pr view {number} --web",
            urgency="medium",
        ),
    )


def _parse_github_datetime(*, value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _git(*, repo_path: Path, argv: list[str], runner: CommandRunner) -> CommandResult:
    return runner(argv=["git", "-C", str(repo_path), *argv], cwd=repo_path)


def _run_command(*, argv: list[str], cwd: Path) -> CommandResult:  # pragma: no cover
    completed = subprocess.run(
        argv,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(
        stdout=completed.stdout,
        stderr=completed.stderr,
        returncode=completed.returncode,
    )


def _quote(path: Path) -> str:
    return shlex.quote(str(path))


def main(
    *,
    argv: list[str],
    environ: Mapping[str, str],
    stdout: TextIO,
    stderr: TextIO,
    runner: CommandRunner | None = None,
) -> int:
    _ = environ
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.stale_days < 0:
        _ = stderr.write("hygiene-scan: --stale-days must be non-negative\n")
        return 2
    items = scan_hygiene(
        repo_path=args.repo,
        repo_name=args.repo_name,
        stale_days=args.stale_days,
        include_prs=not args.no_prs,
        runner=runner or _run_command,
    )
    _ = stdout.write(json.dumps([asdict(item) for item in items], sort_keys=True))
    _ = stdout.write("\n")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="livespec-hygiene-scan")
    _ = parser.add_argument("--repo", type=Path, default=Path.cwd())
    _ = parser.add_argument("--repo-name", type=str, default=None)
    _ = parser.add_argument("--stale-days", type=int, default=_DEFAULT_STALE_DAYS)
    _ = parser.add_argument("--no-prs", action="store_true", default=False)
    return parser


def run() -> int:  # pragma: no cover
    """Process entry: wire real process inputs and outputs."""
    return main(
        argv=sys.argv[1:],
        environ=os.environ,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


if __name__ == "__main__":
    raise SystemExit(run())
