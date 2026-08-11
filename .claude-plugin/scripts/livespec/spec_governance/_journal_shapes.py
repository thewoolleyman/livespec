"""Shared journal-event shape primitives, extracted from `journal`.

Holds the two value sets and the digest predicate that every journal
validator leans on, plus the revise-decision and drift-acceptance shape
checks that are their heaviest consumer.

The primitives travel WITH those consumers rather than staying behind,
because that is what keeps this module a leaf: `journal` imports from
here and nothing here imports from `journal`, so the two cannot form an
import cycle. Leaving `_digest` in the parent would have inverted that
and required the cycle.
"""

from __future__ import annotations

import re
from typing import Any, cast

from livespec.spec_governance.config import PROPOSAL_STEM_PATTERN

__all__: list[str] = [
    "_digest",
    "_drift_acceptance_shape_error",
    "_revise_decision_shape_error",
    "_spec_pr_merge_shape_error",
]

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_VALUES = {"hard-floor", "invocation", "proposal", "global", "default"}
_REGISTRATION_RESULT_VALUES = {"registered", "blocked", "failed"}
_REQUIRED_GATE_STATE_VALUES = {"pending", "green", "red", "unavailable"}


def _digest(*, value: object) -> bool:
    return isinstance(value, str) and _SHA256_PATTERN.fullmatch(value) is not None


def _revise_decision_shape_error(*, event: dict[str, Any]) -> str | None:
    basic_error = _revise_decision_basic_shape_error(event=event)
    if basic_error is not None:
        return basic_error
    drift_error = _drift_acceptance_shape_error(event=event)
    if drift_error is not None:
        return drift_error
    if event.get("selected_decision") not in {"accept", "modify", "reject"}:
        return "revise decision selected_decision is invalid"
    return _revise_decision_text_shape_error(event=event)


def _revise_decision_basic_shape_error(*, event: dict[str, Any]) -> str | None:
    stem = event.get("proposal_stem")
    if not isinstance(stem, str) or PROPOSAL_STEM_PATTERN.fullmatch(stem) is None:
        return "revise decision proposal_stem is invalid"
    if not _digest(value=event.get("content_digest")):
        return "content_digest must be lowercase sha256 hex"
    if event.get("effective_mode") not in {"delegated", "consensus"}:
        return "revise decision effective_mode is invalid"
    return None


def _revise_decision_text_shape_error(*, event: dict[str, Any]) -> str | None:
    required_text = ("decider_identity", "decider_model", "review_outcome", "final_outcome")
    if any(
        not isinstance(event.get(field), str) or not event[field] for field in required_text
    ) or not isinstance(event.get("escalation_reason"), str):
        return "revise decision identity, model, outcomes, and escalation must be strings"
    return None


def _drift_acceptance_shape_error(*, event: dict[str, Any]) -> str | None:
    drift_fields = {
        "effective_drift_acceptance_mode",
        "effective_drift_acceptance_source",
        "consensus_evidence_digest",
    }
    present = drift_fields.intersection(event)
    if not present:
        return None
    if present != drift_fields:
        return "drift revise decision fields must be present together"
    if event.get("effective_drift_acceptance_mode") not in {"human", "consensus"}:
        return "effective_drift_acceptance_mode is invalid"
    if event.get("effective_drift_acceptance_source") not in _SOURCE_VALUES:
        return "effective_drift_acceptance_source is invalid"
    if not _digest(value=event.get("consensus_evidence_digest")):
        return "consensus_evidence_digest must be lowercase sha256 hex"
    return None


def _spec_pr_merge_shape_error(*, event: dict[str, Any]) -> str | None:
    basic_error = _spec_pr_merge_basic_shape_error(event=event)
    if basic_error is not None:
        return basic_error
    if "merge_evidence_digest" in event and not _digest(
        value=event.get("merge_evidence_digest"),
    ):
        return "merge_evidence_digest must be lowercase sha256 hex"
    return None


def _spec_pr_merge_basic_shape_error(*, event: dict[str, Any]) -> str | None:
    identity = event.get("pull_request_identity")
    if not isinstance(identity, str) or not identity:
        return "spec_pr_merge pull_request_identity is invalid"
    if _proposal_stems_error(value=event.get("proposal_stems")):
        return "spec_pr_merge proposal_stems is invalid"
    if event.get("effective_policy") != "auto-on-green":
        return "spec_pr_merge effective_policy is invalid"
    if event.get("registration_result") not in _REGISTRATION_RESULT_VALUES:
        return "spec_pr_merge registration_result is invalid"
    if event.get("required_gate_state") not in _REQUIRED_GATE_STATE_VALUES:
        return "spec_pr_merge required_gate_state is invalid"
    return None


def _proposal_stems_error(*, value: object) -> bool:
    if not isinstance(value, list) or not value:
        return True
    stems: set[str] = set()
    items = cast(list[object], value)
    for item in items:
        if not isinstance(item, str) or PROPOSAL_STEM_PATTERN.fullmatch(item) is None:
            return True
        stems.add(item)
    return len(stems) != len(items)
