"""The `gh` boundary: request argv, response measurement, budget signal.

One cohesive concern — everything that happens where a budgeted request
meets the `gh` process. The REQUEST half turns a resource into an argv,
including the conditional-read header only the `api` subcommand can
carry. The RESPONSE half reads what GitHub reported off `gh`'s streams:
the budget headers, the HTTP status, the cache and pacing headers, the
classification of a refusal, and the durable local signal every measured
read appends to.

`gh_transport` joins the two, and it is the ONE place in this library
that builds a `gh` invocation. Every first-party GitHub read here goes
through it, so the conditional-read, pacing, backoff and floor policies
`GithubBudgetedClient` implements apply uniformly rather than to
whichever caller remembered to ask.
"""

import json
import os
import shlex
from collections.abc import Callable, Mapping
from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec_runtime.github_budget_types import (
    GhExecutor,
    GhInvocation,
    GithubBudgetRequest,
    GithubBudgetResponse,
    GithubBudgetSignalFailed,
    GithubBudgetTransport,
    GithubRateLimitClassification,
    GithubRateLimitSnapshot,
)

__all__: list[str] = [
    "RATE_LIMIT_RESOURCE",
    "append_rate_limit_snapshot",
    "classify_github_failure",
    "extract_conditional_headers",
    "extract_rate_limit_headers",
    "gh_argv",
    "gh_headers",
    "gh_invocation",
    "gh_status_code",
    "gh_transport",
    "parse_rate_limit_snapshot",
    "record_budget_signal",
    "snapshot_from_headers",
]

RATE_LIMIT_RESOURCE = "/rate_limit"

_DEFAULT_SIGNAL_PATH = Path("tmp/github-rate-limit.jsonl")
_SIGNAL_PATH_ENV = "LIVESPEC_GITHUB_BUDGET_LOG"
_HTTP_AUTH_FAILURE = 401
_HTTP_FORBIDDEN = 403
_HTTP_OK = 200
_HTTP_STATUS_MARKER = "(HTTP "
_NO_HTTP_STATUS = 0
_CONDITIONAL_SUBCOMMAND = "api"
_CONDITIONAL_HEADERS = frozenset(
    {
        "etag",
        "retry-after",
        "x-poll-interval",
    }
)
_RATE_LIMIT_HEADERS = frozenset(
    {
        "x-ratelimit-limit",
        "x-ratelimit-remaining",
        "x-ratelimit-reset",
        "x-ratelimit-resource",
        "x-ratelimit-used",
    }
)


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


def snapshot_from_headers(*, headers: Mapping[str, str]) -> GithubRateLimitSnapshot | None:
    """The budget snapshot a response's headers carry, or None when unmeasured.

    ⚠️ AN UNMEASURED READ AND A MEASURED ZERO ARE DIFFERENT FACTS. A
    response carrying no `x-ratelimit-*` headers reported nothing;
    `remaining: 0` reports a budget that is spent. Fabricating the second
    from the first would make every read a transport could not measure —
    a `gh` subcommand run without its header stream, a command that never
    spawned — look like primary exhaustion, and the client would then
    refuse deferrable work and back off until a reset that was never
    read. So absence stays absence, and each policy that needs a number
    says for itself what it does without one.
    """
    present = {name.lower() for name in headers}
    if not present.issuperset(_RATE_LIMIT_HEADERS):
        return None
    return parse_rate_limit_snapshot(headers=headers)


def extract_rate_limit_headers(*, text: str | None) -> dict[str, str]:
    """Extract `x-ratelimit-*` header lines from `gh` debug/include text."""
    return _headers_named(text=text, wanted=lambda name: name.startswith("x-ratelimit-"))


def extract_conditional_headers(*, text: str | None) -> dict[str, str]:
    """Extract the cache and pacing header lines from `gh` debug/include text.

    A closed set, not a prefix: `etag` is what lets a poll-shaped read be
    revalidated for no primary budget, `retry-after` is the server's own
    backoff instruction, and `x-poll-interval` is how long the server
    asks not to be asked again. They are the three headers the budgeted
    client acts on that are not budget NUMBERS, which is why they are
    read here and not by `extract_rate_limit_headers`.
    """
    return _headers_named(text=text, wanted=lambda name: name in _CONDITIONAL_HEADERS)


def _headers_named(*, text: str | None, wanted: Callable[[str], bool]) -> dict[str, str]:
    """The `wanted` header lines of one `gh` debug/include stream, lowercased.

    `gh` prefixes response headers with `<` on its `GH_DEBUG=api` stream
    and prints them bare under `--include`, so the prefix is stripped
    rather than required.
    """
    if text is None:
        return {}
    headers: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.removeprefix("<").strip()
        name, separator, value = line.partition(":")
        if separator and wanted(name.lower()):
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


def gh_argv(*, resource: str, headers: Mapping[str, str]) -> list[str]:
    """The `gh` argv one budgeted request becomes.

    The leading `/` discriminates two resource forms. A REST PATH
    (`/rate_limit`) becomes `gh api --include <path>`: it is the shape
    the client's own floor preflight issues, and `--include` puts the
    budget headers in `gh`'s OUTPUT, so the preflight is measurable even
    on an executor that cannot turn on `gh`'s debug stream. Anything else
    is a shlex-joined `gh` ARGUMENT TAIL — `pr view 42 --repo <url>
    --json state` — which `shlex.split` inverts exactly.

    Only `gh api` accepts `-H`, so only that form can carry the client's
    conditional-read header; `gh_headers` withholds the `etag` of every
    other form for the same reason. A read the transport could not later
    revalidate is left uncached rather than cached and then silently
    re-read unconditionally.
    """
    tail = (
        ["api", "--include", resource.removeprefix("/")]
        if resource.startswith("/")
        else shlex.split(resource)
    )
    return ["gh", *tail, *_conditional_flags(tail=tail, headers=headers)]


def _conditional_flags(*, tail: list[str], headers: Mapping[str, str]) -> list[str]:
    if tail[:1] != [_CONDITIONAL_SUBCOMMAND]:
        return []
    return [flag for name, value in headers.items() for flag in ("-H", f"{name}: {value}")]


def gh_headers(*, invocation: GhInvocation, revalidatable: bool) -> dict[str, str]:
    """The response headers one `gh` outcome surfaced.

    `gh` echoes them on stderr under `GH_DEBUG=api` and on stdout under
    `--include`, so both streams are read. An outcome that surfaced none
    yields an EMPTY mapping, which `snapshot_from_headers` then reports
    as unmeasured.
    """
    headers = extract_rate_limit_headers(text=invocation.stderr)
    headers.update(extract_rate_limit_headers(text=invocation.stdout))
    headers.update(extract_conditional_headers(text=invocation.stderr))
    headers.update(extract_conditional_headers(text=invocation.stdout))
    if not revalidatable:
        _ = headers.pop("etag", None)
    return headers


def gh_status_code(*, invocation: GhInvocation) -> int:
    """The HTTP status one `gh` outcome reports, or 0 when it reports none.

    `gh` formats a 4xx/5xx response as `gh: <message> (HTTP <code>)` on a
    dedicated stderr line. A zero exit means `gh` got an answer, so it
    reads as 200. A non-zero exit carrying no marker — and a run that
    never happened — reads as 0, a value no policy in the client treats
    as a rate-limit signal, so an unparseable failure stays the ordinary
    failure its caller will name.
    """
    if invocation.unspawnable is not None:
        return _NO_HTTP_STATUS
    if invocation.returncode == 0:
        return _HTTP_OK
    marked = [
        line.rpartition(_HTTP_STATUS_MARKER)[2].removesuffix(")")
        for line in invocation.stderr.splitlines()
        if _HTTP_STATUS_MARKER in line
    ]
    return int(marked[-1]) if marked and marked[-1].isdigit() else _NO_HTTP_STATUS


def gh_invocation(*, value: object) -> GhInvocation:
    """The `gh` outcome a budgeted response carries.

    `GithubBudgetResponse.value` is typed `object` because the transport
    protocol is transport-agnostic; this is the one place that reads it
    back as THIS transport's record. A value of any other shape is a
    wiring defect rather than a runtime condition, so it becomes an
    outcome that names itself — an unspawnable run quoting what arrived —
    instead of an exception raised two layers from the cause.
    """
    if isinstance(value, GhInvocation):
        return value
    return GhInvocation(argv="", unspawnable=f"budgeted response carried no gh outcome: {value!r}")


def record_budget_signal(*, invocation: GhInvocation, response: GithubBudgetResponse) -> None:
    """Append the durable local budget signal, when the read was measured.

    Recording here rather than at each call site is what makes the signal
    complete: a read the client turns into an `UNMEASURABLE` failure
    never reaches its caller as a response at all, and that read — the
    rate-limited one — is exactly the row an operator most needs.
    """
    snapshot = response.snapshot
    if snapshot is None:
        return
    _ = append_rate_limit_snapshot(
        snapshot=snapshot,
        argv=invocation.argv,
        status_code=response.status_code,
        classification=(
            None
            if response.status_code == _HTTP_OK
            else classify_github_failure(status_code=response.status_code, snapshot=snapshot)
        ),
    )


def gh_transport(*, execute: GhExecutor) -> GithubBudgetTransport:
    """Adapt a `gh` executor to the budgeted client's transport protocol.

    `execute` spawns an argv and reports the outcome; EVERY piece of `gh`
    knowledge — the argv, the conditional-read header, which streams
    carry the response headers, which reads are free — is applied here,
    so a call site supplies only how to run a command.
    """

    def transport(*, request: GithubBudgetRequest) -> GithubBudgetResponse:
        argv = gh_argv(resource=request.resource, headers=request.headers)
        invocation = execute(argv=argv)
        headers = gh_headers(
            invocation=invocation,
            revalidatable=argv[1:2] == [_CONDITIONAL_SUBCOMMAND],
        )
        response = GithubBudgetResponse(
            status_code=gh_status_code(invocation=invocation),
            headers=headers,
            value=invocation,
            primary_budget_spent=0 if request.resource == RATE_LIMIT_RESOURCE else 1,
            snapshot=snapshot_from_headers(headers=headers),
        )
        record_budget_signal(invocation=invocation, response=response)
        return response

    return transport
