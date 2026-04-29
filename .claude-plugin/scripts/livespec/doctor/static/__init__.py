"""Static-doctor check registry.

Per PROPOSAL.md §"`doctor` → Static-phase structure" lines
2507-2512, the registry imports every check module by name and
re-exports a tuple of `(SLUG, run)` pairs (v021 Q1: applicability
table is owned by the orchestrator, NOT a per-check `APPLIES_TO`
constant). Adding or removing a check is one explicit edit to
this file; no dynamic discovery.

v032 TDD redo: registry grows one entry per cycle as each check's
test-driven pass-Finding pulls it in. Cycle 21 added
`livespec_jsonc_valid`; cycle 22 added `template_exists`; cycle
23 added `template_files_present`; cycle 24 added
`proposed_changes_and_history_dirs`; cycle 25 added
`version_directories_complete`; cycle 26 adds
`version_contiguity`. Remaining two Phase-3 minimum checks
(`revision_to_proposed_change_pairing`,
`proposed_change_topic_format`) land in subsequent cycles. The
v022 D7 narrowed-registry policy (Phase 3: 8 implemented checks;
Phase 7: remaining four) governs the final shape.

Slug ↔ module-filename ↔ JSON `check_id` mapping is recorded
literally per row: module `livespec_jsonc_valid.py` → SLUG
`"livespec-jsonc-valid"` → `check_id` `"doctor-livespec-jsonc-valid"`;
module `template_exists.py` → SLUG `"template-exists"` → `check_id`
`"doctor-template-exists"`; module `template_files_present.py` →
SLUG `"template-files-present"` → `check_id`
`"doctor-template-files-present"`; module
`proposed_changes_and_history_dirs.py` → SLUG
`"proposed-changes-and-history-dirs"` → `check_id`
`"doctor-proposed-changes-and-history-dirs"`; module
`version_directories_complete.py` → SLUG
`"version-directories-complete"` → `check_id`
`"doctor-version-directories-complete"`; module
`version_contiguity.py` → SLUG `"version-contiguity"` →
`check_id` `"doctor-version-contiguity"`. There is no
slug-to-filename conversion loop.
"""

from __future__ import annotations

from collections.abc import Callable

from livespec.context import DoctorContext
from livespec.doctor.static import (
    livespec_jsonc_valid,
    proposed_changes_and_history_dirs,
    template_exists,
    template_files_present,
    version_contiguity,
    version_directories_complete,
)
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["CHECKS", "CheckRunFn"]


CheckRunFn = Callable[..., Finding]
"""Type alias for the `run` function exported by every static-check
module. Signature is `run(*, ctx: DoctorContext) -> Finding`.

v032 TDD redo cycle 21: cycle-21 checks return plain `Finding`; the
spec's eventual `IOResult[Finding, LivespecError]` shape lands when
a failure-path test (e.g., schema-invalid config) consumes the
ROP discrimination. Same pattern as cycle 8's plain-`str`
`current_user_or_unknown`.

Declared with `Callable[..., Finding]` because each check declares
its single argument as keyword-only (`*, ctx: DoctorContext`); the
`...` form keeps pyright permissive at this seam while the
keyword-only-args check enforces the discipline at the per-check
definition site."""

# Marker re-export so future checks importing the registry's
# typing surface have it available without re-importing.
_DoctorContextType = DoctorContext


CHECKS: tuple[tuple[str, CheckRunFn], ...] = (
    (livespec_jsonc_valid.SLUG, livespec_jsonc_valid.run),
    (template_exists.SLUG, template_exists.run),
    (template_files_present.SLUG, template_files_present.run),
    (
        proposed_changes_and_history_dirs.SLUG,
        proposed_changes_and_history_dirs.run,
    ),
    (version_directories_complete.SLUG, version_directories_complete.run),
    (version_contiguity.SLUG, version_contiguity.run),
)
"""Phase-3 minimum-subset checks. Order is registration order;
the orchestrator iterates this tuple per spec tree, applying
the orchestrator-owned applicability table to decide which checks
run for which `template_name`. Cycle 26 still hardcodes
unconditional-applicability; the table grows under future consumer
pressure (e.g., when a sub-spec test exercises the main-only
restriction on `template-exists` and `template-files-present` per
PROPOSAL.md lines 2534-2538)."""
