# pyright: reportUnknownMemberType=none
"""Ratification-evidence validation for mutating revise decisions."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, cast

from returns.io import IOResult

from livespec.errors import LivespecError, ValidationError
from livespec.schemas.dataclasses.revise_input import RevisionInput
from livespec.spec_governance.config import parse_config_text

__all__: list[str] = [
    "_canonical_ratification_digest",
    "_validate_ratification_reviews",
]

_REVIEW_MODES = frozenset({"manual-spawn", "auto-spawn"})
_UTC_SECONDS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_EVIDENCE = frozenset(
    {
        "reviewer_identity",
        "reviewer_model",
        "separate_reviewer",
        "read_only",
        "reviewed_at",
        "verdict",
        "proposal_stem",
        "content_digest",
    },
)


def _canonical_ratification_digest(*, decision: dict[str, object]) -> str:
    """Digest final resulting-files bytes with unambiguous length prefixes."""
    digest = hashlib.sha256()
    resulting_files = decision.get("resulting_files", [])
    if not isinstance(resulting_files, list):
        return digest.hexdigest()
    entries = cast(list[object], resulting_files)
    for raw_entry in entries:
        if not isinstance(raw_entry, dict):
            continue
        entry = cast(dict[str, object], raw_entry)
        path_bytes = str(entry.get("path", "")).encode("utf-8")
        content_bytes = str(entry.get("content", "")).encode("utf-8")
        digest.update(str(len(path_bytes)).encode("ascii"))
        digest.update(b":")
        digest.update(path_bytes)
        digest.update(str(len(content_bytes)).encode("ascii"))
        digest.update(b":")
        digest.update(content_bytes)
    return digest.hexdigest()


def _validate_ratification_reviews(
    *,
    revise_input: RevisionInput,
    project_root: Path,
) -> IOResult[RevisionInput, LivespecError]:
    """Require schema-valid no-blockers evidence for every accept/modify decision."""
    reviewer_model = _configured_reviewer_model(project_root=project_root)
    for decision in revise_input.decisions:
        decision_value = str(decision.get("decision", ""))
        if decision_value == "reject":
            continue
        error = _validate_decision_review(decision=decision, reviewer_model=reviewer_model)
        if error is not None:
            return IOResult.from_failure(ValidationError(error))
    return IOResult.from_value(revise_input)


def _configured_reviewer_model(*, project_root: Path) -> str | None:
    config_path = project_root / ".livespec.jsonc"
    if not config_path.is_file():
        return None
    text = config_path.read_text(encoding="utf-8")
    declared = parse_config_text(text=text)
    return declared.effective.ratification_reviewer_model


def _validate_decision_review(
    *,
    decision: dict[str, object],
    reviewer_model: str | None,
) -> str | None:
    mode = decision.get("ratification_review")
    if mode not in _REVIEW_MODES:
        return "revise: mutating decisions require ratification_review manual-spawn or auto-spawn"
    evidence = decision.get("ratification_evidence")
    if not isinstance(evidence, dict):
        return "revise: mutating decisions require ratification_evidence"
    narrowed_evidence = cast(dict[Any, Any], evidence)
    return _validate_evidence(
        decision=decision,
        evidence=narrowed_evidence,
        reviewer_model=reviewer_model,
    )


def _validate_evidence(
    *,
    decision: dict[str, object],
    evidence: dict[Any, Any],
    reviewer_model: str | None,
) -> str | None:
    missing = sorted(_REQUIRED_EVIDENCE.difference(str(key) for key in evidence))
    if missing:
        return f"revise: ratification_evidence missing required fields: {missing}"
    for validator in (
        _reviewer_error,
        _declaration_error,
        _timestamp_error,
        _verdict_error,
        _proposal_stem_error,
        _digest_error,
    ):
        error = validator(
            decision=decision,
            evidence=evidence,
            reviewer_model=reviewer_model,
        )
        if error is not None:
            return error
    return None


def _reviewer_error(
    *,
    decision: dict[str, object],
    evidence: dict[Any, Any],
    reviewer_model: str | None,
) -> str | None:
    _ = decision
    if evidence.get("reviewer_model") != reviewer_model and reviewer_model is not None:
        return "revise: ratification reviewer_model does not match configured reviewer"
    if evidence.get("reviewer_identity") != evidence.get("reviewer_model"):
        return "revise: ratification reviewer identity/model mismatch"
    return None


def _declaration_error(
    *,
    decision: dict[str, object],
    evidence: dict[Any, Any],
    reviewer_model: str | None,
) -> str | None:
    _ = (decision, reviewer_model)
    if evidence.get("separate_reviewer") is not True:
        return "revise: ratification evidence must declare a separate reviewer"
    if evidence.get("read_only") is not True:
        return "revise: ratification evidence must declare read-only review"
    return None


def _timestamp_error(
    *,
    decision: dict[str, object],
    evidence: dict[Any, Any],
    reviewer_model: str | None,
) -> str | None:
    _ = (decision, reviewer_model)
    reviewed_at = evidence.get("reviewed_at")
    if not isinstance(reviewed_at, str) or not _UTC_SECONDS.fullmatch(reviewed_at):
        return "revise: ratification reviewed_at must be UTC ISO-8601 seconds"
    return None


def _verdict_error(
    *,
    decision: dict[str, object],
    evidence: dict[Any, Any],
    reviewer_model: str | None,
) -> str | None:
    _ = (decision, reviewer_model)
    if evidence.get("verdict") != "NO BLOCKERS":
        return "revise: ratification verdict must be literal NO BLOCKERS"
    return None


def _proposal_stem_error(
    *,
    decision: dict[str, object],
    evidence: dict[Any, Any],
    reviewer_model: str | None,
) -> str | None:
    _ = reviewer_model
    if evidence.get("proposal_stem") != decision.get("proposal_topic"):
        return "revise: ratification proposal stem does not match decision topic"
    return None


def _digest_error(
    *,
    decision: dict[str, object],
    evidence: dict[Any, Any],
    reviewer_model: str | None,
) -> str | None:
    _ = reviewer_model
    digest = evidence.get("content_digest")
    if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
        return "revise: ratification content_digest must be lowercase sha256 hex"
    if digest != _canonical_ratification_digest(decision=decision):
        return "revise: ratification content_digest does not match final bytes"
    return None
