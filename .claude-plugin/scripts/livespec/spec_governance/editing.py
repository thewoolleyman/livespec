"""Validated action grammar for spec-governance policy edits."""

from __future__ import annotations

from pathlib import Path

from livespec.spec_governance._editing_decision_modes import (
    EditResult,
    _apply_drift_acceptance_action,
    _apply_revise_decision_action,
    _edit_result,
)
from livespec.spec_governance.config import (
    DOCTOR_CHECK_ID_PATTERN,
    MODEL_PATTERN,
    PROPOSAL_STEM_PATTERN,
)
from livespec.spec_governance.config_edit import write_config_map_entry, write_config_value
from livespec.spec_governance.proposal_edit import write_proposal_override

__all__: list[str] = [
    "EditResult",
    "apply_action",
]

_GLOBAL_VALUE_ACTIONS = {
    "set-propose-change-mode": ("propose_change_mode", {"interactive", "batch"}),
    "set-critique-mode": ("critique_mode", {"interactive", "batch"}),
    "set-in-flight-alignment": ("in_flight_alignment", {"prompt", "default-align"}),
    "set-ratification-reviewer-model": ("ratification_reviewer_model", None),
}
_RATIFICATION_VALUES = {"manual-spawn", "auto-spawn"}
_GLOBAL_ACTION_PARTS = 2
_DOCTOR_ACTION_PARTS = 3
_RATIFICATION_GLOBAL_PARTS = 3
_RATIFICATION_PROPOSAL_PARTS = 4
_REVISE_DECISION_GLOBAL_PARTS = 3
_REVISE_DECISION_PROPOSAL_PARTS = 4
_DRIFT_ACCEPTANCE_GLOBAL_PARTS = 3
_DOCTOR_VALUES = {
    "fix-now",
    "capture-as-work-item",
    "propose-change",
    "defer",
    "dismiss",
}


def apply_action(*, project_root: Path, action: str) -> str | EditResult:
    """Validate and apply one allowlisted action."""
    parts = action.split(":")
    if parts[0] in _GLOBAL_VALUE_ACTIONS and len(parts) == _GLOBAL_ACTION_PARTS:
        return _apply_global_action(project_root=project_root, verb=parts[0], value=parts[1])
    if parts[0] == "set-doctor-disposition" and len(parts) == _DOCTOR_ACTION_PARTS:
        return _apply_doctor_action(project_root=project_root, check_id=parts[1], value=parts[2])
    if parts[0] == "set-revise-decision-mode" and len(parts) >= _REVISE_DECISION_GLOBAL_PARTS:
        return _apply_revise_decision_action(project_root=project_root, parts=parts)
    if parts[0] == "set-drift-acceptance-mode" and len(parts) >= _DRIFT_ACCEPTANCE_GLOBAL_PARTS:
        return _apply_drift_acceptance_action(project_root=project_root, parts=parts)
    if parts[0] == "set-ratification-review" and len(parts) >= _RATIFICATION_GLOBAL_PARTS:
        return _apply_ratification_action(project_root=project_root, parts=parts)
    return f"unsupported action grammar: {action}"


def _apply_global_action(
    *,
    project_root: Path,
    verb: str,
    value: str,
) -> str | EditResult:
    key, allowed = _GLOBAL_VALUE_ACTIONS[verb]
    if value == "clear":
        return _edit_result(
            changed_path=write_config_value(project_root=project_root, key=key, value=None),
        )
    if allowed is not None and value not in allowed:
        return f"{verb}: unsupported value {value!r}"
    if allowed is None and MODEL_PATTERN.fullmatch(value) is None:
        return f"{verb}: model must match {MODEL_PATTERN.pattern}"
    return _edit_result(
        changed_path=write_config_value(project_root=project_root, key=key, value=value),
    )


def _apply_doctor_action(
    *,
    project_root: Path,
    check_id: str,
    value: str,
) -> str | EditResult:
    if DOCTOR_CHECK_ID_PATTERN.fullmatch(check_id) is None:
        return f"doctor check id must match {DOCTOR_CHECK_ID_PATTERN.pattern}"
    if value != "clear" and value not in _DOCTOR_VALUES:
        return f"doctor disposition must be one of {sorted(_DOCTOR_VALUES)} or clear"
    return _edit_result(
        changed_path=write_config_map_entry(
            project_root=project_root,
            map_key="doctor_dispositions",
            entry_key=check_id,
            value=None if value == "clear" else value,
        ),
    )


def _apply_ratification_action(
    *,
    project_root: Path,
    parts: list[str],
) -> str | EditResult:
    if parts[1] == "global" and len(parts) == _RATIFICATION_GLOBAL_PARTS:
        return _apply_ratification_global(project_root=project_root, value=parts[2])
    if parts[1] == "proposal" and len(parts) == _RATIFICATION_PROPOSAL_PARTS:
        return _apply_ratification_proposal(
            project_root=project_root,
            proposal_stem=parts[2],
            value=parts[3],
        )
    return "set-ratification-review requires global:<value> or proposal:<stem>:<value>"


def _apply_ratification_global(
    *,
    project_root: Path,
    value: str,
) -> str | EditResult:
    if value == "clear":
        return _edit_result(
            changed_path=write_config_value(
                project_root=project_root,
                key="ratification_review",
                value=None,
            ),
        )
    if value not in _RATIFICATION_VALUES:
        return f"ratification review must be one of {sorted(_RATIFICATION_VALUES)} or clear"
    return _edit_result(
        changed_path=write_config_value(
            project_root=project_root,
            key="ratification_review",
            value=value,
        ),
    )


def _apply_ratification_proposal(
    *,
    project_root: Path,
    proposal_stem: str,
    value: str,
) -> str | EditResult:
    if PROPOSAL_STEM_PATTERN.fullmatch(proposal_stem) is None:
        return f"proposal stem must match {PROPOSAL_STEM_PATTERN.pattern}"
    if value != "clear" and value not in _RATIFICATION_VALUES:
        return f"proposal override must be one of {sorted(_RATIFICATION_VALUES)} or clear"
    return _edit_result(
        changed_path=write_proposal_override(
            project_root=project_root,
            proposal_stem=proposal_stem,
            value=None if value == "clear" else value,
        ),
    )
