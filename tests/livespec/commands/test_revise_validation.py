"""Payload-shape validation moved out of the revise supervisor.

`_check_decisions_nonempty` was extracted from `revise.py` into this module so
the supervisor drops back under the 200-LLOC soft ceiling (livespec-n33rwg.1).
It belongs here rather than in `_revise_helpers` because that module contracts
for pure compose-and-format helpers, while this one is the pre-write validation
home — and rejecting a present-but-empty `decisions[]` is validation.

The rule it enforces is not cosmetic: per the revise clause, an empty
`decisions[]` MUST fail with UsageError (exit 2) rather than falling through to
the schema's `minItems: 1`, so the operator sees the precondition they actually
violated instead of a schema-shaped exit 4.
"""

from __future__ import annotations

from typing import Any

from livespec.commands._revise_validation import _check_decisions_nonempty
from livespec.errors import UsageError
from returns.result import Failure, Success

__all__: list[str] = []


def test_empty_decisions_list_is_rejected_as_usage_error() -> None:
    """A present-but-empty decisions[] fails on the UsageError track."""
    result = _check_decisions_nonempty(payload={"decisions": []})
    assert isinstance(result, Failure), (
        "an empty decisions[] must be rejected; a revise pass with zero "
        "decisions would cut a no-op revision"
    )
    assert isinstance(result.failure(), UsageError)


def test_nonempty_decisions_list_passes_through_unchanged() -> None:
    """A populated decisions[] rides the success track carrying its payload."""
    payload: dict[str, Any] = {"decisions": [{"proposal_topic": "t"}]}
    result = _check_decisions_nonempty(payload=payload)
    assert isinstance(result, Success)
    assert result.unwrap() == payload


def test_absent_decisions_key_falls_through_to_schema_validation() -> None:
    """A missing key is NOT this guard's business — schema validation owns it."""
    payload: dict[str, Any] = {}
    result = _check_decisions_nonempty(payload=payload)
    assert isinstance(result, Success)
