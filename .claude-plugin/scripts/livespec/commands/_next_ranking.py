# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: see sibling next.py for the
# full prelude. Same pragma applies here for consistency.
"""Pure ranking + ISO-age helpers extracted from `next.py`.

Extracted at li-f2dk3t so the parent file's LLOC stays under
the 250-LLOC hard ceiling enforced by
`livespec_dev_tooling.checks.file_lloc`. The split is purely
organizational; the behavior is identical to the inline
original.

Stages: ISO age parsing (`_raw_fromisoformat`,
`_parse_iso_age_days`), oldest-age aggregation
(`_collect_oldest_age_days`), urgency-bucket ranking
(`_rank_revise`, `_rank`), and history-version threshold
constants.
"""

from __future__ import annotations

import datetime

from returns.result import Result, Success, safe

from livespec.errors import LivespecError, PreconditionError
from livespec.schemas.dataclasses.next_output import NextOutput

__all__: list[str] = [
    "HIGH_URGENCY_AGE_DAYS",
    "HIGH_URGENCY_COUNT_THRESHOLD",
    "MEDIUM_URGENCY_AGE_DAYS",
    "MEDIUM_URGENCY_COUNT_THRESHOLD",
    "PRUNE_HISTORY_THRESHOLD",
    "_collect_oldest_age_days",
    "_parse_iso_age_days",
    "_rank",
    "_rank_revise",
    "_raw_fromisoformat",
]


HIGH_URGENCY_COUNT_THRESHOLD = 3
MEDIUM_URGENCY_COUNT_THRESHOLD = 2
HIGH_URGENCY_AGE_DAYS = 7.0
MEDIUM_URGENCY_AGE_DAYS = 1.0
PRUNE_HISTORY_THRESHOLD = 20


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


def _collect_oldest_age_days(
    *,
    created_ats: list[str],
    now: datetime.datetime,
) -> Result[float | None, LivespecError]:
    """Compute the maximum age-days across all proposal `created_at` values.

    Returns `Success(None)` when the input list is empty. Per-
    proposal age Results are aggregated via accumulator-style
    `.bind` so the first failure short-circuits.
    """
    if not created_ats:
        return Success(None)
    aggregate: Result[list[float], LivespecError] = Success([])
    for created_at in created_ats:
        aggregate = aggregate.bind(
            lambda ages, c=created_at: _parse_iso_age_days(created_at=c, now=now).map(
                lambda age, _ages=ages: [*_ages, age],
            ),
        )
    return aggregate.map(max)


def _rank_revise(
    *,
    proposal_count: int,
    oldest_age_days: float | None,
) -> NextOutput:
    """Construct the `action=revise` NextOutput with urgency-bucket logic."""
    if proposal_count >= HIGH_URGENCY_COUNT_THRESHOLD or (
        oldest_age_days is not None and oldest_age_days >= HIGH_URGENCY_AGE_DAYS
    ):
        urgency = "high"
    elif proposal_count >= MEDIUM_URGENCY_COUNT_THRESHOLD or (
        oldest_age_days is not None and oldest_age_days >= MEDIUM_URGENCY_AGE_DAYS
    ):
        urgency = "medium"
    else:
        urgency = "low"
    age_phrase = (
        f"oldest is ~{oldest_age_days:.1f} days old"
        if oldest_age_days is not None
        else "age unknown"
    )
    reason = f"{proposal_count} proposed change(s) pending; {age_phrase}"
    return NextOutput(action="revise", reason=reason, urgency=urgency)


def _rank(
    *,
    proposal_count: int,
    oldest_age_days: float | None,
    history_version_count: int,
) -> NextOutput:
    """Pure ranker — compose a NextOutput from the three input counts."""
    if proposal_count >= 1:
        return _rank_revise(proposal_count=proposal_count, oldest_age_days=oldest_age_days)
    if history_version_count >= PRUNE_HISTORY_THRESHOLD:
        return NextOutput(
            action="prune-history",
            reason=f"{history_version_count} unpruned history versions; consider pruning",
            urgency="low",
        )
    return NextOutput(action="none", reason="No pending spec-side work", urgency="low")
