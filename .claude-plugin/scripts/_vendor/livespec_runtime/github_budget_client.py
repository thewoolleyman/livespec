"""Budget-aware GitHub transport wrapper."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from threading import Lock
from time import monotonic
from time import sleep as sleep_seconds

from returns.io import IOFailure

from livespec_runtime.github_budget_client_support import (
    GithubCachedRead,
    backoff_seconds,
    cached_response,
    header_value,
    int_option,
    mapping_option,
    poll_interval,
    snapshot_from_headers,
    unmeasurable_classification,
    with_snapshot,
)
from livespec_runtime.github_budget_measurement import (
    classify_github_failure,
    parse_rate_limit_snapshot,
)
from livespec_runtime.github_budget_types import (
    GithubBudgetDeferred,
    GithubBudgetRequest,
    GithubBudgetResponse,
    GithubBudgetResult,
    GithubBudgetSuccess,
    GithubBudgetTransport,
    GithubBudgetUnmeasurable,
    GithubRateLimitSnapshot,
)

__all__: list[str] = [
    "GithubBudgetedClient",
]

_HTTP_FORBIDDEN = 403
_HTTP_NOT_MODIFIED = 304
_MUTATING_METHODS = frozenset({"DELETE", "PATCH", "POST", "PUT"})


@dataclass(slots=True, kw_only=True)
class GithubBudgetedClient:
    """Budget-aware wrapper around an injected GitHub transport."""

    transport: GithubBudgetTransport
    now: Callable[[], float] = monotonic
    sleep: Callable[[float], None] = sleep_seconds
    max_attempts: int = 3
    _cache: dict[str, GithubCachedRead] = field(default_factory=dict, init=False, repr=False)
    _last_mutation_at: float | None = field(default=None, init=False, repr=False)
    _mutation_lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def request(
        self,
        *,
        method: str,
        resource: str,
        headers: Mapping[str, str] | None = None,
        value: object | None = None,
        **options: object,
    ) -> GithubBudgetResult:
        """Issue one request after applying cache, pacing, backoff, and floor policy."""
        method_name = method.upper()
        floor_failure = self._floor_failure(
            resource=resource,
            deferrable=bool(options.get("deferrable", False)),
            remaining_floor=int_option(options=options, name="remaining_floor"),
            snapshot_headers=mapping_option(options=options, name="snapshot_headers"),
        )
        if floor_failure is not None:
            return IOFailure(floor_failure)
        if method_name in _MUTATING_METHODS:
            with self._mutation_lock:
                return self._request_with_backoff(
                    method=method_name,
                    resource=resource,
                    headers=headers,
                    value=value,
                )
        return self._request_with_backoff(
            method=method_name,
            resource=resource,
            headers=headers,
            value=value,
        )

    def _request_with_backoff(
        self,
        *,
        method: str,
        resource: str,
        headers: Mapping[str, str] | None,
        value: object | None,
    ) -> GithubBudgetResult:
        repeat = 0
        attempts = max(1, self.max_attempts)
        while True:
            response = self._request_once(
                method=method,
                resource=resource,
                headers=headers,
                value=value,
            )
            snapshot = snapshot_from_headers(headers=response.headers)
            if response.status_code != _HTTP_FORBIDDEN:
                return GithubBudgetSuccess(
                    response=with_snapshot(response=response, snapshot=snapshot)
                )
            classification = classify_github_failure(
                status_code=response.status_code,
                snapshot=snapshot,
            )
            if repeat + 1 == attempts:
                return IOFailure(
                    GithubBudgetUnmeasurable(
                        argv=f"{method} {resource}",
                        detail=f"GitHub request blocked by {classification.value}",
                        classification=unmeasurable_classification(classification=classification),
                        snapshot=snapshot,
                    )
                )
            self.sleep(
                backoff_seconds(
                    headers=response.headers,
                    snapshot=snapshot,
                    now=self.now(),
                    repeat=repeat,
                )
            )
            repeat += 1

    def _request_once(
        self,
        *,
        method: str,
        resource: str,
        headers: Mapping[str, str] | None,
        value: object | None,
    ) -> GithubBudgetResponse:
        if method in _MUTATING_METHODS:
            self._pace_mutation()
        request_headers = dict(headers or {})
        cached = self._cache.get(resource) if method == "GET" else None
        if cached is not None and self.now() < cached.next_poll_at:
            return cached_response(cached=cached, headers=cached.response.headers)
        if cached is not None:
            request_headers["If-None-Match"] = cached.etag
        response = self.transport(
            request=GithubBudgetRequest(
                method=method,
                resource=resource,
                headers=request_headers,
                value=value,
            )
        )
        if cached is not None and response.status_code == _HTTP_NOT_MODIFIED:
            return cached_response(cached=cached, headers=response.headers)
        if method == "GET":
            self._store_read(resource=resource, response=response)
        return response

    def _pace_mutation(self) -> None:
        if self._last_mutation_at is not None:
            wait = 1.0 - (self.now() - self._last_mutation_at)
            self.sleep(max(0.0, wait))
        self._last_mutation_at = self.now()

    def _store_read(self, *, resource: str, response: GithubBudgetResponse) -> None:
        etag = header_value(headers=response.headers, name="etag")
        if etag is None:
            return
        read_poll_interval = poll_interval(headers=response.headers)
        self._cache[resource] = GithubCachedRead(
            response=response,
            etag=etag,
            next_poll_at=self.now() + read_poll_interval,
        )

    def _floor_failure(
        self,
        *,
        resource: str,
        deferrable: bool,
        remaining_floor: int,
        snapshot_headers: Mapping[str, str] | None,
    ) -> GithubBudgetDeferred | None:
        if not deferrable or remaining_floor <= 0:
            return None
        snapshot = self._preflight_snapshot(snapshot_headers=snapshot_headers)
        failure = GithubBudgetDeferred(
            resource=resource,
            remaining=snapshot.remaining,
            floor=remaining_floor,
            snapshot=snapshot,
        )
        failures: dict[bool, GithubBudgetDeferred | None] = {
            False: None,
            True: failure,
        }
        return failures[snapshot.remaining < remaining_floor]

    def _preflight_snapshot(
        self,
        *,
        snapshot_headers: Mapping[str, str] | None,
    ) -> GithubRateLimitSnapshot:
        if snapshot_headers is not None:
            return parse_rate_limit_snapshot(headers=snapshot_headers)
        response = self.transport(
            request=GithubBudgetRequest(
                method="GET",
                resource="/rate_limit",
                headers={},
            )
        )
        return parse_rate_limit_snapshot(headers=response.headers)
