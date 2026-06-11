# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: see sibling next.py for the
# full prelude. Same pragma applies here for consistency.
"""Pure ranking, pagination, and ISO-age helpers for `next.py`.

Extracted from `next.py` so the parent file's LLOC stays under
the 250-LLOC hard ceiling enforced by
`livespec_dev_tooling.checks.file_lloc`.

Per `SPECIFICATION/contracts.md` §"/livespec:next spec-side
thin-transport skill" → §"Ranker semantics" + §"`prune-history`
ordering invariant": the ranker enumerates ALL ripe candidates
(one `revise` candidate per pending proposal, plus one
`prune-history` candidate when the unpruned history version
count reaches the threshold), sorts by action tier
(prune-history strictly below every other action), urgency
descending, then `target` lexicographic, and applies
offset/limit last to produce the returned slice.

Stages: threshold extraction from the `.livespec.jsonc` body
(`_threshold_from_config_text`, per §"`.livespec.jsonc`
configuration"), ISO age parsing (`_raw_fromisoformat`,
`_parse_iso_age_days`), per-proposal age aggregation
(`_collect_proposal_ages`), candidate enumeration + sorting
(`_revise_urgency`, `_enumerate_candidates`), pagination
(`_paginate`), and payload shaping (`_output_payload`).
"""

from __future__ import annotations

import datetime
from typing import Any

from returns.result import Failure, Result, Success, safe

from livespec.errors import LivespecError, PreconditionError
from livespec.parse import jsonc
from livespec.schemas.dataclasses.next_output import (
    NextCandidate,
    NextOutput,
    NextPagination,
)

__all__: list[str] = [
    "ACTION_TIER",
    "HIGH_URGENCY_AGE_DAYS",
    "HIGH_URGENCY_COUNT_THRESHOLD",
    "MEDIUM_URGENCY_AGE_DAYS",
    "MEDIUM_URGENCY_COUNT_THRESHOLD",
    "PRUNE_HISTORY_THRESHOLD",
    "URGENCY_RANK",
    "_collect_proposal_ages",
    "_enumerate_candidates",
    "_output_payload",
    "_paginate",
    "_parse_iso_age_days",
    "_raw_fromisoformat",
    "_revise_urgency",
    "_threshold_from_config_text",
]


HIGH_URGENCY_COUNT_THRESHOLD = 3
MEDIUM_URGENCY_COUNT_THRESHOLD = 2
HIGH_URGENCY_AGE_DAYS = 7.0
MEDIUM_URGENCY_AGE_DAYS = 1.0
# Default per `SPECIFICATION/contracts.md` §"`.livespec.jsonc`
# configuration": applies when `next.prune_history_threshold` is
# absent from the project's `.livespec.jsonc` (or the config file
# itself is absent). A present key overrides it per invocation via
# `_threshold_from_config_text`.
PRUNE_HISTORY_THRESHOLD = 20

# Sort tier per action, per §"`prune-history` ordering invariant":
# prune-history sorts strictly below EVERY other action in the
# enumeration, independent of urgency. The reference ranker emits
# only `revise` and `prune-history` candidates; the remaining
# actions carry tiers so the comparator is total over the schema
# enumeration.
ACTION_TIER: dict[str, int] = {
    "revise": 0,
    "propose-change": 1,
    "critique": 2,
    "none": 3,
    "prune-history": 4,
}

# Urgency descending: high sorts before medium sorts before low.
URGENCY_RANK: dict[str, int] = {"high": 0, "medium": 1, "low": 2}


def _threshold_from_config_text(*, text: str) -> Result[int, LivespecError]:
    """Extract `next.prune_history_threshold` from a `.livespec.jsonc` body.

    Per `SPECIFICATION/contracts.md` §"`.livespec.jsonc`
    configuration": the key value MUST be a positive integer; a
    present-but-non-positive-integer value (including a boolean —
    a `bool` is an `int` subclass that would otherwise coerce
    silently) yields `Failure(PreconditionError)` naming the
    offending key and value, which the supervisor lifts to exit
    3. When the key is absent the default
    `PRUNE_HISTORY_THRESHOLD` (20) applies. Malformed JSONC is
    treated as key-absent defensively — `livespec_jsonc_valid`
    is the dedicated doctor mechanism for surfacing malformed
    configs (mirrors the prune-history wrapper's
    `_resolve_skip_from_config_text` precedent).
    """
    parsed: dict[str, object] = jsonc.loads(text=text).value_or({})
    section = parsed.get("next")
    if not isinstance(section, dict) or "prune_history_threshold" not in section:
        return Success(PRUNE_HISTORY_THRESHOLD)
    value = section["prune_history_threshold"]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return Failure(
            PreconditionError(
                "next: .livespec.jsonc key next.prune_history_threshold "
                f"must be a positive integer, got {value!r}",
            ),
        )
    return Success(value)


@safe(exceptions=(ValueError,))
def _raw_fromisoformat(*, normalized: str) -> datetime.datetime:
    """Decorator-lifted call into `datetime.fromisoformat`."""
    return datetime.datetime.fromisoformat(normalized)


def _parse_iso_age_days(
    *,
    created_at: str,
    now: datetime.datetime,
) -> Result[float, LivespecError]:
    """Compute the age in days between `created_at` (ISO 8601) and `now`.

    Accepts the canonical `YYYY-MM-DDTHH:MM:SSZ` shape per
    `proposed_change_front_matter.schema.json`'s `date-time`
    format. The trailing `Z` is stripped and `+00:00` is
    appended before `datetime.fromisoformat` (stdlib 3.10 does
    not accept the `Z` suffix directly).
    """
    base = created_at.rstrip("Z")
    normalized = f"{base}+00:00"
    return (
        _raw_fromisoformat(normalized=normalized)
        .alt(
            lambda exc: PreconditionError(f"next: unparseable created_at {created_at!r}: {exc}"),
        )
        .map(
            lambda parsed: (now - parsed).total_seconds() / 86400.0,
        )
    )


def _collect_proposal_ages(
    *,
    entries: list[tuple[str, str]],
    now: datetime.datetime,
) -> Result[list[tuple[str, float]], LivespecError]:
    """Map each `(target, created_at)` entry to `(target, age_days)`.

    Returns `Success([])` when the input list is empty. Per-
    proposal age Results are aggregated via accumulator-style
    `.bind` so the first failure short-circuits.
    """
    aggregate: Result[list[tuple[str, float]], LivespecError] = Success([])
    for target, created_at in entries:
        aggregate = aggregate.bind(
            lambda ages, t=target, c=created_at: _parse_iso_age_days(
                created_at=c,
                now=now,
            ).map(
                lambda age, _ages=ages, _t=t: [*_ages, (_t, age)],
            ),
        )
    return aggregate


def _revise_urgency(
    *,
    proposal_count: int,
    age_days: float,
) -> str:
    """Bucket one revise candidate's urgency from queue depth + its age.

    The two axes are OR-ed so either a deep queue OR a long-
    stale proposal lifts urgency: count ≥ 3 OR age ≥ 7 days →
    `high`; count ≥ 2 OR age ≥ 1 day → `medium`; otherwise
    `low`. The depth axis applies the full queue depth to every
    candidate; the age axis is per-proposal.
    """
    if proposal_count >= HIGH_URGENCY_COUNT_THRESHOLD or age_days >= HIGH_URGENCY_AGE_DAYS:
        return "high"
    if proposal_count >= MEDIUM_URGENCY_COUNT_THRESHOLD or age_days >= MEDIUM_URGENCY_AGE_DAYS:
        return "medium"
    return "low"


def _enumerate_candidates(
    *,
    proposal_ages: list[tuple[str, float]],
    history_version_count: int,
    prune_history_threshold: int = PRUNE_HISTORY_THRESHOLD,
) -> list[NextCandidate]:
    """Enumerate ALL ripe candidates, sorted per §"Ranker semantics".

    One `revise` candidate per pending proposal (target = the
    spec-target-relative proposal path) plus one `prune-history`
    candidate when the history version count reaches
    `prune_history_threshold` (no target — pruning addresses a
    version range). The threshold is resolved per invocation from
    `.livespec.jsonc`'s `next.prune_history_threshold` key by the
    supervisor (default `PRUNE_HISTORY_THRESHOLD` when absent,
    per §"`.livespec.jsonc` configuration"). Sort key: action
    tier (prune-history strictly last), urgency descending, then
    target lexicographic. An empty result IS the no-work signal.
    """
    proposal_count = len(proposal_ages)
    candidates = [
        NextCandidate(
            action="revise",
            reason=(
                f"proposed change {target} pending; ~{age_days:.1f} days old; "
                f"queue depth {proposal_count}"
            ),
            urgency=_revise_urgency(proposal_count=proposal_count, age_days=age_days),
            target=target,
        )
        for target, age_days in proposal_ages
    ]
    if history_version_count >= prune_history_threshold:
        candidates.append(
            NextCandidate(
                action="prune-history",
                reason=f"{history_version_count} unpruned history versions; consider pruning",
                urgency="low",
            ),
        )
    return sorted(
        candidates,
        key=lambda candidate: (
            ACTION_TIER[candidate.action],
            URGENCY_RANK[candidate.urgency],
            candidate.target or "",
        ),
    )


def _paginate(
    *,
    candidates: list[NextCandidate],
    offset: int,
    limit: int,
) -> NextOutput:
    """Apply offset/limit to the ranked list and build the NextOutput.

    Per §"Output schema": `total` counts ripe candidates BEFORE
    the slice; `has_more` is `true` iff
    `offset + len(candidates) < total`; `offset >= total` yields
    an empty window with `has_more: false`.
    """
    total = len(candidates)
    window = candidates[offset : offset + limit]
    return NextOutput(
        candidates=tuple(window),
        pagination=NextPagination(
            offset=offset,
            limit=limit,
            total=total,
            has_more=offset + len(window) < total,
        ),
    )


def _output_payload(*, output: NextOutput) -> dict[str, Any]:
    """Shape the NextOutput dataclass into the wire payload dict.

    Candidate dicts omit the `target` key when the dataclass
    field is None (the schema marks `target` optional; emitting
    `"target": null` would violate `type: string`).
    """
    candidates: list[dict[str, Any]] = []
    for candidate in output.candidates:
        item: dict[str, Any] = {
            "action": candidate.action,
            "reason": candidate.reason,
            "urgency": candidate.urgency,
        }
        if candidate.target is not None:
            item["target"] = candidate.target
        candidates.append(item)
    return {
        "candidates": candidates,
        "pagination": {
            "offset": output.pagination.offset,
            "limit": output.pagination.limit,
            "total": output.pagination.total,
            "has_more": output.pagination.has_more,
        },
    }
