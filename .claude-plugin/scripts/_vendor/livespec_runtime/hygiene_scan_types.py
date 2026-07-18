"""Shared types for hygiene scanning."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

__all__: list[str] = [
    "CommandResult",
    "CommandRunner",
    "GitWorktree",
    "ScanContext",
]


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandResult:
    """Captured command result for injectable git/gh reads."""

    stdout: str = ""
    stderr: str = ""
    returncode: int = 0


CommandRunner = Callable[..., CommandResult]


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
