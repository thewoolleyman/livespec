# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
"""Git worktree parsing and listing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from returns.io import IOResult

from livespec.errors import LivespecError, PreconditionError
from livespec.io.proc import run_subprocess

__all__: list[str] = ["Worktree", "list_worktrees"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Worktree:
    """A single entry in `git worktree list --porcelain` output."""

    path: Path
    branch: str | None
    is_primary: bool


_REFS_HEADS_PREFIX: str = "refs/heads/"


def _parse_worktree_porcelain(*, text: str) -> tuple[Worktree, ...]:
    """Parse `git worktree list --porcelain` text into Worktree records.

    Porcelain format: records separated by blank lines; each
    record is a sequence of `<key> <value>` lines. The first
    record is the primary worktree (per `git-worktree(1)`); we
    set `is_primary=True` for it and `False` for the rest.
    Unrecognized record lines (`bare`, `detached`, `locked`,
    `prunable`, etc.) are tolerated — only `worktree` and
    `branch` lines influence the parsed value.
    """
    records: list[Worktree] = []
    current_path: Path | None = None
    current_branch: str | None = None
    blocks = text.split("\n\n")
    for index, block in enumerate(blocks):
        for line in block.splitlines():
            key, _sep, value = line.partition(" ")
            if key == "worktree":
                current_path = Path(value)
            elif key == "branch":
                current_branch = value.removeprefix(_REFS_HEADS_PREFIX)
        if current_path is not None:
            records.append(
                Worktree(
                    path=current_path,
                    branch=current_branch,
                    is_primary=(index == 0),
                ),
            )
        current_path = None
        current_branch = None
    return tuple(records)


def list_worktrees(
    *,
    project_root: Path,
) -> IOResult[tuple[Worktree, ...], LivespecError]:
    """Return the list of git worktrees attached to `project_root`'s repo.

    Composes `git -C <project_root> worktree list --porcelain`
    and parses the output into Worktree records. The first
    record is the primary worktree; subsequent records are
    secondary worktrees (the orchestrator-side janitor considers
    those for cleanup candidacy).

    Failure modes lifted to IOFailure(PreconditionError):
      - `git worktree list` exits non-zero (e.g., not a git
        working tree). The doctor folds this into a skipped
        finding.
      - The `git` binary itself missing: lifts via the proc seam.
    """
    return run_subprocess(
        argv=[
            "git",
            "-C",
            str(project_root),
            "worktree",
            "list",
            "--porcelain",
        ],
    ).bind(
        lambda completed: (  # pyright: ignore[reportArgumentType]
            IOResult.from_value(_parse_worktree_porcelain(text=completed.stdout))
            if completed.returncode == 0
            else IOResult.from_failure(
                PreconditionError(
                    f"git.list_worktrees: "
                    f"`git worktree list --porcelain` exited "
                    f"{completed.returncode}",
                ),
            )
        ),
    )
