"""Decision-mode policy edits, extracted from `editing`.

Carries the `set-revise-decision-mode` and `set-drift-acceptance-mode`
handler families, together with the `EditResult` value they return and
the `_edit_result` constructor every handler in the grammar uses.

`EditResult` and `_edit_result` move here rather than staying behind for
the same reason the journal split moved its digest predicate: they are
shared by handlers on both sides, and putting them in the child keeps
the dependency one-way. `editing` imports from here and re-exports
`EditResult` as part of its public surface; nothing here imports from
`editing`, so the two cannot form a cycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from returns.io import IOFailure, IOResult, IOSuccess
from returns.unsafe import unsafe_perform_io

from livespec.errors import ValidationError
from livespec.spec_governance.config import PROPOSAL_STEM_PATTERN
from livespec.spec_governance.config_edit import write_config_value
from livespec.spec_governance.proposal_edit import write_proposal_override

__all__: list[str] = [
    "EditResult",
    "_apply_drift_acceptance_action",
    "_apply_revise_decision_action",
    "_edit_result",
]

_REVISE_DECISION_VALUES = {"manual", "delegated", "consensus"}
_DRIFT_ACCEPTANCE_VALUES = {"human", "consensus"}
_REVISE_DECISION_GLOBAL_PARTS = 3
_REVISE_DECISION_PROPOSAL_PARTS = 4
_DRIFT_ACCEPTANCE_GLOBAL_PARTS = 3


@dataclass(frozen=True, kw_only=True, slots=True)
class EditResult:
    """Result of one validated policy edit."""

    changed_path: Path
    message: str


def _edit_result(*, changed_path: Path | str | IOResult[Path, ValidationError]) -> str | EditResult:
    """Adapt a config-edit outcome to this module's `str`-error / `EditResult` channel.

    ⚠️ The config writers now REFUSE on the failure track rather than rewriting a
    file they could not read. This is the one seam every caller already funnels
    through, so that refusal reaches the existing error channel **without moving a
    single call site** — the operator sees a message naming the broken block
    instead of a success that silently destroyed their siblings.
    """
    if isinstance(changed_path, IOFailure):
        return str(unsafe_perform_io(changed_path.failure()))
    resolved: Path | str
    if isinstance(changed_path, IOSuccess):
        resolved = unsafe_perform_io(changed_path.unwrap())
    else:
        resolved = cast("Path | str", changed_path)
    if isinstance(resolved, str):
        return resolved
    return EditResult(changed_path=resolved, message="policy edit applied")


def _apply_revise_decision_action(
    *,
    project_root: Path,
    parts: list[str],
) -> str | EditResult:
    if parts[1] == "global" and len(parts) == _REVISE_DECISION_GLOBAL_PARTS:
        return _apply_revise_decision_global(project_root=project_root, value=parts[2])
    if parts[1] == "proposal" and len(parts) == _REVISE_DECISION_PROPOSAL_PARTS:
        return _apply_revise_decision_proposal(
            project_root=project_root,
            proposal_stem=parts[2],
            value=parts[3],
        )
    return "set-revise-decision-mode requires global:<value> or proposal:<stem>:<value>"


def _apply_revise_decision_global(
    *,
    project_root: Path,
    value: str,
) -> str | EditResult:
    if value != "clear" and value not in _REVISE_DECISION_VALUES:
        return f"revise decision mode must be one of {sorted(_REVISE_DECISION_VALUES)} or clear"
    return _edit_result(
        changed_path=write_config_value(
            project_root=project_root,
            key="revise_decision_mode",
            value=None if value == "clear" else value,
        ),
    )


def _apply_revise_decision_proposal(
    *,
    project_root: Path,
    proposal_stem: str,
    value: str,
) -> str | EditResult:
    if PROPOSAL_STEM_PATTERN.fullmatch(proposal_stem) is None:
        return f"proposal stem must match {PROPOSAL_STEM_PATTERN.pattern}"
    if value != "clear" and value not in _REVISE_DECISION_VALUES:
        return f"proposal override must be one of {sorted(_REVISE_DECISION_VALUES)} or clear"
    return _edit_result(
        changed_path=write_proposal_override(
            project_root=project_root,
            proposal_stem=proposal_stem,
            value=None if value == "clear" else value,
            key="decision_policy",
        ),
    )


def _apply_drift_acceptance_action(
    *,
    project_root: Path,
    parts: list[str],
) -> str | EditResult:
    if parts[1] == "global" and len(parts) == _DRIFT_ACCEPTANCE_GLOBAL_PARTS:
        return _apply_drift_acceptance_global(project_root=project_root, value=parts[2])
    return "set-drift-acceptance-mode requires global:<value>"


def _apply_drift_acceptance_global(
    *,
    project_root: Path,
    value: str,
) -> str | EditResult:
    if value != "clear" and value not in _DRIFT_ACCEPTANCE_VALUES:
        return f"drift acceptance mode must be one of {sorted(_DRIFT_ACCEPTANCE_VALUES)} or clear"
    return _edit_result(
        changed_path=write_config_value(
            project_root=project_root,
            key="drift_acceptance_mode",
            value=None if value == "clear" else value,
        ),
    )
