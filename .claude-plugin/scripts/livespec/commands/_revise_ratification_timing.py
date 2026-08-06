"""Timestamp-order validation for revise ratification evidence."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, cast

from returns.result import Failure

from livespec.parse import front_matter

__all__: list[str] = [
    "DEFAULT_MIN_REVIEW_AGE_SECONDS",
    "ratification_timestamp_error",
]

DEFAULT_MIN_REVIEW_AGE_SECONDS = 1

_UTC_SECONDS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def ratification_timestamp_error(
    *,
    evidence: dict[Any, Any],
    min_review_age_seconds: int,
    proposal_bytes: bytes,
    revised_at: str | None,
) -> str | None:
    """Validate review evidence timestamps against proposal and ratification time."""
    reviewed_at = evidence.get("reviewed_at")
    if not isinstance(reviewed_at, str) or not _UTC_SECONDS.fullmatch(reviewed_at):
        return "revise: ratification reviewed_at must be UTC ISO-8601 seconds"
    if revised_at is None:
        return None
    if not _UTC_SECONDS.fullmatch(revised_at):
        return "revise: ratification revised_at must be UTC ISO-8601 seconds"
    reviewed = _parse_utc_seconds(value=reviewed_at)
    created_at = _proposal_created_at(proposal_bytes=proposal_bytes)
    if created_at is not None and reviewed < _parse_utc_seconds(value=created_at):
        return "revise: ratification reviewed_at must not precede proposal created_at"
    minimum_reviewed_before = reviewed + timedelta(seconds=min_review_age_seconds)
    if minimum_reviewed_before > _parse_utc_seconds(value=revised_at):
        return (
            "revise: ratification reviewed_at must be strictly before "
            "revised_at by the configured threshold"
        )
    return None


def _parse_utc_seconds(*, value: str) -> datetime:
    return datetime.fromisoformat(value.removesuffix("Z") + "+00:00")


def _proposal_created_at(*, proposal_bytes: bytes) -> str | None:
    text = proposal_bytes.decode("utf-8", errors="replace")
    parsed = front_matter.parse_front_matter(text=text)
    if isinstance(parsed, Failure):
        return None
    created_at = cast(dict[str, object], parsed.unwrap()).get("created_at")
    if isinstance(created_at, str) and _UTC_SECONDS.fullmatch(created_at):
        return created_at
    return None
