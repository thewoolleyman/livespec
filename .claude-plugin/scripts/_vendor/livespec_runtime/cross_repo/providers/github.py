"""GitHub `gh` CLI provider for cross-repo state queries.

Per livespec/SPECIFICATION/contracts.md v072: every GitHub query the
resolve-ref walker issues funnels through this module. `gh` MUST be
installed and authenticated
(`gh auth status` returning success) in any environment where the
runtime is consumed; absence is a configuration error surfaced by the
caller's retry policy collapsing to `RefStatus.UNKNOWN`.

Each function returns an `IOResult`: the ANSWER on the success track,
and a `GithubQueryFailed` naming the command and the reason on the
failure track. The resolve-ref walker wraps them in
`retry.retry_with_backoff` and translates retry exhaustion to
`RefStatus.UNKNOWN`. The one expected non-failure exit — a 404 on the
branch existence probe — is detected by the stderr fingerprint and is
`IOSuccess(False)`, NOT a failure: it means the branch is gone, which
is an answer.

⚠️ THE TWO ERROR CHANNELS ARE SPLIT ON PURPOSE, AND THE SPLIT IS NOW
SHARPER THAN IT WAS. Per livespec/SPECIFICATION/non-functional-requirements.md,
schema-level input (canonical github_url form) is validated at the
boundary and surfaced as a typed error: `NonCanonicalGithubUrlError`
still RAISES, because a malformed URL is a caller defect that no retry
can fix and no `RefStatus` can honestly represent. Runtime TRANSPORT
failure (gh exit codes, JSON decode, a payload missing its key) used to
raise built-ins alongside it; those now ride the failure track, where
the retry layer can act on them.
"""

import json
import shlex
from typing import Any

from returns.io import IOFailure, IOResult, IOSuccess
from returns.unsafe import unsafe_perform_io

from livespec_runtime.cross_repo.providers.github_process import (
    GithubBudgetUnmeasurable,
    GithubFailure,
    GithubQueryFailed,
    completed_gh,
)

__all__: list[str] = [
    "GithubBudgetUnmeasurable",
    "GithubFailure",
    "GithubQueryFailed",
    "NonCanonicalGithubUrlError",
    "branch_exists_on_remote",
    "branch_merged_into_default",
    "query_pull_request_state",
]


# Named rather than written as bare `True`/`False` literals at the lift
# sites: `IOSuccess(...)` takes its value positionally, and a positional
# boolean says nothing at the call site about which answer it is.
_A_404_MEANS_THE_BRANCH_IS_GONE = False
_GH_ANSWERED_SO_THE_BRANCH_EXISTS = True


class NonCanonicalGithubUrlError(Exception):
    """Raised when a github_url is not the canonical https form.

    Canonical form: `https://github.com/<owner>/<name>` with an
    optional trailing `.git` and/or trailing `/`. Any other form
    (`git@github.com:...`, `git://...`, bare owner/name) raises this
    error at the module boundary so consumers never silently dispatch
    `gh` against a malformed URL.

    Inherits `Exception` directly: consumers catch this domain type
    (or `Exception`), never `ValueError`.
    """

    def __init__(self, *, github_url: str) -> None:
        super().__init__(f"expected canonical github_url, got {github_url!r}")
        self.github_url = github_url


def query_pull_request_state(*, github_url: str, number: int) -> IOResult[str, GithubFailure]:
    """Return the PR's `state` via `gh pr view --json state`.

    State is one of `OPEN`, `CLOSED`, `MERGED` per the GitHub REST API.
    The caller (resolve-ref walker) interprets `MERGED` or `CLOSED` as
    `RefStatus.CLOSED` and `OPEN` as `RefStatus.OPEN`.
    """
    argv = ["gh", "pr", "view", str(number), "--repo", github_url, "--json", "state"]
    completed = completed_gh(argv=argv)
    if isinstance(completed, IOFailure):
        return completed
    return _decoded_field(
        argv=argv, stdout=unsafe_perform_io(completed.unwrap()).stdout, key="state"
    )


def branch_exists_on_remote(*, github_url: str, name: str) -> IOResult[bool, GithubFailure]:
    """Return True iff the named branch exists on the remote.

    Uses `gh api repos/<owner>/<name>/branches/<branch>`. A 404 is
    detected via the structured `gh: <message> (HTTP 404)` line that
    `gh` emits to stderr on a 4xx response — the trailing
    `(HTTP 404)` marker on any stderr line is the discriminator,
    NOT a bare `'404'` substring (which can collide with unrelated
    content such as a URL fragment in an error body). Any other
    CalledProcessError propagates so the retry-wrap layer can decide
    whether to back off and retry.

    Per livespec/SPECIFICATION/history/v003/contracts.md: the 404 SHOULD
    be detected via `gh`'s
    structured response, not a substring match on stderr.
    """
    owner_name = _split_owner_name(github_url=github_url)
    argv = ["gh", "api", f"repos/{owner_name}/branches/{name}"]
    completed = completed_gh(argv=argv)
    if isinstance(completed, IOFailure):
        failure = unsafe_perform_io(completed.failure())
        if isinstance(failure, GithubQueryFailed) and failure.http_404:
            return IOSuccess(_A_404_MEANS_THE_BRANCH_IS_GONE)
        return completed
    return IOSuccess(_GH_ANSWERED_SO_THE_BRANCH_EXISTS)


def _decoded_field(*, argv: list[str], stdout: str, key: str) -> IOResult[str, GithubFailure]:
    """The named string field of a `gh --json` payload, or why it is absent.

    A malformed payload and a payload missing the key both used to raise
    (`JSONDecodeError` / `KeyError`) and reach the retry layer's broad
    catch, which reported neither. Both are transport-shaped — `gh`
    answered with something unusable — so both land on the failure track
    naming the command and the key.
    """
    try:
        payload: dict[str, Any] = json.loads(stdout)
    except json.JSONDecodeError as undecodable:
        return IOFailure(
            GithubQueryFailed(argv=shlex.join(argv), detail=f"undecodable response: {undecodable}")
        )
    value = payload.get(key)
    if not isinstance(value, str):
        return IOFailure(
            GithubQueryFailed(argv=shlex.join(argv), detail=f"response carried no {key!r} string")
        )
    return IOSuccess(value)


def branch_merged_into_default(
    *,
    github_url: str,
    name: str,
    default_branch: str,
) -> IOResult[bool, GithubFailure]:
    """Return True iff `name` is fully reachable from `default_branch`.

    Uses `gh api repos/<owner>/<name>/compare/<default>...<name>`. The
    `status` field is `identical` when the two refs point at the same
    commit and `behind` when `name` has zero commits ahead of
    `default_branch` (i.e., `name` is merged). Both translate to
    `True`; `ahead` / `diverged` translate to `False`.
    """
    owner_name = _split_owner_name(github_url=github_url)
    argv = ["gh", "api", f"repos/{owner_name}/compare/{default_branch}...{name}"]
    completed = completed_gh(argv=argv)
    if isinstance(completed, IOFailure):
        return completed
    decoded = _decoded_field(
        argv=argv, stdout=unsafe_perform_io(completed.unwrap()).stdout, key="status"
    )
    return decoded.map(lambda status: status in ("identical", "behind"))


def _split_owner_name(*, github_url: str) -> str:
    """Convert `https://github.com/<owner>/<name>[.git][/]` → `<owner>/<name>`.

    Accepts the canonical https form with an optional `.git` suffix and/or
    trailing `/`. Raises `NonCanonicalGithubUrlError` on any other shape
    (ssh, git protocol, bare owner/name, host other than github.com).
    """
    prefix = "https://github.com/"
    if not github_url.startswith(prefix):
        raise NonCanonicalGithubUrlError(github_url=github_url)
    tail = github_url[len(prefix) :]
    return tail.removesuffix("/").removesuffix(".git")
