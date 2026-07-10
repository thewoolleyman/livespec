"""Lock parsing helpers for reap_stale_worktrees."""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__: list[str] = ["_parse_locked_pid", "_parse_worktrees"]

_PID_PATTERN = re.compile(r"\(pid (\d+)\)")


@dataclass(frozen=True, kw_only=True)
class Worktree:
    """One entry from `git worktree list --porcelain`."""

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
    for record in porcelain.split("\n\n"):
        if not record.strip():
            continue
        path: str | None = None
        branch: str | None = None
        locked_reason: str | None = None
        for raw_line in record.splitlines():
            line = raw_line.rstrip("\n")
            if line.startswith("worktree "):
                path = line[len("worktree ") :]
            elif line.startswith("branch "):
                ref = line[len("branch ") :]
                branch = ref[len("refs/heads/") :] if ref.startswith("refs/heads/") else ref
            elif line.startswith("locked"):
                rest = line[len("locked") :].strip()
                locked_reason = rest
        if path is not None:
            worktrees.append(
                Worktree(
                    path=path,
                    branch=branch,
                    is_primary=len(worktrees) == 0,
                    locked_reason=locked_reason,
                )
            )
    return worktrees


def _parse_locked_pid(*, reason: str) -> int | None:
    """Extract the integer pid from a lock reason `(pid N)` token, else None."""
    match = _PID_PATTERN.search(reason)
    if match is None:
        return None
    return int(match.group(1))
