"""Tests for livespec.commands._next_ranking.

Pure-ranker + ISO-age helpers extracted from `next.py` to keep
the parent file under the 250-LLOC hard ceiling. The functions
are exercised indirectly through
`tests/livespec/commands/test_next.py` end-to-end paths; this
module pins direct per-helper coverage for the mirror-paired
test contract per `tests/CLAUDE.md`.
"""

from __future__ import annotations

import datetime

from livespec.commands._next_ranking import (
    HIGH_URGENCY_AGE_DAYS,
    HIGH_URGENCY_COUNT_THRESHOLD,
    MEDIUM_URGENCY_AGE_DAYS,
    MEDIUM_URGENCY_COUNT_THRESHOLD,
    PRUNE_HISTORY_THRESHOLD,
    _collect_oldest_age_days,
    _parse_iso_age_days,
    _rank,
    _rank_revise,
    _raw_fromisoformat,
)
from livespec.errors import PreconditionError
from returns.result import Failure, Success

__all__: list[str] = []


def test_raw_fromisoformat_success() -> None:
    """Parses a canonical ISO-8601 string."""
    result = _raw_fromisoformat(normalized="2026-01-01T00:00:00+00:00")
    match result:
        case Success(parsed):
            assert parsed.year == 2026
        case _:
            msg = f"expected Success, got {result!r}"
            raise AssertionError(msg)


def test_raw_fromisoformat_failure_on_invalid() -> None:
    """Invalid ISO string -> Failure(ValueError)."""
    result = _raw_fromisoformat(normalized="not-an-iso-date")
    match result:
        case Failure(_):
            pass
        case _:
            msg = f"expected Failure on invalid input, got {result!r}"
            raise AssertionError(msg)


def test_parse_iso_age_days_returns_age_in_days() -> None:
    """Compute age between two ISO timestamps in days."""
    now = datetime.datetime(2026, 1, 11, 0, 0, 0, tzinfo=datetime.timezone.utc)
    result = _parse_iso_age_days(created_at="2026-01-01T00:00:00Z", now=now)
    match result:
        case Success(age):
            assert age == 10.0
        case _:
            msg = f"expected Success(10.0), got {result!r}"
            raise AssertionError(msg)


def test_parse_iso_age_days_returns_precondition_error_on_malformed() -> None:
    """Unparseable created_at -> Failure(PreconditionError)."""
    now = datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    result = _parse_iso_age_days(created_at="garbage", now=now)
    match result:
        case Failure(PreconditionError()):
            pass
        case _:
            msg = f"expected Failure(PreconditionError), got {result!r}"
            raise AssertionError(msg)


def test_collect_oldest_age_days_empty_returns_none() -> None:
    """Empty input -> Success(None)."""
    now = datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    result = _collect_oldest_age_days(created_ats=[], now=now)
    match result:
        case Success(value):
            assert value is None
        case _:
            msg = f"expected Success(None), got {result!r}"
            raise AssertionError(msg)


def test_collect_oldest_age_days_returns_max_age() -> None:
    """Returns the maximum age among the inputs."""
    now = datetime.datetime(2026, 1, 11, 0, 0, 0, tzinfo=datetime.timezone.utc)
    result = _collect_oldest_age_days(
        created_ats=[
            "2026-01-10T00:00:00Z",  # 1 day old
            "2026-01-05T00:00:00Z",  # 6 days old (oldest)
            "2026-01-08T00:00:00Z",  # 3 days old
        ],
        now=now,
    )
    match result:
        case Success(age):
            assert age == 6.0
        case _:
            msg = f"expected Success(6.0), got {result!r}"
            raise AssertionError(msg)


def test_collect_oldest_age_days_propagates_first_failure() -> None:
    """First unparseable input short-circuits with Failure(PreconditionError)."""
    now = datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    result = _collect_oldest_age_days(
        created_ats=["2026-01-01T00:00:00Z", "garbage"],
        now=now,
    )
    match result:
        case Failure(PreconditionError()):
            pass
        case _:
            msg = f"expected Failure(PreconditionError), got {result!r}"
            raise AssertionError(msg)


def test_rank_revise_high_urgency_on_high_count() -> None:
    """`proposal_count >= HIGH_URGENCY_COUNT_THRESHOLD` -> urgency=high."""
    output = _rank_revise(
        proposal_count=HIGH_URGENCY_COUNT_THRESHOLD,
        oldest_age_days=0.0,
    )
    assert output.action == "revise"
    assert output.urgency == "high"


def test_rank_revise_high_urgency_on_high_age() -> None:
    """`oldest_age_days >= HIGH_URGENCY_AGE_DAYS` -> urgency=high."""
    output = _rank_revise(proposal_count=1, oldest_age_days=HIGH_URGENCY_AGE_DAYS)
    assert output.action == "revise"
    assert output.urgency == "high"


def test_rank_revise_medium_urgency_on_medium_count() -> None:
    """`proposal_count >= MEDIUM_URGENCY_COUNT_THRESHOLD` -> urgency=medium."""
    output = _rank_revise(proposal_count=MEDIUM_URGENCY_COUNT_THRESHOLD, oldest_age_days=0.0)
    assert output.action == "revise"
    assert output.urgency == "medium"


def test_rank_revise_medium_urgency_on_medium_age() -> None:
    """`oldest_age_days >= MEDIUM_URGENCY_AGE_DAYS` -> urgency=medium."""
    output = _rank_revise(proposal_count=1, oldest_age_days=MEDIUM_URGENCY_AGE_DAYS)
    assert output.action == "revise"
    assert output.urgency == "medium"


def test_rank_revise_low_urgency_otherwise() -> None:
    """Below all thresholds -> urgency=low."""
    output = _rank_revise(proposal_count=1, oldest_age_days=0.5)
    assert output.action == "revise"
    assert output.urgency == "low"


def test_rank_revise_age_phrase_when_none() -> None:
    """`oldest_age_days=None` -> reason contains 'age unknown'."""
    output = _rank_revise(proposal_count=1, oldest_age_days=None)
    assert "age unknown" in output.reason


def test_rank_returns_revise_when_queue_nonempty() -> None:
    """`proposal_count >= 1` -> action=revise."""
    output = _rank(proposal_count=1, oldest_age_days=0.5, history_version_count=5)
    assert output.action == "revise"


def test_rank_returns_prune_history_when_threshold_exceeded() -> None:
    """Empty queue + history >= threshold -> action=prune-history."""
    output = _rank(
        proposal_count=0,
        oldest_age_days=None,
        history_version_count=PRUNE_HISTORY_THRESHOLD,
    )
    assert output.action == "prune-history"
    assert output.urgency == "low"


def test_rank_returns_none_otherwise() -> None:
    """Empty queue + short history -> action=none."""
    output = _rank(proposal_count=0, oldest_age_days=None, history_version_count=1)
    assert output.action == "none"
    assert output.urgency == "low"
