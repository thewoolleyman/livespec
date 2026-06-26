"""Static-doctor check registry + applicability table.

Per, this
package's `__init__.py` holds the registry of implemented
static-phase check modules. Each check is registered
explicitly (no dynamic discovery); adding or removing a check is
one explicit edit to this file.

This work lands the first registry entry; cycles 134-141 add
the remaining seven Phase-3 minimum-subset checks
(`template_exists`, `template_files_present`,
`proposed_changes_and_history_dirs`,
`version_directories_complete`, `version_contiguity`,
`revision_to_proposed_change_pairing`,
`proposed_change_topic_format`).  (sub-steps 7.b/7.c/
7.d/7.a.ii) registers the remaining four checks
(`bcp14_keyword_wellformedness`, `gherkin_blank_line_format`,
`anchor_reference_resolution`, `out_of_band_edits`); all
twelve are now wired.

This work makes the orchestrator-owned applicability mapping
explicit: APPLICABILITY_BY_TREE_KIND maps each `tree_kind`
('main' or 'sub_spec') to the tuple of check modules that
apply to that kind of tree. Phase-3 minimum subset: every
implemented check applies to the main tree; the sub-spec tree
omits the project-root-level checks (livespec_jsonc_valid +
template_exists are config-file concerns that don't recur per
sub-spec). Sub-spec-tree dispatch lands in subsequent cycles
under outside-in pressure.

Each check module exposes a `SLUG` constant + a `run(ctx)`
function returning `IOResult[Finding, LivespecError]`.
"""

from __future__ import annotations

from typing import Literal

from livespec.doctor.static import (
    accept_decision_snapshot_consistency,
    anchor_reference_resolution,
    bcp14_keyword_wellformedness,
    config_named_cli_callability,
    copier_template_workflow_coverage,
    gherkin_blank_line_format,
    livespec_jsonc_valid,
    master_direct_uncommitted_spec_edits,
    no_cross_spec_reference,
    no_spec_section_citation_in_code,
    out_of_band_edits,
    parent_proposed_change_resolves,
    proposed_change_topic_format,
    proposed_changes_and_history_dirs,
    revision_to_proposed_change_pairing,
    template_exists,
    template_files_present,
    version_contiguity,
    version_directories_complete,
    wiring_completeness_cross_repo,
)

__all__: list[str] = ["APPLICABILITY_BY_TREE_KIND", "STATIC_CHECKS"]


TreeKind = Literal["main", "sub_spec"]


STATIC_CHECKS = (
    livespec_jsonc_valid,
    config_named_cli_callability,
    template_exists,
    template_files_present,
    proposed_changes_and_history_dirs,
    version_directories_complete,
    version_contiguity,
    revision_to_proposed_change_pairing,
    proposed_change_topic_format,
    bcp14_keyword_wellformedness,
    gherkin_blank_line_format,
    anchor_reference_resolution,
    out_of_band_edits,
    accept_decision_snapshot_consistency,
    copier_template_workflow_coverage,
    master_direct_uncommitted_spec_edits,
    parent_proposed_change_resolves,
    no_cross_spec_reference,
    no_spec_section_citation_in_code,
    wiring_completeness_cross_repo,
)


APPLICABILITY_BY_TREE_KIND: dict[TreeKind, tuple[object, ...]] = {
    "main": STATIC_CHECKS,
    "sub_spec": (
        template_files_present,
        proposed_changes_and_history_dirs,
        version_directories_complete,
        version_contiguity,
        revision_to_proposed_change_pairing,
        proposed_change_topic_format,
        bcp14_keyword_wellformedness,
        gherkin_blank_line_format,
        anchor_reference_resolution,
        no_cross_spec_reference,
        out_of_band_edits,
        accept_decision_snapshot_consistency,
        parent_proposed_change_resolves,
    ),
}
