"""GitHub `gh` CLI provider for cross-repo state queries.

Per livespec/SPECIFICATION/contracts.md v072: every GitHub query the
resolve-ref walker issues funnels through this module. `gh` MUST be
installed and authenticated
(`gh auth status` returning success) in any environment where the
runtime is consumed; absence is a configuration error surfaced by the
caller's retry policy collapsing to `RefStatus.UNKNOWN`.

Each function raises `subprocess.CalledProcessError` (or
`json.JSONDecodeError`) on failure; the resolve-ref walker wraps
them in `retry.retry_with_backoff` and translates retry exhaustion
to `RefStatus.UNKNOWN`. The one expected non-failure exit — a 404
on the branch existence probe — is detected by the stderr fingerprint
and returned as `False` instead of propagating.

`NonCanonicalGithubUrlError` is the only domain exception raised
here. Per livespec/SPECIFICATION/non-functional-requirements.md,
schema-level inputs (canonical github_url
form) are validated at the boundary and surfaced as a typed error;
runtime transport failures (gh exit codes, JSON decode) propagate
as built-ins.
"""

import json
import subprocess
from typing import Any

__all__: list[str] = [
    "NonCanonicalGithubUrlError",
    "branch_exists_on_remote",
    "branch_merged_into_default",
    "query_pull_request_state",
]


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


def query_pull_request_state(*, github_url: str, number: int) -> str:
    """Return the PR's `state` via `gh pr view --json state`.

    State is one of `OPEN`, `CLOSED`, `MERGED` per the GitHub REST API.
    The caller (resolve-ref walker) interprets `MERGED` or `CLOSED` as
    `RefStatus.CLOSED` and `OPEN` as `RefStatus.OPEN`.
    """
    result = subprocess.run(
        [
            "gh",
            "pr",
            "view",
            str(number),
            "--repo",
            github_url,
            "--json",
            "state",
        ],
        capture_output=True,
        check=True,
        text=True,
    )
    payload: dict[str, Any] = json.loads(result.stdout)
    state: str = payload["state"]
    return state


def branch_exists_on_remote(*, github_url: str, name: str) -> bool:
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
    try:
        _ = subprocess.run(
            ["gh", "api", f"repos/{owner_name}/branches/{name}"],
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        if _stderr_indicates_http_404(stderr=exc.stderr):
            return False
        raise
    return True


def _stderr_indicates_http_404(*, stderr: str | None) -> bool:
    """Return True iff any stderr line carries the structured `HTTP 404` marker.

    `gh` formats 4xx responses as `gh: <message> (HTTP <code>)` on a
    dedicated stderr line. Matching on the trailing `(HTTP 404)`
    marker — rather than a bare `404` substring — avoids
    mis-categorizing unrelated content (URL fragments, body text
    referencing 404 pages, etc.) as a real not-found response.
    """
    if not stderr:
        return False
    marker = "(HTTP 404)"
    return any(line.rstrip().endswith(marker) for line in stderr.splitlines())


def branch_merged_into_default(
    *,
    github_url: str,
    name: str,
    default_branch: str,
) -> bool:
    """Return True iff `name` is fully reachable from `default_branch`.

    Uses `gh api repos/<owner>/<name>/compare/<default>...<name>`. The
    `status` field is `identical` when the two refs point at the same
    commit and `behind` when `name` has zero commits ahead of
    `default_branch` (i.e., `name` is merged). Both translate to
    `True`; `ahead` / `diverged` translate to `False`.
    """
    owner_name = _split_owner_name(github_url=github_url)
    result = subprocess.run(
        ["gh", "api", f"repos/{owner_name}/compare/{default_branch}...{name}"],
        capture_output=True,
        check=True,
        text=True,
    )
    payload: dict[str, Any] = json.loads(result.stdout)
    status: str = payload["status"]
    return status in ("identical", "behind")


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
