"""Support helpers for the budget-aware GitHub transport wrapper."""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Literal, cast

from livespec_runtime.github_budget_measurement import parse_rate_limit_snapshot
from livespec_runtime.github_budget_types import (
    GithubBudgetResponse,
    GithubRateLimitClassification,
    GithubRateLimitSnapshot,
)

__all__: list[str] = [
    "GithubCachedRead",
    "MisshapedGithubBudgetOptionError",
    "backoff_seconds",
    "cached_response",
    "header_value",
    "int_option",
    "mapping_option",
    "poll_interval",
    "snapshot_from_headers",
    "unmeasurable_classification",
    "with_snapshot",
]

_HTTP_NOT_MODIFIED = 304
_UNMEASURABLE_CLASSIFICATIONS: dict[
    GithubRateLimitClassification,
    Literal["primary_exhaustion", "secondary_limit"],
] = {
    GithubRateLimitClassification.PRIMARY_EXHAUSTION: "primary_exhaustion",
    GithubRateLimitClassification.SECONDARY_LIMIT: "secondary_limit",
}


class MisshapedGithubBudgetOptionError(Exception):
    """Raised when a request option IS set but does not match its declared shape.

    Inherits `Exception` directly: consumers catch this domain type (or
    `Exception`), never a builtin ancestor such as `TypeError`.
    """

    def __init__(self, *, name: str, expected: str, value: object) -> None:
        super().__init__(f"option {name!r} must be {expected}, got {value!r}")
        self.name = name
        self.expected = expected
        self.value = value


@dataclass(frozen=True, slots=True, kw_only=True)
class GithubCachedRead:
    response: GithubBudgetResponse
    etag: str
    next_poll_at: float


def cached_response(
    *,
    cached: GithubCachedRead,
    headers: Mapping[str, str],
) -> GithubBudgetResponse:
    return replace(
        cached.response,
        status_code=_HTTP_NOT_MODIFIED,
        headers=headers,
        primary_budget_spent=0,
        snapshot=snapshot_from_headers(headers=headers),
    )


def header_value(*, headers: Mapping[str, str], name: str) -> str | None:
    lowered = {key.lower(): value for key, value in headers.items()}
    return lowered.get(name.lower())


def poll_interval(*, headers: Mapping[str, str]) -> float:
    value = header_value(headers=headers, name="x-poll-interval")
    return float(value or 0.0)


def snapshot_from_headers(*, headers: Mapping[str, str]) -> GithubRateLimitSnapshot:
    return parse_rate_limit_snapshot(headers=headers)


def with_snapshot(
    *,
    response: GithubBudgetResponse,
    snapshot: GithubRateLimitSnapshot,
) -> GithubBudgetResponse:
    return replace(response, snapshot=snapshot)


def backoff_seconds(
    *,
    headers: Mapping[str, str],
    snapshot: GithubRateLimitSnapshot,
    now: float,
    repeat: int,
) -> float:
    retry_after = header_value(headers=headers, name="retry-after")
    if retry_after is not None:
        return float(retry_after)
    if snapshot.remaining == 0:
        return max(0.0, float(snapshot.reset) - now)
    return 60.0 * (2.0**repeat)


def int_option(*, options: Mapping[str, object], name: str) -> int:
    """Read one `int` option, defaulting to 0 when it is not set.

    A set-but-mis-shaped value RAISES rather than flowing on wrongly typed: a
    bare `cast` is an assertion to the type checker and compiles to an identity
    function, so the annotation has to be ESTABLISHED at runtime before any
    downstream consumer may rely on it.
    """
    value = options.get(name, 0)
    if not isinstance(value, int):
        raise MisshapedGithubBudgetOptionError(name=name, expected="an int", value=value)
    return value


def mapping_option(
    *,
    options: Mapping[str, object],
    name: str,
) -> Mapping[str, str] | None:
    """Read one `Mapping[str, str]` option; `None` means the option is not set.

    The `None` keeps EXACTLY ONE meaning — absence. A set-but-mis-shaped value
    is a caller bug and RAISES, the same direction `spec_governance` took when
    it lifted its malformed-block failure out of a `None`; folding mis-shape
    into the `None` would make absence and failure indistinguishable here.
    """
    value = options.get(name)
    if value is None:
        return None
    if not _is_str_mapping(value=value):
        raise MisshapedGithubBudgetOptionError(
            name=name,
            expected="a mapping of str to str",
            value=value,
        )
    return cast(Mapping[str, str], value)


def _is_str_mapping(*, value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    pairs = cast(Mapping[object, object], value)
    return all(isinstance(key, str) and isinstance(item, str) for key, item in pairs.items())


def unmeasurable_classification(
    *,
    classification: GithubRateLimitClassification,
) -> Literal["primary_exhaustion", "secondary_limit"]:
    return _UNMEASURABLE_CLASSIFICATIONS[classification]
