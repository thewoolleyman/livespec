"""Doctor static-phase orchestrator.

Per PROPOSAL.md §"`doctor`" (line ~2468) and Plan Phase 3 (lines
1554-1616): the orchestrator enumerates (spec_root, template_name)
pairs at startup (main tree first with template-name sentinel
"main"; then each sub-spec tree under
<main-spec-root>/templates/<sub-name>/ with template-name set
to the sub-spec directory name); per pair it builds a per-tree
DoctorContext (with template_name set appropriately) and runs
the applicable check subset decided by the orchestrator-owned
applicability table.

Phase-3 minimum subset registers 8 implemented checks per Plan
line 1596-1602: livespec_jsonc_valid, template_exists,
template_files_present, proposed_changes_and_history_dirs,
version_directories_complete, version_contiguity,
revision_to_proposed_change_pairing,
proposed_change_topic_format. The remaining 4 checks
(out_of_band_edits, bcp14_keyword_wellformedness,
gherkin_blank_line_format, anchor_reference_resolution) land
at Phase 7.

Cycle 102 lands the supervisor stub returning 1; subsequent
cycles drive the enumeration + per-tree dispatch + per-check
execution behavior under outside-in pressure.
"""

from __future__ import annotations

import sys

__all__: list[str] = ["main"]


def main(*, argv: list[str] | None = None) -> int:
    """Doctor static-phase supervisor entry point. Returns the process exit code.

    Cycle 102 stub: returns 1 (generic error sentinel) until
    subsequent cycles drive the enumeration + per-check
    execution railway. The wrapper invokes `main()` per the
    canonical 6-statement shape; argv defaults to sys.argv[1:]
    when called without args.
    """
    _ = sys.argv[1:] if argv is None else argv
    return 1
