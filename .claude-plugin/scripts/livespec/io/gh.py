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

The gh facade exposes four read operations. The first three serve merged-PR /
branch introspection (originally pulled into existence by the retired
stale-cleanup doctor checks; cleanup discipline moved to the
orchestrator at v105, and these remain general-purpose reads); the
fourth serves the spec pull-request merge-policy gate:

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
  - `list_pull_request_files` — enumerates one pull request's changed
    files with their statuses via `gh api repos/<repo>/pulls/<n>/files
    --paginate`, naming the repository explicitly instead of relying
    on placeholder substitution.

All four pass `cwd=project_root` to `run_subprocess` so gh
resolves the local origin remote regardless of the calling
process's actual cwd. The git facade pins scope via `git -C`; gh
lacks an equivalent flag, so cwd is the documented mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from returns.io import IOResult

from livespec.errors import LivespecError, PreconditionError
from livespec.io.proc import run_subprocess

__all__: list[str] = [
    "PullRequestFile",
    "get_repo_name_with_owner",
    "list_merged_pull_request_head_refs",
    "list_pull_request_files",
    "list_remote_branches",
]

# Field separator for the `@tsv` projection in `list_pull_request_files`. A
# tab cannot occur in a git path as GitHub reports it, so splitting on it is
# unambiguous.
_TSV_SEPARATOR = "\t"
_TSV_FIELD_COUNT = 2


@dataclass(frozen=True, kw_only=True, slots=True)
class PullRequestFile:
    """One changed file of a pull request as the hosting API reports it.

    Deliberately an io-local record rather than the domain type the derivation
    consumes: the io layer sits below `livespec.spec_governance`, and this
    facade must not reach up into it. The caller maps the two fields across.
    """

    filename: str
    status: str


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


def list_pull_request_files(
    *,
    project_root: Path,
    repo: str,
    pull_request_number: int,
) -> IOResult[tuple[PullRequestFile, ...], LivespecError]:
    """Return every changed file of one pull request, with its status intact.

    Composes `gh api repos/<repo>/pulls/<n>/files --paginate --jq '.[] |
    [.status, .filename] | @tsv'` with `cwd=project_root`. `repo` is passed
    explicitly rather than through gh's `{owner}`/`{repo}` placeholders because
    the caller is a CI job that already knows its own repository and must not
    depend on the checkout carrying an origin remote.

    The projection deliberately does NOT filter by status. The spec pull-request
    merge derivation applies its own accepted-status set, so filtering here
    would put a second, silently drifting copy of that rule in the transport.

    Failure modes lifted to IOFailure(PreconditionError):
      - `gh api` exits non-zero (unauthenticated, network failure, unknown pull
        request). Per `SPECIFICATION/spec.md` `effective_spec_pr_merge` a
        hosting-API error is derivation FAILURE, never an empty file list.
      - A row that does not carry exactly two tab-separated fields, which would
        otherwise silently become a file with an empty status.
      - The `gh` binary itself missing: lifts via the proc seam.
    """
    return run_subprocess(
        argv=[
            "gh",
            "api",
            f"repos/{repo}/pulls/{pull_request_number}/files",
            "--paginate",
            "--jq",
            ".[] | [.status, .filename] | @tsv",
        ],
        cwd=project_root,
    ).bind(
        lambda completed: (
            _parse_pull_request_files(stdout=completed.stdout)
            if completed.returncode == 0
            else IOResult.from_failure(
                PreconditionError(
                    f"gh.list_pull_request_files: `gh api repos/{repo}/pulls/"
                    f"{pull_request_number}/files` exited {completed.returncode}",
                ),
            )
        ),
    )


def _parse_pull_request_files(
    *,
    stdout: str,
) -> IOResult[tuple[PullRequestFile, ...], LivespecError]:
    rows = [line for line in stdout.splitlines() if line.strip()]
    fields = [row.split(_TSV_SEPARATOR) for row in rows]
    malformed = [parts for parts in fields if len(parts) != _TSV_FIELD_COUNT]
    if malformed:
        offender = _TSV_SEPARATOR.join(malformed[0])
        return IOResult.from_failure(
            PreconditionError(
                f"gh.list_pull_request_files: malformed changed-file row: {offender!r}",
            ),
        )
    return IOResult.from_value(
        tuple(PullRequestFile(status=parts[0], filename=parts[1]) for parts in fields),
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
