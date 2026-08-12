# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library, same rationale as the sibling
# `livespec.io.git`: bind chains lose flow-narrowing through pyright strict
# mode because returns uses KindN higher-kinded types pyright cannot unify
# with concrete IOResult.
"""Git reads describing a pull request's changed-file surface.

Extracted as a private sibling of `livespec.io.git` — the `_git_remote` /
`_git_worktrees` precedent — so the facade stays under its per-file LLOC
ceiling; the public seam remains `livespec.io.git`.

Both operations exist for the spec pull-request merge-policy gate, and both
report a git error as IOFailure rather than as empty output. That asymmetry is
the point: `SPECIFICATION/spec.md` `effective_spec_pr_merge` requires a git
error to resolve derivation FAILURE and never a KNOWN-EMPTY, and the embedded
shell these replace could only distinguish the two by checking `$?` separately
from the emptiness of `$(...)`.

Neither function spells the diff flags itself. The caller supplies them, so the
rename-detection rules that decided wrongly in production stay in the one place
`livespec.spec_governance.pr_merge_derivation` declares them.
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult

from livespec.errors import LivespecError, PreconditionError
from livespec.io.proc import run_subprocess

__all__: list[str] = ["diff_name_only", "merge_base"]


def merge_base(
    *,
    project_root: Path,
    base_ref: str,
    head_ref: str,
) -> IOResult[str, LivespecError]:
    """Return the merge-base commit of two refs.

    Composes `git -C <project_root> merge-base <base_ref> <head_ref>`. A
    non-zero exit lifts to IOFailure(PreconditionError): the caller cannot
    compute a real pull-request diff without it, and a shallow checkout is one
    documented way to reach that state.
    """
    return run_subprocess(
        argv=["git", "-C", str(project_root), "merge-base", base_ref, head_ref],
    ).bind(
        lambda completed: (  # pyright: ignore[reportArgumentType]
            IOResult.from_value(completed.stdout.strip())
            if completed.returncode == 0 and completed.stdout.strip()
            else IOResult.from_failure(
                PreconditionError(
                    f"git.merge_base: `git merge-base {base_ref} {head_ref}` exited "
                    f"{completed.returncode}",
                ),
            )
        ),
    )


def diff_name_only(
    *,
    project_root: Path,
    base_ref: str,
    head_ref: str,
    diff_args: tuple[str, ...],
    pathspec: str | None = None,
) -> IOResult[tuple[str, ...], LivespecError]:
    """Return the paths `git diff` reports between two refs, one per tuple entry.

    `diff_args` is passed through verbatim and MUST already carry
    `--name-only`; this facade adds no flags of its own, so a caller handing it
    `livespec.spec_governance.pr_merge_derivation.LOCAL_DIFF_ARGS` runs exactly
    the invocation that module's constant describes.

    `pathspec`, when given, is appended after a `--` separator so it is
    unambiguously a path even if it begins with a dash.

    Failure modes lifted to IOFailure(PreconditionError):
      - `git diff` exits non-zero (an unknown ref, a shallow checkout that
        cannot reach the base). Empty output after a ZERO exit is an ordinary
        empty tuple; only the non-zero exit is a failure.
      - The `git` binary itself missing: lifts via the proc seam.
    """
    pathspec_argv = [] if pathspec is None else ["--", pathspec]
    argv = [
        "git",
        "-C",
        str(project_root),
        "diff",
        *diff_args,
        base_ref,
        head_ref,
        *pathspec_argv,
    ]
    return run_subprocess(
        argv=argv
    ).bind(
        lambda completed: (  # pyright: ignore[reportArgumentType]
            IOResult.from_value(tuple(line for line in completed.stdout.splitlines() if line))
            if completed.returncode == 0
            else IOResult.from_failure(
                PreconditionError(
                    f"git.diff_name_only: `git diff {' '.join(diff_args)} {base_ref} "
                    f"{head_ref}` exited {completed.returncode}",
                ),
            )
        ),
    )
