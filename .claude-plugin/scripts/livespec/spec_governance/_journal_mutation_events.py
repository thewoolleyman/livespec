"""Spec-mutation event validators, extracted from `journal`.

The three journal events that record a change to the spec itself: a
ratification, a revise decision, and a spec-PR merge. Each checks the
common envelope first and then delegates to its own shape helper in
`_journal_shapes`.

They are grouped because they share that two-step form and because the
newest of them, `_validate_spec_pr_merge`, is what pushed `journal` back
into the 201-250 LLOC soft band four days after it was emptied. The
authoring and doctor validators stay behind: they record workflow
activity rather than spec mutation.

`_validate_common` and the shape helpers all come from `_journal_shapes`,
the shared-primitives leaf, so nothing here imports from `journal` and
the two cannot form a cycle.
"""

from __future__ import annotations

from typing import Any

from livespec.spec_governance._journal_shapes import (
    _digest,
    _revise_decision_shape_error,
    _spec_pr_merge_shape_error,
    _validate_common,
)
from livespec.spec_governance.config import PROPOSAL_STEM_PATTERN

__all__: list[str] = [
    "_validate_ratification",
    "_validate_revise_decision",
    "_validate_spec_pr_merge",
]


def _validate_ratification(*, event: dict[str, Any]) -> str | None:
    common = _validate_common(
        event=event,
        required={
            "event_type",
            "proposal_stem",
            "content_digest",
            "reviewer_identity",
            "reviewer_model",
            "verdict",
            "effective_source",
            "outcome",
        },
    )
    if common is not None:
        return common
    if (
        not isinstance(event["proposal_stem"], str)
        or PROPOSAL_STEM_PATTERN.fullmatch(event["proposal_stem"]) is None
    ):
        return "ratification proposal_stem is invalid"
    if not _digest(value=event.get("content_digest")):
        return "content_digest must be lowercase sha256 hex"
    return None


def _validate_revise_decision(*, event: dict[str, Any]) -> str | None:
    common = _validate_common(
        event=event,
        required={
            "event_type",
            "proposal_stem",
            "content_digest",
            "effective_mode",
            "effective_source",
            "selected_decision",
            "decider_identity",
            "decider_model",
            "review_outcome",
            "final_outcome",
            "escalation_reason",
            "outcome",
        },
    )
    if common is not None:
        return common
    return _revise_decision_shape_error(event=event)


def _validate_spec_pr_merge(*, event: dict[str, Any]) -> str | None:
    common = _validate_common(
        event=event,
        required={
            "event_type",
            "pull_request_identity",
            "proposal_stems",
            "effective_policy",
            "effective_source",
            "registration_result",
            "required_gate_state",
            "outcome",
        },
    )
    if common is not None:
        return common
    return _spec_pr_merge_shape_error(event=event)
