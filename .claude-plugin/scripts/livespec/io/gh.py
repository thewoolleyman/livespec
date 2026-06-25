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
"""GitHub CLI boundary facade.

Per style doc: every operation that touches the gh CLI binary lives
here under the typed io seam so the
railway flows through `IOResult`. Mirrors the shape of
`livespec.io.git`: a happy-path single subprocess invocation; the
proc facade handles OSError → PreconditionError; non-zero exits
lift to a typed PreconditionError on the IOFailure track.

The gh facade exposes three operations for merged-PR/branch
introspection (originally pulled into existence by the retired
stale-cleanup doctor checks; cleanup discipline moved to the
orchestrator at v105, and these remain general-purpose reads):

  - `get_repo_name_with_owner` — resolves `<owner>/<name>` for the
    current repo via `gh repo view --json nameWithOwner`. Used to
    template the corrective-action narration that calls
    `gh api -X DELETE repos/<owner>/<name>/git/refs/heads/<branch>`.
  - `list_remote_branches` — enumerates every remote branch via
    `gh api -X GET 'repos/{owner}/{repo}/branches' --paginate`.
    gh substitutes the `{owner}`/`{repo}` placeholders against the
    local origin remote.
  - `list_merged_pull_request_head_refs` — enumerates the head
    branch names of merged PRs via `gh pr list --state merged`.
    Limit 1000 matches the gh default ceiling.

All three pass `cwd=project_root` to `run_subprocess` so gh
resolves the local origin remote regardless of the calling
process's actual cwd. The git facade pins scope via `git -C`; gh
lacks an equivalent flag, so cwd is the documented mechanism.
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult

from livespec.errors import LivespecError, PreconditionError
from livespec.io.proc import run_subprocess

__all__: list[str] = [
    "get_repo_name_with_owner",
    "list_merged_pull_request_head_refs",
    "list_remote_branches",
]


def get_repo_name_with_owner(
    *,
    project_root: Path,
) -> IOResult[str, LivespecError]:
    """Return the `<owner>/<name>` identity of the current repo per gh.

    Composes `gh repo view --json nameWithOwner --jq .nameWithOwner`
    with `cwd=project_root`. The result is the canonical
    `owner/name` string (e.g., `thewoolleyman/livespec`) that
    cleanup tooling templates into the
    `gh api -X DELETE repos/<owner>/<name>/git/refs/heads/<branch>`
    narration.

    Failure modes lifted to IOFailure(PreconditionError):
      - `gh repo view` exits non-zero (gh unauthenticated, no
        origin remote, network failure). The doctor folds this
        into a `skipped` finding.
      - Empty stdout after a zero exit (impossible in practice but
        guarded as a precondition failure to keep the consumer
        chain total).
      - The `gh` binary itself missing: lifts via the proc seam.
    """
    return run_subprocess(
        argv=[
            "gh",
            "repo",
            "view",
            "--json",
            "nameWithOwner",
            "--jq",
            ".nameWithOwner",
        ],
        cwd=project_root,
    ).bind(
        lambda completed: (  # pyright: ignore[reportArgumentType]
            IOResult.from_value(completed.stdout.strip())
            if completed.returncode == 0 and completed.stdout.strip()
            else IOResult.from_failure(
                PreconditionError(
                    f"gh.get_repo_name_with_owner: `gh repo view` exited "
                    f"{completed.returncode}; repo identity undetermined",
                ),
            )
        ),
    )


def list_remote_branches(
    *,
    project_root: Path,
) -> IOResult[tuple[str, ...], LivespecError]:
    """Return every remote branch name for the current repo per gh.

    Composes `gh api -X GET 'repos/{owner}/{repo}/branches'
    --paginate --jq '.[].name'` with `cwd=project_root`. The
    `{owner}` and `{repo}` placeholders are gh's documented
    auto-substitution against the local origin remote. The
    `--paginate` flag walks every page of the branches endpoint;
    `--jq .[].name` projects each entry to its `name` field, one
    branch name per line on stdout.

    Failure modes lifted to IOFailure(PreconditionError):
      - `gh api repos/branches` exits non-zero (gh unauthenticated,
        network failure, repo not on GitHub).
      - The `gh` binary itself missing: lifts via the proc seam.
    """
    return run_subprocess(
        argv=[
            "gh",
            "api",
            "-X",
            "GET",
            "repos/{owner}/{repo}/branches",
            "--paginate",
            "--jq",
            ".[].name",
        ],
        cwd=project_root,
    ).bind(
        lambda completed: (  # pyright: ignore[reportArgumentType]
            IOResult.from_value(
                tuple(line for line in completed.stdout.splitlines() if line.strip()),
            )
            if completed.returncode == 0
            else IOResult.from_failure(
                PreconditionError(
                    f"gh.list_remote_branches: "
                    f"`gh api repos/branches` exited {completed.returncode}",
                ),
            )
        ),
    )


def list_merged_pull_request_head_refs(
    *,
    project_root: Path,
) -> IOResult[tuple[str, ...], LivespecError]:
    """Return the head branch names of merged PRs in the current repo per gh.

    Composes `gh pr list --state merged --json headRefName --limit
    1000 --jq '.[].headRefName'` with `cwd=project_root`. The
    `--limit 1000` matches gh's documented ceiling for the pr-list
    surface; consumers assume a project will not accumulate more
    than 1000 unprocessed merged PRs awaiting branch deletion
    before cleanup runs.

    Failure modes lifted to IOFailure(PreconditionError):
      - `gh pr list` exits non-zero (gh unauthenticated, network
        failure, repo not on GitHub).
      - The `gh` binary itself missing: lifts via the proc seam.
    """
    return run_subprocess(
        argv=[
            "gh",
            "pr",
            "list",
            "--state",
            "merged",
            "--json",
            "headRefName",
            "--limit",
            "1000",
            "--jq",
            ".[].headRefName",
        ],
        cwd=project_root,
    ).bind(
        lambda completed: (  # pyright: ignore[reportArgumentType]
            IOResult.from_value(
                tuple(line for line in completed.stdout.splitlines() if line.strip()),
            )
            if completed.returncode == 0
            else IOResult.from_failure(
                PreconditionError(
                    f"gh.list_merged_pull_request_head_refs: "
                    f"`gh pr list --state merged` exited {completed.returncode}",
                ),
            )
        ),
    )
