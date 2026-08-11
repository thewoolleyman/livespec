"""Spec-PR-merge policy edits, extracted from `editing`.

The `set-spec-pr-merge` handler family: the grammar dispatcher and its
global and per-proposal arms.

This is the feature whose arrival pushed `editing` back into the 201-250
LLOC soft band four days after the band was emptied, so it is the natural
seam -- the newest cohesive family, cleanly separable.

`EditResult` and `_edit_result` come from `_editing_decision_modes`, the
sibling leaf extracted earlier, NOT from `editing`. So this module is a
leaf too: `editing` imports from here and nothing here imports from
`editing`, and the two cannot form a cycle.
"""

from __future__ import annotations

from pathlib import Path

from livespec.spec_governance._editing_decision_modes import EditResult, _edit_result
from livespec.spec_governance.config import PROPOSAL_STEM_PATTERN
from livespec.spec_governance.config_edit import write_config_value
from livespec.spec_governance.proposal_edit import write_proposal_override

__all__: list[str] = [
    "_apply_spec_pr_merge_action",
]

_SPEC_PR_MERGE_VALUES = {"manual", "auto-on-green"}
_SPEC_PR_MERGE_GLOBAL_PARTS = 3
_SPEC_PR_MERGE_PROPOSAL_PARTS = 4


def _apply_spec_pr_merge_action(
    *,
    project_root: Path,
    parts: list[str],
) -> str | EditResult:
    if parts[1] == "global" and len(parts) == _SPEC_PR_MERGE_GLOBAL_PARTS:
        return _apply_spec_pr_merge_global(project_root=project_root, value=parts[2])
    if parts[1] == "proposal" and len(parts) == _SPEC_PR_MERGE_PROPOSAL_PARTS:
        return _apply_spec_pr_merge_proposal(
            project_root=project_root,
            proposal_stem=parts[2],
            value=parts[3],
        )
    return "set-spec-pr-merge requires global:<value> or proposal:<stem>:<value>"


def _apply_spec_pr_merge_global(
    *,
    project_root: Path,
    value: str,
) -> str | EditResult:
    if value == "clear":
        return _edit_result(
            changed_path=write_config_value(
                project_root=project_root,
                key="spec_pr_merge",
                value=None,
            ),
        )
    if value not in _SPEC_PR_MERGE_VALUES:
        return f"spec PR merge must be one of {sorted(_SPEC_PR_MERGE_VALUES)} or clear"
    return _edit_result(
        changed_path=write_config_value(
            project_root=project_root,
            key="spec_pr_merge",
            value=value,
        ),
    )


def _apply_spec_pr_merge_proposal(
    *,
    project_root: Path,
    proposal_stem: str,
    value: str,
) -> str | EditResult:
    if PROPOSAL_STEM_PATTERN.fullmatch(proposal_stem) is None:
        return f"proposal stem must match {PROPOSAL_STEM_PATTERN.pattern}"
    if value != "clear" and value not in _SPEC_PR_MERGE_VALUES:
        return f"proposal override must be one of {sorted(_SPEC_PR_MERGE_VALUES)} or clear"
    return _edit_result(
        changed_path=write_proposal_override(
            project_root=project_root,
            proposal_stem=proposal_stem,
            value=None if value == "clear" else value,
            key="spec_pr_merge_policy",
        ),
    )
