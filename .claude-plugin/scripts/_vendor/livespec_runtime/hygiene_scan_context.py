"""Git context and command helpers for hygiene scanning.

`run_command` is the subsystem's ONE process-spawn boundary, and
`CommandRunner` is the protocol every reader here is written against, so
the two move together: changing the leaf's return type IS changing the
protocol, and a tree part-way through that change does not type-check.

The railway carries exactly one failure — the command could not be
SPAWNED. A non-zero EXIT is data (see `CommandUnavailable`).

`budgeted_gh_read` is the GitHub half of that same concern. The scan's
GitHub reads do not go to `gh` directly: they go through
`GithubBudgetedClient` over the SAME injected runner, so a scan run
against a budget near its floor declines its advisory reads instead of
spending the last of a budget interactive work needs.
"""

from __future__ import annotations

import shlex
import subprocess
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path

from returns.io import IOFailure, IOResult, IOSuccess
from returns.unsafe import unsafe_perform_io

from livespec_runtime.github_budget import (
    GhInvocation,
    GithubBudgetedClient,
    gh_invocation,
    gh_transport,
)
from livespec_runtime.hygiene_scan_types import (
    CommandResult,
    CommandRunner,
    CommandUnavailable,
    GitWorktree,
    ScanContext,
)

__all__: list[str] = [
    "DEFAULT_STALE_DAYS",
    "GH_READ_BUDGET_FLOOR",
    "budgeted_gh_read",
    "build_context",
    "git",
    "parse_worktrees",
    "quote_path",
    "run_command",
    "worktrees",
]

DEFAULT_STALE_DAYS = 30

# Requests held back for work a human is waiting on. The scan is a
# janitor: its findings keep until the next run, and an interactive
# resolve walk's do not.
GH_READ_BUDGET_FLOOR = 250


def build_context(
    *,
    repo_path: Path,
    repo_name: str | None,
    now: datetime | None,
    stale_days: int,
    runner: CommandRunner,
) -> IOResult[ScanContext, CommandUnavailable]:
    """Resolve the shared git context, or name the command that could not run.

    Three reads, and none has a defensible default: a context assembled
    around a primary path or a base ref that was never read would send
    every downstream check against the wrong repository. So the first
    unspawnable command ends the assembly rather than being absorbed.
    """
    listed = git(repo_path=repo_path, argv=["worktree", "list", "--porcelain"], runner=runner)
    if isinstance(listed, IOFailure):
        return listed
    parsed_worktrees = parse_worktrees(output=unsafe_perform_io(listed.unwrap()).stdout)
    primary_path = parsed_worktrees[0].path if parsed_worktrees else repo_path
    toplevel = git(repo_path=repo_path, argv=["rev-parse", "--show-toplevel"], runner=runner)
    if isinstance(toplevel, IOFailure):
        return toplevel
    current = Path(unsafe_perform_io(toplevel.unwrap()).stdout.strip() or str(repo_path))
    based = origin_head(repo_path=primary_path, runner=runner)
    if isinstance(based, IOFailure):
        return based
    base_ref = unsafe_perform_io(based.unwrap())
    return IOSuccess(
        ScanContext(
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
    )


def origin_head(*, repo_path: Path, runner: CommandRunner) -> IOResult[str, CommandUnavailable]:
    """The `origin/HEAD` ref, defaulting only when git ANSWERED and had none."""
    return git(
        repo_path=repo_path,
        argv=["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"],
        runner=runner,
    ).map(lambda result: result.stdout.strip().removeprefix("refs/remotes/") or "origin/HEAD")


def worktrees(*, context: ScanContext) -> IOResult[list[GitWorktree], CommandUnavailable]:
    return git(
        repo_path=context.primary_path,
        argv=["worktree", "list", "--porcelain"],
        runner=context.runner,
    ).map(lambda result: parse_worktrees(output=result.stdout))


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


def git(
    *, repo_path: Path, argv: list[str], runner: CommandRunner
) -> IOResult[CommandResult, CommandUnavailable]:
    return runner(argv=["git", "-C", str(repo_path), *argv], cwd=repo_path)


def run_command(*, argv: list[str], cwd: Path) -> IOResult[CommandResult, CommandUnavailable]:
    """Spawn `argv` in `cwd`, or name the command that could not be spawned.

    The failure track is narrow and STRUCTURAL — `subprocess.run` itself
    raising, which means the binary is missing or `cwd` is gone. What a
    given exit code MEANS is each reader's own policy, one layer up, so
    the exit code rides the success track untouched.
    """
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as unusable:
        return IOFailure(CommandUnavailable(argv=shlex.join(argv), detail=str(unusable)))
    return IOSuccess(
        CommandResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
        )
    )


def quote_path(*, path: Path) -> str:
    return shlex.quote(str(path))


def _gh_invoked(*, argv: list[str], context: ScanContext) -> GhInvocation:
    """One command run through the scan's injected runner, as a `gh` outcome.

    The two vocabularies line up exactly, which is why this is an
    adaptation and not a re-implementation: `CommandUnavailable` means
    the command could not be SPAWNED, and that is precisely what
    `GhInvocation.unspawnable` records.
    """
    outcome = context.runner(argv=argv, cwd=context.primary_path)
    if isinstance(outcome, IOFailure):
        return GhInvocation(
            argv=shlex.join(argv),
            unspawnable=unsafe_perform_io(outcome.failure()).detail,
        )
    result = unsafe_perform_io(outcome.unwrap())
    return GhInvocation(
        argv=shlex.join(argv),
        stdout=result.stdout,
        stderr=result.stderr,
        returncode=result.returncode,
    )


def budgeted_gh_read(*, context: ScanContext, resource: str) -> IOResult[str, CommandUnavailable]:
    """One budgeted GitHub read's stdout, or the command that could not be SPAWNED.

    `resource` is the shlex-joined `gh` argument tail; the transport
    builds the argv, so this subsystem names WHAT it wants to read and
    never HOW to invoke `gh`.

    The read is declared DEFERRABLE with a reserved floor. Below the
    floor the client refuses it outright, and that refusal, a non-zero
    exit, and an empty answer are the SAME thing to every reader here —
    nothing to report this pass — so all three yield an EMPTY string on
    the success track rather than three shapes the callers would each
    have to re-discriminate. Only a command that never ran takes the
    failure track, which is exactly the contract `CommandUnavailable`
    already documents.

    The client is per-call because the scan is: one pass reads once, so
    a cache that outlived the pass would answer a later scan from a
    reading it took a scan ago.
    """
    client = GithubBudgetedClient(
        transport=gh_transport(execute=partial(_gh_invoked, context=context)),
        max_attempts=1,
    )
    outcome = client.request(
        method="GET",
        resource=resource,
        deferrable=True,
        remaining_floor=GH_READ_BUDGET_FLOOR,
    )
    if isinstance(outcome, IOFailure):
        return IOSuccess("")
    invocation = gh_invocation(value=outcome.unwrap().value)
    if invocation.unspawnable is not None:
        return IOFailure(CommandUnavailable(argv=invocation.argv, detail=invocation.unspawnable))
    return IOSuccess(invocation.stdout if invocation.returncode == 0 else "")
