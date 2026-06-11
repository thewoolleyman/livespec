# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. Per-call cast
# or refactor to named typed functions is the canonical fix; this file's
# railway composition pattern means roughly half of all lines are bind
# targets, so file-level silencing keeps the source readable. Non-railway
# code in this tree retains full enforcement (other modules do not carry
# this pragma). reportArgumentType is left ON so non-HKT firings still
# surface; HKT-related reportArgumentType call sites carry per-line
# ignore markers attached to the offending argument's line below.
"""Remote-head query helper for the git boundary facade.

Private sibling of `livespec.io.git` (the leading underscore marks
it as a helper module, exempt from the mirror-pairing test; its
behavior is exercised through the public `io.git.list_remote_branches`
re-export in `tests/livespec/io/test_git.py`). Extracted from
`git.py` so that file stays under the per-file LLOC ceiling per
`SPECIFICATION/constraints.md` §"File LLOC ceiling".

Holds `list_remote_branches`, the case (b) staleness signal for
the orchestrator-side worktree janitor: a secondary worktree whose
branch is absent from the remote head set is stale even when `git
branch --merged` is blind to it (a `gh pr merge --rebase` lands a
distinct SHA on default, so the merged branch is not a
default-ancestor).
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult

from livespec.errors import LivespecError, PreconditionError
from livespec.io.proc import run_subprocess

__all__: list[str] = ["list_remote_branches"]


_REFS_HEADS_PREFIX: str = "refs/heads/"


def list_remote_branches(
    *,
    project_root: Path,
) -> IOResult[tuple[str, ...], LivespecError]:
    """Return the short-names of every branch head on `origin`.

    Composes `git -C <project_root> ls-remote --heads origin`,
    which prints one `<object-id> TAB refs/heads/<branch>` line per
    remote head. The `refs/heads/` prefix is stripped (NOT split on
    `/`, since branch names embed slashes, e.g. `feature/foo`) to
    recover each short-name. The result is a tuple of remote-branch
    short-names in ls-remote's emit order.

    This is the case (b) signal for the doctor's no-stale-worktree
    invariant: a secondary worktree whose branch is NOT in this set
    is absent from the remote (the rebase-merged-then-deleted
    condition that `git branch --merged` never surfaces, because a
    `gh pr merge --rebase` lands a distinct SHA on default so the
    merged branch is not an ancestor).

    Network note: `ls-remote` is a NETWORK operation against the
    configured `origin`. The no-stale-worktree check assumes a
    reachable origin (a fetch already ran this session); when the
    remote query fails it lashes the failure into a `skipped`
    Finding, mirroring the other precondition gates.

    Failure modes lifted to IOFailure(PreconditionError):
      - `git ls-remote --heads origin` exits non-zero (no `origin`
        remote configured, network unreachable, auth failure). The
        doctor's no-stale-worktree check folds this into a `skipped`
        finding.
      - The `git` binary itself missing: lifts via the proc seam.
    """
    return run_subprocess(
        argv=[
            "git",
            "-C",
            str(project_root),
            "ls-remote",
            "--heads",
            "origin",
        ],
    ).bind(
        lambda completed: (  # pyright: ignore[reportArgumentType]
            IOResult.from_value(
                tuple(
                    line.split("\t", 1)[1].removeprefix(_REFS_HEADS_PREFIX)
                    for line in completed.stdout.splitlines()
                    if "\t" in line
                ),
            )
            if completed.returncode == 0
            else IOResult.from_failure(
                PreconditionError(
                    f"git.list_remote_branches: "
                    f"`git ls-remote --heads origin` exited "
                    f"{completed.returncode}",
                ),
            )
        ),
    )
