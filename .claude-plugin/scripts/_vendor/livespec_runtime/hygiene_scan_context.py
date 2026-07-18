"""Git context and command helpers for hygiene scanning."""

from __future__ import annotations

import shlex
import subprocess
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path

from livespec_runtime.hygiene_scan_types import (
    CommandResult,
    CommandRunner,
    GitWorktree,
    ScanContext,
)

__all__: list[str] = [
    "DEFAULT_STALE_DAYS",
    "build_context",
    "git",
    "parse_worktrees",
    "quote_path",
    "run_command",
    "worktrees",
]

DEFAULT_STALE_DAYS = 30


def build_context(
    *,
    repo_path: Path,
    repo_name: str | None,
    now: datetime | None,
    stale_days: int,
    runner: CommandRunner,
) -> ScanContext:
    parsed_worktrees = parse_worktrees(
        output=git(
            repo_path=repo_path,
            argv=["worktree", "list", "--porcelain"],
            runner=runner,
        ).stdout
    )
    primary_path = parsed_worktrees[0].path if parsed_worktrees else repo_path
    current_path = git(repo_path=repo_path, argv=["rev-parse", "--show-toplevel"], runner=runner)
    current = Path(current_path.stdout.strip() or str(repo_path))
    base_ref = origin_head(repo_path=primary_path, runner=runner)
    return ScanContext(
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


def origin_head(*, repo_path: Path, runner: CommandRunner) -> str:
    result = git(
        repo_path=repo_path,
        argv=["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"],
        runner=runner,
    )
    ref = result.stdout.strip().removeprefix("refs/remotes/")
    return ref or "origin/HEAD"


def worktrees(*, context: ScanContext) -> list[GitWorktree]:
    return parse_worktrees(
        output=git(
            repo_path=context.primary_path,
            argv=["worktree", "list", "--porcelain"],
            runner=context.runner,
        ).stdout
    )


def parse_worktrees(*, output: str) -> list[GitWorktree]:
    records: list[GitWorktree] = []
    current: dict[str, str | bool] = {}
    for line in output.splitlines():
        if line.startswith("worktree "):
            append_worktree(records=records, payload=current)
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
    append_worktree(records=records, payload=current)
    return records


def append_worktree(*, records: list[GitWorktree], payload: Mapping[str, str | bool]) -> None:
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


def git(*, repo_path: Path, argv: list[str], runner: CommandRunner) -> CommandResult:
    return runner(argv=["git", "-C", str(repo_path), *argv], cwd=repo_path)


def run_command(*, argv: list[str], cwd: Path) -> CommandResult:  # pragma: no cover
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


def quote_path(*, path: Path) -> str:
    return shlex.quote(str(path))
