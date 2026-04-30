"""Static-doctor check registry.

Per PROPOSAL.md §"`doctor` → Static-phase structure" lines
2507-2512, this package's `__init__.py` holds the registry of
implemented static-phase check modules. Each check is registered
explicitly (no dynamic discovery); adding or removing a check is
one explicit edit to this file.

Cycle 131 lands the first registry entry: `livespec_jsonc_valid`,
the first of the eight Phase-3 minimum-subset checks per Plan
Phase 3 line 1596-1602. Subsequent cycles append additional
checks (`template_exists`, `template_files_present`,
`proposed_changes_and_history_dirs`,
`version_directories_complete`, `version_contiguity`,
`revision_to_proposed_change_pairing`,
`proposed_change_topic_format`) one at a time as outside-in
consumer pressure pulls them in.

The registry is a tuple of imported modules so the orchestrator
can iterate it deterministically; each module exposes a `SLUG`
constant + a `run(ctx)` function returning
`IOResult[Finding, LivespecError]`.
"""

from __future__ import annotations

from livespec.doctor.static import (
    livespec_jsonc_valid,
    template_exists,
    template_files_present,
)

__all__: list[str] = ["STATIC_CHECKS"]


STATIC_CHECKS = (livespec_jsonc_valid, template_exists, template_files_present)
