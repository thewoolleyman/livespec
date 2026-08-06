"""Tests for livespec.commands._revise_ratification_timing."""

from __future__ import annotations

from livespec.commands._revise_ratification_timing import ratification_timestamp_error

__all__: list[str] = []


def test_ratification_timestamp_error_accepts_missing_ratification_timestamp() -> None:
    assert (
        ratification_timestamp_error(
            evidence={"reviewed_at": "2026-08-03T12:34:56Z"},
            min_review_age_seconds=1,
            proposal_bytes=b"proposal without front matter\n",
            revised_at=None,
        )
        is None
    )


def test_ratification_timestamp_error_rejects_malformed_ratification_timestamp() -> None:
    assert (
        ratification_timestamp_error(
            evidence={"reviewed_at": "2026-08-03T12:34:56Z"},
            min_review_age_seconds=1,
            proposal_bytes=b"proposal without front matter\n",
            revised_at="2026-08-03T12:34Z",
        )
        == "revise: ratification revised_at must be UTC ISO-8601 seconds"
    )


def test_ratification_timestamp_error_ignores_missing_proposal_front_matter() -> None:
    assert (
        ratification_timestamp_error(
            evidence={"reviewed_at": "2026-08-03T12:34:56Z"},
            min_review_age_seconds=1,
            proposal_bytes=b"proposal without front matter\n",
            revised_at="2026-08-03T12:34:57Z",
        )
        is None
    )


def test_ratification_timestamp_error_ignores_malformed_proposal_created_at() -> None:
    proposal_bytes = (
        b"---\n"
        b"topic: demo\n"
        b"author: Human <human@example.com>\n"
        b"created_at: 2026-08-03T12:34Z\n"
        b"---\n"
    )

    assert (
        ratification_timestamp_error(
            evidence={"reviewed_at": "2026-08-03T12:34:56Z"},
            min_review_age_seconds=1,
            proposal_bytes=proposal_bytes,
            revised_at="2026-08-03T12:34:57Z",
        )
        is None
    )
