"""Shared types for hygiene scanning."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from returns.io import IOResult

__all__: list[str] = [
    "CommandResult",
    "CommandRunner",
    "CommandUnavailable",
    "GitWorktree",
    "ScanContext",
]


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandResult:
    """Captured command result for injectable git/gh reads."""

    stdout: str = ""
    stderr: str = ""
    returncode: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandUnavailable:
    """A command the hygiene scan depends on could not be SPAWNED.

    Deliberately NOT inhabited by "the command ran and exited non-zero".
    Every reader in this subsystem already branches on `returncode` — a
    `git symbolic-ref` that finds nothing, a `ls-remote` against a deleted
    branch — so those are ordinary ANSWERS and stay on the success track.
    Widening this to cover them would convert the scan's normal readings
    into errors.

    `argv` is the shell-quoted command so an operator can rerun it: the
    scan is invoked from janitors and hooks where a bare "a command
    failed" leaves nothing to act on.
    """

    argv: str
    detail: str


CommandRunner = Callable[..., IOResult[CommandResult, CommandUnavailable]]


@dataclass(frozen=True, slots=True, kw_only=True)
class GitWorktree:
    """Parsed `git worktree list --porcelain` record."""

    path: Path
    head: str | None = None
    branch: str | None = None
    detached: bool = False
    prunable_reason: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ScanContext:
    """Resolved git context shared by hygiene checks."""

    repo_path: Path
    repo_name: str
    primary_path: Path
    current_path: Path
    base_ref: str
    default_branch: str
    now: datetime
    stale_after: timedelta
    runner: CommandRunner
