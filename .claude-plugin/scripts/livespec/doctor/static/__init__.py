"""Static-doctor check registry.

Per v022 D7, Phase 3 narrows this registry to the eight checks
implemented at this phase; Phase 7 adds the remaining four
(`out_of_band_edits`, `bcp14_keyword_wellformedness`,
`gherkin_blank_line_format`, `anchor_reference_resolution`). The
registry shape is `(SLUG, run)` per v021 Q1 (the v018 Q1 triple
shape with `APPLIES_TO` was reverted; the orchestrator owns the
applicability table).

JSON slug ↔ module filename ↔ check_id is named explicitly per row
below. There is no slug-to-filename conversion loop.

Adding or removing a check is one explicit edit to this file plus
the corresponding edit to the orchestrator-owned applicability
table in `livespec/doctor/run_static.py` (when the new check has
non-uniform applicability).
"""

from collections.abc import Callable
from typing import Final

from returns.io import IOResult

from livespec.context import DoctorContext
from livespec.doctor.static import (
    livespec_jsonc_valid,
    proposed_change_topic_format,
    proposed_changes_and_history_dirs,
    revision_to_proposed_change_pairing,
    template_exists,
    template_files_present,
    version_contiguity,
    version_directories_complete,
)
from livespec.errors import LivespecError
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId

__all__: list[str] = [
    "CHECKS",
    "CheckRunFn",
]


CheckRunFn = Callable[..., IOResult[Finding, LivespecError]]
"""Type alias for the `run` function exported by every static-check
module: `run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]`.

Declared with `Callable[..., ...]` (not `Callable[[DoctorContext],
...]`) because each check declares its single argument as keyword-only
(`*, ctx: DoctorContext`); the `...` form keeps pyright permissive at
this seam while the keyword-only-args check enforces the discipline at
the per-check definition site."""

# Marker re-export of DoctorContext so future checks importing the
# registry's typing surface have it available without re-importing.
_DoctorContextType = DoctorContext


CHECKS: Final[tuple[tuple[CheckId, CheckRunFn], ...]] = (
    (livespec_jsonc_valid.SLUG, livespec_jsonc_valid.run),
    (template_exists.SLUG, template_exists.run),
    (template_files_present.SLUG, template_files_present.run),
    (proposed_changes_and_history_dirs.SLUG, proposed_changes_and_history_dirs.run),
    (version_directories_complete.SLUG, version_directories_complete.run),
    (version_contiguity.SLUG, version_contiguity.run),
    (revision_to_proposed_change_pairing.SLUG, revision_to_proposed_change_pairing.run),
    (proposed_change_topic_format.SLUG, proposed_change_topic_format.run),
)
"""The eight Phase-3 implemented checks. Order is the registration
order; the orchestrator iterates this tuple per spec tree, applying
the orchestrator-owned applicability table to decide which checks
run for which `template_name`."""
