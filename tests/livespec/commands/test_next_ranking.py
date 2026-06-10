"""Tests for livespec.commands._next_ranking.

Pure ranking, pagination, and ISO-age helpers extracted from
`next.py` to keep the parent file under the 250-LLOC hard
ceiling. The functions are exercised indirectly through
`tests/livespec/commands/test_next.py` end-to-end paths; this
module pins direct per-helper coverage for the mirror-paired
test contract per `tests/CLAUDE.md`.
"""

from __future__ import annotations

import datetime

from livespec.commands._next_ranking import (
    ACTION_TIER,
    HIGH_URGENCY_AGE_DAYS,
    HIGH_URGENCY_COUNT_THRESHOLD,
    MEDIUM_URGENCY_AGE_DAYS,
    MEDIUM_URGENCY_COUNT_THRESHOLD,
    PRUNE_HISTORY_THRESHOLD,
    _collect_proposal_ages,
    _enumerate_candidates,
    _output_payload,
    _paginate,
    _parse_iso_age_days,
    _raw_fromisoformat,
    _revise_urgency,
)
from livespec.errors import PreconditionError
from livespec.schemas.dataclasses.next_output import NextCandidate
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


def test_collect_proposal_ages_empty_returns_empty_list() -> None:
    """Empty input -> Success([])."""
    now = datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    result = _collect_proposal_ages(entries=[], now=now)
    assert result == Success([])


def test_collect_proposal_ages_maps_each_entry_to_target_age_pair() -> None:
    """Each (target, created_at) maps to (target, age_days)."""
    now = datetime.datetime(2026, 1, 11, 0, 0, 0, tzinfo=datetime.timezone.utc)
    result = _collect_proposal_ages(
        entries=[
            ("proposed_changes/a.md", "2026-01-10T00:00:00Z"),
            ("proposed_changes/b.md", "2026-01-05T00:00:00Z"),
        ],
        now=now,
    )
    match result:
        case Success(ages):
            assert ages == [
                ("proposed_changes/a.md", 1.0),
                ("proposed_changes/b.md", 6.0),
            ]
        case _:
            msg = f"expected Success(pairs), got {result!r}"
            raise AssertionError(msg)


def test_collect_proposal_ages_propagates_first_failure() -> None:
    """First unparseable input short-circuits with Failure(PreconditionError)."""
    now = datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    result = _collect_proposal_ages(
        entries=[
            ("proposed_changes/a.md", "2026-01-01T00:00:00Z"),
            ("proposed_changes/b.md", "garbage"),
        ],
        now=now,
    )
    match result:
        case Failure(PreconditionError()):
            pass
        case _:
            msg = f"expected Failure(PreconditionError), got {result!r}"
            raise AssertionError(msg)


def test_revise_urgency_high_on_high_count() -> None:
    """`proposal_count >= HIGH_URGENCY_COUNT_THRESHOLD` -> high."""
    urgency = _revise_urgency(proposal_count=HIGH_URGENCY_COUNT_THRESHOLD, age_days=0.0)
    assert urgency == "high"


def test_revise_urgency_high_on_high_age() -> None:
    """`age_days >= HIGH_URGENCY_AGE_DAYS` -> high."""
    urgency = _revise_urgency(proposal_count=1, age_days=HIGH_URGENCY_AGE_DAYS)
    assert urgency == "high"


def test_revise_urgency_medium_on_medium_count() -> None:
    """`proposal_count >= MEDIUM_URGENCY_COUNT_THRESHOLD` -> medium."""
    urgency = _revise_urgency(proposal_count=MEDIUM_URGENCY_COUNT_THRESHOLD, age_days=0.0)
    assert urgency == "medium"


def test_revise_urgency_medium_on_medium_age() -> None:
    """`age_days >= MEDIUM_URGENCY_AGE_DAYS` -> medium."""
    urgency = _revise_urgency(proposal_count=1, age_days=MEDIUM_URGENCY_AGE_DAYS)
    assert urgency == "medium"


def test_revise_urgency_low_otherwise() -> None:
    """Below all thresholds -> low."""
    urgency = _revise_urgency(proposal_count=1, age_days=0.5)
    assert urgency == "low"


def test_enumerate_candidates_emits_one_revise_per_proposal() -> None:
    """Each (target, age) pair yields one revise candidate carrying its target."""
    candidates = _enumerate_candidates(
        proposal_ages=[
            ("proposed_changes/a.md", 0.5),
            ("proposed_changes/b.md", 0.25),
        ],
        history_version_count=0,
    )
    assert [c.action for c in candidates] == ["revise", "revise"]
    assert [c.target for c in candidates] == [
        "proposed_changes/a.md",
        "proposed_changes/b.md",
    ]
    assert all(len(c.reason) > 0 for c in candidates)


def test_enumerate_candidates_sorts_urgency_descending_then_target() -> None:
    """Within the revise tier: urgency desc, then target lexicographic."""
    candidates = _enumerate_candidates(
        proposal_ages=[
            ("proposed_changes/a-fresh.md", 0.1),
            ("proposed_changes/z-old.md", 10.0),
        ],
        history_version_count=0,
    )
    assert [c.target for c in candidates] == [
        "proposed_changes/z-old.md",
        "proposed_changes/a-fresh.md",
    ]
    assert [c.urgency for c in candidates] == ["high", "medium"]


def test_enumerate_candidates_appends_prune_history_at_threshold() -> None:
    """`history_version_count >= threshold` adds a target-less low candidate."""
    candidates = _enumerate_candidates(
        proposal_ages=[],
        history_version_count=PRUNE_HISTORY_THRESHOLD,
    )
    assert len(candidates) == 1
    assert candidates[0].action == "prune-history"
    assert candidates[0].urgency == "low"
    assert candidates[0].target is None


def test_enumerate_candidates_ranks_prune_history_strictly_last() -> None:
    """Per the ordering invariant: prune-history sorts below revise."""
    candidates = _enumerate_candidates(
        proposal_ages=[("proposed_changes/a.md", 0.1)],
        history_version_count=PRUNE_HISTORY_THRESHOLD + 5,
    )
    assert [c.action for c in candidates] == ["revise", "prune-history"]


def test_enumerate_candidates_empty_inputs_yield_empty_list() -> None:
    """No proposals + short history -> [] (the no-work signal)."""
    candidates = _enumerate_candidates(
        proposal_ages=[],
        history_version_count=PRUNE_HISTORY_THRESHOLD - 1,
    )
    assert candidates == []


def test_action_tier_orders_prune_history_below_every_other_action() -> None:
    """ACTION_TIER pins prune-history strictly below the rest of the enum."""
    prune_tier = ACTION_TIER["prune-history"]
    others = {action: tier for action, tier in ACTION_TIER.items() if action != "prune-history"}
    assert all(tier < prune_tier for tier in others.values())


def test_paginate_slices_and_reports_totals() -> None:
    """offset/limit slice the ranked list; total counts pre-slice."""
    candidates = [
        NextCandidate(action="revise", reason=f"r{i}", urgency="low", target=f"t{i}.md")
        for i in range(3)
    ]
    output = _paginate(candidates=candidates, offset=0, limit=2)
    assert [c.target for c in output.candidates] == ["t0.md", "t1.md"]
    assert output.pagination.offset == 0
    assert output.pagination.limit == 2
    assert output.pagination.total == 3
    assert output.pagination.has_more is True


def test_paginate_offset_beyond_total_yields_empty_window() -> None:
    """`offset >= total` -> empty candidates + has_more false."""
    candidates = [
        NextCandidate(action="revise", reason="r", urgency="low", target="t.md"),
    ]
    output = _paginate(candidates=candidates, offset=4, limit=5)
    assert output.candidates == ()
    assert output.pagination.total == 1
    assert output.pagination.has_more is False


def test_paginate_window_draining_list_has_no_more() -> None:
    """A window that reaches the end of the list reports has_more false."""
    candidates = [
        NextCandidate(action="revise", reason=f"r{i}", urgency="low", target=f"t{i}.md")
        for i in range(2)
    ]
    output = _paginate(candidates=candidates, offset=1, limit=5)
    assert [c.target for c in output.candidates] == ["t1.md"]
    assert output.pagination.has_more is False


def test_output_payload_omits_target_key_when_none() -> None:
    """A None target keeps the `target` key out of the candidate dict."""
    output = _paginate(
        candidates=[
            NextCandidate(action="prune-history", reason="r", urgency="low"),
        ],
        offset=0,
        limit=5,
    )
    payload = _output_payload(output=output)
    assert payload["candidates"] == [
        {"action": "prune-history", "reason": "r", "urgency": "low"},
    ]
    assert payload["pagination"] == {
        "offset": 0,
        "limit": 5,
        "total": 1,
        "has_more": False,
    }


def test_output_payload_includes_target_key_when_present() -> None:
    """A str target serializes as the `target` key on the candidate dict."""
    output = _paginate(
        candidates=[
            NextCandidate(action="revise", reason="r", urgency="high", target="t.md"),
        ],
        offset=0,
        limit=5,
    )
    payload = _output_payload(output=output)
    assert payload["candidates"] == [
        {"action": "revise", "reason": "r", "urgency": "high", "target": "t.md"},
    ]
