"""GitHub request-budget parsing, classification, and signal logging."""

import json
import os
from collections.abc import Mapping
from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec_runtime.github_budget_types import (
    GithubBudgetSignalFailed,
    GithubRateLimitClassification,
    GithubRateLimitSnapshot,
)

__all__: list[str] = [
    "append_rate_limit_snapshot",
    "classify_github_failure",
    "extract_rate_limit_headers",
    "parse_rate_limit_snapshot",
]

_DEFAULT_SIGNAL_PATH = Path("tmp/github-rate-limit.jsonl")
_SIGNAL_PATH_ENV = "LIVESPEC_GITHUB_BUDGET_LOG"
_HTTP_AUTH_FAILURE = 401
_HTTP_FORBIDDEN = 403


def parse_rate_limit_snapshot(*, headers: Mapping[str, str]) -> GithubRateLimitSnapshot:
    """Parse GitHub rate-limit headers into a typed snapshot."""
    lowered = {key.lower(): value for key, value in headers.items()}
    return GithubRateLimitSnapshot(
        limit=int(lowered["x-ratelimit-limit"]),
        remaining=int(lowered["x-ratelimit-remaining"]),
        used=int(lowered["x-ratelimit-used"]),
        reset=int(lowered["x-ratelimit-reset"]),
        resource=lowered["x-ratelimit-resource"],
    )


def extract_rate_limit_headers(*, text: str | None) -> dict[str, str]:
    """Extract `x-ratelimit-*` header lines from `gh` debug/include text."""
    if text is None:
        return {}
    headers: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.removeprefix("<").strip()
        name, separator, value = line.partition(":")
        if separator and name.lower().startswith("x-ratelimit-"):
            headers[name.lower()] = value.strip()
    return headers


def classify_github_failure(
    *,
    status_code: int,
    snapshot: GithubRateLimitSnapshot,
) -> GithubRateLimitClassification:
    """Classify a failed GitHub response into exactly one branch."""
    if status_code == _HTTP_FORBIDDEN and snapshot.remaining == 0:
        return GithubRateLimitClassification.PRIMARY_EXHAUSTION
    if status_code == _HTTP_FORBIDDEN and snapshot.remaining > 0:
        return GithubRateLimitClassification.SECONDARY_LIMIT
    if status_code == _HTTP_AUTH_FAILURE:
        return GithubRateLimitClassification.AUTH_FAILURE
    return GithubRateLimitClassification.OTHER


def append_rate_limit_snapshot(
    *,
    snapshot: GithubRateLimitSnapshot,
    argv: str,
    status_code: int | None,
    classification: GithubRateLimitClassification | None,
    path: Path | None = None,
) -> IOResult[None, GithubBudgetSignalFailed]:
    """Append one rate-limit snapshot to the durable local JSONL signal."""
    signal_path = _signal_path(path=path)
    record = {
        "argv": argv,
        "classification": None if classification is None else classification.value,
        "limit": snapshot.limit,
        "remaining": snapshot.remaining,
        "reset": snapshot.reset,
        "resource": snapshot.resource,
        "status_code": status_code,
        "used": snapshot.used,
    }
    signal_path.parent.mkdir(parents=True, exist_ok=True)
    with signal_path.open("a", encoding="utf-8") as handle:
        _ = handle.write(json.dumps(record, sort_keys=True))
        _ = handle.write("\n")
    return IOSuccess(None)


def _signal_path(*, path: Path | None) -> Path:
    if path is not None:
        return path
    return Path(os.environ.get(_SIGNAL_PATH_ENV, str(_DEFAULT_SIGNAL_PATH)))
