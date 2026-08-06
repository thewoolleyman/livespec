"""Typed GitHub request-budget records."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Literal, TypeAlias

from returns.io import IOFailure

__all__: list[str] = [
    "GithubBudgetDeferred",
    "GithubBudgetFailure",
    "GithubBudgetRequest",
    "GithubBudgetResponse",
    "GithubBudgetResult",
    "GithubBudgetSignalFailed",
    "GithubBudgetSuccess",
    "GithubBudgetTransport",
    "GithubBudgetUnmeasurable",
    "GithubRateLimitClassification",
    "GithubRateLimitSnapshot",
]

GithubBudgetFailure: TypeAlias = "GithubBudgetDeferred | GithubBudgetUnmeasurable"
GithubBudgetResult: TypeAlias = "GithubBudgetSuccess | IOFailure[GithubBudgetFailure]"
GithubBudgetTransport: TypeAlias = Callable[..., "GithubBudgetResponse"]


@dataclass(frozen=True, slots=True, kw_only=True)
class GithubRateLimitClassification:
    """The mutually exclusive classes for a failed GitHub response."""

    value: Literal["primary_exhaustion", "secondary_limit", "auth_failure", "other"]

    PRIMARY_EXHAUSTION: ClassVar["GithubRateLimitClassification"]
    SECONDARY_LIMIT: ClassVar["GithubRateLimitClassification"]
    AUTH_FAILURE: ClassVar["GithubRateLimitClassification"]
    OTHER: ClassVar["GithubRateLimitClassification"]


GithubRateLimitClassification.PRIMARY_EXHAUSTION = GithubRateLimitClassification(
    value="primary_exhaustion"
)
GithubRateLimitClassification.SECONDARY_LIMIT = GithubRateLimitClassification(
    value="secondary_limit"
)
GithubRateLimitClassification.AUTH_FAILURE = GithubRateLimitClassification(value="auth_failure")
GithubRateLimitClassification.OTHER = GithubRateLimitClassification(value="other")


@dataclass(frozen=True, slots=True, kw_only=True)
class GithubRateLimitSnapshot:
    """A parsed view of GitHub's `x-ratelimit-*` response headers."""

    limit: int
    remaining: int
    used: int
    reset: int
    resource: str


@dataclass(frozen=True, slots=True, kw_only=True)
class GithubBudgetRequest:
    """A GitHub transport request after budget policy has been applied."""

    method: str
    resource: str
    headers: Mapping[str, str]
    value: object | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class GithubBudgetResponse:
    """A GitHub transport response with measured primary-budget cost."""

    status_code: int
    headers: Mapping[str, str]
    value: object | None
    primary_budget_spent: int
    snapshot: GithubRateLimitSnapshot | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class GithubBudgetUnmeasurable:
    """A rate-limited GitHub query whose answer cannot be measured now."""

    argv: str
    detail: str
    classification: Literal["primary_exhaustion", "secondary_limit"]
    snapshot: GithubRateLimitSnapshot
    outcome: Literal["UNMEASURABLE"] = "UNMEASURABLE"


@dataclass(frozen=True, slots=True, kw_only=True)
class GithubBudgetSignalFailed:
    """The local budget signal could not be appended."""

    path: Path
    detail: str


@dataclass(frozen=True, slots=True, kw_only=True)
class GithubBudgetSuccess:
    """Successful budgeted GitHub response."""

    response: GithubBudgetResponse

    def unwrap(self) -> GithubBudgetResponse:
        return self.response


@dataclass(frozen=True, slots=True, kw_only=True)
class GithubBudgetDeferred:
    """Deferrable work refused to preserve the caller's reserved budget floor."""

    resource: str
    remaining: int
    floor: int
    snapshot: GithubRateLimitSnapshot
