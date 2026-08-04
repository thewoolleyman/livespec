"""Validated append-only digest-only spec-governance journal events."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from livespec.spec_governance.config import DOCTOR_CHECK_ID_PATTERN, PROPOSAL_STEM_PATTERN

__all__: list[str] = [
    "JournalAppend",
    "append_journal_event",
    "append_journal_payload",
    "digest_json_bytes",
]

_JOURNAL_PATH = Path("tmp") / "livespec-spec-governance-journal.jsonl"
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_VALUES = {"hard-floor", "invocation", "proposal", "global", "default"}
_OUTCOME_VALUES = {"consumed", "spawned", "selected", "blocked", "failed", "dismissed", "deferred"}
_DOCTOR_VERB_VALUES = {
    "fix-now",
    "capture-as-work-item",
    "propose-change",
    "defer",
    "dismiss",
}
_RAW_FIELD_DENYLIST = {
    "intent",
    "topic",
    "target",
    "message",
    "input_envelope",
    "finding_message",
    "proposal_content",
    "resulting_files",
    "resulting_file_content",
    "raw_content",
}


@dataclass(frozen=True, kw_only=True, slots=True)
class JournalAppend:
    """Successful journal append metadata."""

    path: Path
    digest: str


def digest_json_bytes(*, payload: object) -> str:
    """Return SHA-256 over deterministic UTF-8 JSON bytes."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def append_journal_event(*, project_root: Path, event_path: Path) -> str | JournalAppend:
    """Validate one event JSON file and append it as one JSONL row."""
    try:
        raw = event_path.read_text(encoding="utf-8")
        event = cast(object, json.loads(raw))
    except (OSError, json.JSONDecodeError) as exc:
        return f"journal event unreadable or malformed: {exc}"
    if not isinstance(event, dict):
        return "journal event must be a JSON object"
    return append_journal_payload(
        project_root=project_root,
        event=cast(dict[str, Any], event),
    )


def append_journal_payload(*, project_root: Path, event: dict[str, Any]) -> str | JournalAppend:
    """Validate and append an in-memory digest-only event, failing closed on I/O."""
    validation_error = _validate_event(event=event)
    if validation_error is not None:
        return validation_error
    canonical = json.dumps(event, sort_keys=True, separators=(",", ":"))
    journal_path = project_root / _JOURNAL_PATH
    try:
        journal_path.parent.mkdir(parents=True, exist_ok=True)
        with journal_path.open("a", encoding="utf-8") as handle:
            _ = handle.write(f"{canonical}\n")
    except OSError as exc:
        return f"journal append failed: {exc}"
    return JournalAppend(
        path=_JOURNAL_PATH,
        digest=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    )


def _validate_event(*, event: dict[str, Any]) -> str | None:
    if any(field in event for field in _RAW_FIELD_DENYLIST):
        return "journal event must carry digests, not raw intent/message fields"
    event_type = event.get("event_type")
    if event_type == "authoring_auto_consumption":
        return _validate_authoring(event=event)
    if event_type == "doctor_disposition":
        return _validate_doctor(event=event)
    if event_type == "ratification_review":
        return _validate_ratification(event=event)
    if event_type == "revise_decision":
        return _validate_revise_decision(event=event)
    return (
        "journal event_type must be authoring_auto_consumption, "
        "doctor_disposition, ratification_review, or revise_decision"
    )


def _validate_common(*, event: dict[str, Any], required: set[str]) -> str | None:
    extra_missing = sorted(required.difference(event))
    if extra_missing:
        return f"journal event missing required fields: {extra_missing}"
    if event.get("effective_source") not in _SOURCE_VALUES:
        return "journal effective_source is invalid"
    if event.get("outcome") not in _OUTCOME_VALUES:
        return "journal outcome is invalid"
    return None


def _validate_authoring(*, event: dict[str, Any]) -> str | None:
    common = _validate_common(
        event=event,
        required={
            "event_type",
            "operation",
            "governing_key",
            "effective_source",
            "input_envelope_digest",
            "outcome",
        },
    )
    if common is not None:
        return common
    if event["operation"] not in {"propose-change", "critique"}:
        return "authoring operation is invalid"
    if not _digest(value=event.get("input_envelope_digest")):
        return "input_envelope_digest must be lowercase sha256 hex"
    return None


def _validate_doctor(*, event: dict[str, Any]) -> str | None:
    common = _validate_common(
        event=event,
        required={
            "event_type",
            "check_id",
            "spec_root",
            "finding_message_digest",
            "selected_verb",
            "governing_key",
            "effective_source",
            "outcome",
        },
    )
    if common is not None:
        return common
    if (
        not isinstance(event["check_id"], str)
        or DOCTOR_CHECK_ID_PATTERN.fullmatch(event["check_id"]) is None
    ):
        return "doctor check_id is invalid"
    if not _digest(value=event.get("finding_message_digest")):
        return "finding_message_digest must be lowercase sha256 hex"
    if event["selected_verb"] not in _DOCTOR_VERB_VALUES:
        return "doctor selected_verb is invalid"
    return None


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


def _revise_decision_shape_error(*, event: dict[str, Any]) -> str | None:
    stem = event.get("proposal_stem")
    if not isinstance(stem, str) or PROPOSAL_STEM_PATTERN.fullmatch(stem) is None:
        return "revise decision proposal_stem is invalid"
    if not _digest(value=event.get("content_digest")):
        return "content_digest must be lowercase sha256 hex"
    if event.get("effective_mode") not in {"delegated", "consensus"}:
        return "revise decision effective_mode is invalid"
    if event.get("selected_decision") not in {"accept", "modify", "reject"}:
        return "revise decision selected_decision is invalid"
    required_text = ("decider_identity", "decider_model", "review_outcome", "final_outcome")
    if any(
        not isinstance(event.get(field), str) or not event[field] for field in required_text
    ) or not isinstance(event.get("escalation_reason"), str):
        return "revise decision identity, model, outcomes, and escalation must be strings"
    return None


def _digest(*, value: object) -> bool:
    return isinstance(value, str) and _SHA256_PATTERN.fullmatch(value) is not None
