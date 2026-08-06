"""Subprocess execution and budget measurement for the GitHub provider."""

import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Literal, TypeAlias

from returns.io import IOFailure, IOResult, IOSuccess

from livespec_runtime.github_budget import (
    GithubBudgetUnmeasurable,
    GithubRateLimitClassification,
    append_rate_limit_snapshot,
    classify_github_failure,
    extract_rate_limit_headers,
    parse_rate_limit_snapshot,
)

__all__: list[str] = [
    "GithubFailure",
    "GithubQueryFailed",
    "completed_gh",
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
RateLimitOutcome: TypeAlias = Literal["primary_exhaustion", "secondary_limit"]

_RATE_LIMIT_OUTCOMES: dict[GithubRateLimitClassification, RateLimitOutcome | None] = {
    GithubRateLimitClassification.PRIMARY_EXHAUSTION: "primary_exhaustion",
    GithubRateLimitClassification.SECONDARY_LIMIT: "secondary_limit",
    GithubRateLimitClassification.AUTH_FAILURE: None,
    GithubRateLimitClassification.OTHER: None,
}


def completed_gh(*, argv: list[str]) -> IOResult[subprocess.CompletedProcess[str], GithubFailure]:
    """Run a `gh` command, or name the invocation that did not answer."""
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            check=True,
            env=_gh_env_with_headers(),
            text=True,
        )
    except subprocess.CalledProcessError as failed:
        return _failed_completed_gh(argv=argv, failed=failed)
    except OSError as unusable:
        return IOFailure(GithubQueryFailed(argv=shlex.join(argv), detail=str(unusable)))
    _record_budget_snapshot(
        argv=argv,
        stdout=completed.stdout,
        stderr=completed.stderr,
        status_code=0,
        classification=None,
    )
    return IOSuccess(completed)


def _failed_completed_gh(
    *,
    argv: list[str],
    failed: subprocess.CalledProcessError,
) -> IOResult[subprocess.CompletedProcess[str], GithubFailure]:
    argv_display = shlex.join(argv)
    detail = (failed.stderr or "").strip() or f"exit {failed.returncode}"
    headers = extract_rate_limit_headers(text=failed.stderr)
    if headers:
        return _failed_github_response(
            argv=argv,
            detail=detail,
            failed=failed,
            headers=headers,
        )
    return IOFailure(
        GithubQueryFailed(
            argv=argv_display,
            detail=detail,
            http_404=stderr_indicates_http_404(stderr=failed.stderr),
        )
    )


def _failed_github_response(
    *,
    argv: list[str],
    detail: str,
    failed: subprocess.CalledProcessError,
    headers: dict[str, str],
) -> IOResult[subprocess.CompletedProcess[str], GithubFailure]:
    status_code = _http_status_code(stderr=failed.stderr)
    snapshot = parse_rate_limit_snapshot(headers=headers)
    classification = classify_github_failure(status_code=status_code, snapshot=snapshot)
    _record_budget_snapshot(
        argv=argv,
        stdout=None,
        stderr=failed.stderr,
        status_code=status_code,
        classification=classification,
    )
    rate_limit_outcome = _RATE_LIMIT_OUTCOMES[classification]
    failures: dict[RateLimitOutcome | None, GithubFailure] = {
        None: GithubQueryFailed(
            argv=shlex.join(argv),
            detail=detail,
            http_404=stderr_indicates_http_404(stderr=failed.stderr),
        ),
        "primary_exhaustion": GithubBudgetUnmeasurable(
            argv=shlex.join(argv),
            detail=detail,
            classification="primary_exhaustion",
            snapshot=snapshot,
        ),
        "secondary_limit": GithubBudgetUnmeasurable(
            argv=shlex.join(argv),
            detail=detail,
            classification="secondary_limit",
            snapshot=snapshot,
        ),
    }
    return IOFailure(failures[rate_limit_outcome])


def _record_budget_snapshot(
    *,
    argv: list[str],
    stdout: str | None,
    stderr: str | None,
    status_code: int | None,
    classification: GithubRateLimitClassification | None,
) -> None:
    headers = extract_rate_limit_headers(text=stderr)
    headers.update(extract_rate_limit_headers(text=stdout))
    if not headers:
        return
    snapshot = parse_rate_limit_snapshot(headers=headers)
    _ = append_rate_limit_snapshot(
        snapshot=snapshot,
        argv=shlex.join(argv),
        status_code=status_code,
        classification=classification,
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


def _http_status_code(*, stderr: str) -> int:
    marker = "(HTTP "
    return int(
        next(
            line.rpartition(marker)[2].removesuffix(")")
            for line in stderr.splitlines()
            if marker in line
        )
    )


def _gh_env_with_headers() -> dict[str, str]:
    env = dict(os.environ)
    env["GH_DEBUG"] = "api"
    return env
