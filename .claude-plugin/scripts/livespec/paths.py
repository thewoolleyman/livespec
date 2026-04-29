"""livespec.paths — shared filesystem-path helpers.

Per PROPOSAL.md §"Template resolution contract" lines 1424-1503,
the bundle root (`.claude-plugin/`) is a load-bearing anchor for
built-in template resolution. Two doctor-static checks
(`template_exists`, `template_files_present`) and one supervisor
(`commands/resolve_template`) all need the path. This module
collapses the three duplicated `Path(__file__).resolve().parents[N]`
computations into one shared helper.

v032 TDD redo cycle 23: extracted at the third consumer per Kent
Beck's three-strikes-and-refactor rhythm. Cycles 19 and 22 inlined
the math (different N values per module depth); cycle 23's
`template_files_present` is the third consumer, and the natural
home is here at `livespec/paths.py` (depth 3 under `.claude-plugin/`,
so parents[2] = `.claude-plugin/`). Cycles 19 and 22 will adopt
this helper as part of cycle 23 (their inline `_bundle_root`
helpers collapse into a single import).

The helper is keyword-only-arg-free because it takes no arguments
(the depth-from-this-module is a fixed property of where this file
sits in the tree, not a runtime parameter).
"""

from __future__ import annotations

from pathlib import Path

__all__: list[str] = ["bundle_root"]


def bundle_root() -> Path:
    """Return `<bundle-root>` (`.claude-plugin/`) absolute path.

    From `.claude-plugin/scripts/livespec/paths.py`,
    parents[0]=livespec/, parents[1]=scripts/, parents[2]=.claude-plugin/.
    """
    return Path(__file__).resolve().parents[2]
