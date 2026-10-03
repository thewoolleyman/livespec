"""Budgeted `gh` execution for the GitHub provider.

Every query this provider issues goes through ONE process-wide
`GithubBudgetedClient`, which is what makes its conditional-read cache
worth having: the branch-existence and compare reads poll state that is
usually unchanged, and a read the server answers `304 Not Modified`
costs no primary budget at all. A per-call client would carry a cache
that is empty on every call, which is the same as having none.

⚠️ THE CLIENT IS BUILT WITH `max_attempts=1` ON PURPOSE. Retry policy
for this provider belongs to `cross_repo.retry`, one layer up — that is
the layer that knows a retry-exhausted query degrades to
`RefStatus.UNKNOWN`. A second retry loop inside the transport would
multiply the attempt count the resolver chose and sleep on a schedule it
never asked for.
"""

import os
import shlex
import subprocess
from dataclasses import dataclass, replace
from typing import TypeAlias

from returns.io import IOFailure, IOResult, IOSuccess
from returns.unsafe import unsafe_perform_io

from livespec_runtime.github_budget import (
    GhInvocation,
    GithubBudgetedClient,
    GithubBudgetFailure,
    GithubBudgetUnmeasurable,
    gh_invocation,
    gh_transport,
)
from livespec_runtime.github_budget_measurement import gh_argv

__all__: list[str] = [
    "GithubFailure",
    "GithubQueryFailed",
    "budget_failure",
    "budgeted_gh",
    "spawn_gh",
    "stderr_indicates_http_404",
]


@dataclass(frozen=True, slots=True, kw_only=True)
class GithubQueryFailed:
    """A `gh` query that did not produce an answer.

    Deliberately NOT inhabited by "gh answered, and the answer was no".
    A 404 on the branch-existence probe means the branch is gone; a PR
    in state `CLOSED` is a state. Both are answers and both stay on the
    success track — putting them here would make the retry layer burn
    three attempts re-asking a question that was already settled.

    `argv` is the shell-quoted command so an operator can rerun it. The
    pre-railway code discarded it: `retry_with_backoff` returned a bare
    `None`, so a resolution that degraded to `UNKNOWN` could not say
    which of three possible queries had failed.
    """

    argv: str
    detail: str
    http_404: bool = False


GithubFailure: TypeAlias = GithubQueryFailed | GithubBudgetUnmeasurable


def spawn_gh(*, argv: list[str]) -> GhInvocation:
    """Spawn one `gh` argv, reporting what it printed or why it never ran.

    `GH_DEBUG=api` is what makes the response headers observable: `gh`
    echoes them on stderr, and that stream is where both the budget
    snapshot and the conditional-read `etag` are read from.
    """
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            check=True,
            env=_gh_env_with_headers(),
            text=True,
        )
    except subprocess.CalledProcessError as failed:
        return GhInvocation(
            argv=shlex.join(argv),
            stdout=failed.stdout or "",
            stderr=failed.stderr or "",
            returncode=failed.returncode,
        )
    except OSError as unusable:
        return GhInvocation(argv=shlex.join(argv), unspawnable=str(unusable))
    return GhInvocation(argv=shlex.join(argv), stdout=completed.stdout, stderr=completed.stderr)


_CLIENT = GithubBudgetedClient(transport=gh_transport(execute=spawn_gh), max_attempts=1)


def budgeted_gh(*, resource: str) -> IOResult[GhInvocation, GithubFailure]:
    """Issue one budgeted `gh` read, or name the query that did not answer.

    `resource` is the shlex-joined `gh` argument tail; it doubles as the
    client's cache key, which is why it is passed instead of an argv the
    caller has already spelled out.
    """
    outcome = _CLIENT.request(method="GET", resource=resource)
    if isinstance(outcome, IOFailure):
        argv = shlex.join(gh_argv(resource=resource, headers={}))
        return IOFailure(budget_failure(failure=unsafe_perform_io(outcome.failure()), argv=argv))
    return _answered(invocation=gh_invocation(value=outcome.unwrap().value))


def budget_failure(*, failure: GithubBudgetFailure, argv: str) -> GithubFailure:
    """Restate a budget refusal in this provider's failure vocabulary.

    The rate-limited case passes through — `GithubFailure` names
    `GithubBudgetUnmeasurable` — carrying the `gh` argv rather than the
    client's method-and-resource wording, so the failure an operator sees
    is still a command they can rerun.

    A DEFERRAL cannot reach this provider: none of its reads is declared
    deferrable, because a resolution the walker asked for is not
    postponable work. The client's failure type admits one all the same,
    so it is mapped here rather than widening the ratified
    `GithubQueryFailed | GithubBudgetUnmeasurable` union to a third
    variant no caller of this provider could ever observe.
    """
    if isinstance(failure, GithubBudgetUnmeasurable):
        return replace(failure, argv=argv)
    return GithubQueryFailed(
        argv=argv,
        detail=f"deferred with {failure.remaining} left of a {failure.floor} floor",
    )


def _answered(*, invocation: GhInvocation) -> IOResult[GhInvocation, GithubFailure]:
    """The outcome as an answer, or as the failure it reports."""
    if invocation.unspawnable is not None:
        return IOFailure(GithubQueryFailed(argv=invocation.argv, detail=invocation.unspawnable))
    if invocation.returncode == 0:
        return IOSuccess(invocation)
    return IOFailure(
        GithubQueryFailed(
            argv=invocation.argv,
            detail=invocation.stderr.strip() or f"exit {invocation.returncode}",
            http_404=stderr_indicates_http_404(stderr=invocation.stderr),
        )
    )


def stderr_indicates_http_404(*, stderr: str | None) -> bool:
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


def _gh_env_with_headers() -> dict[str, str]:
    env = dict(os.environ)
    env["GH_DEBUG"] = "api"
    return env
