"""livespec.context — immutable context dataclasses.

Per `python-skill-script-style-requirements.md` §"Context
dataclasses", every context dataclass is
`@dataclass(frozen=True, kw_only=True, slots=True)`. The full
`DoctorContext` shape carries 8 fields (project_root, spec_root,
config, config_load_status, template_root, template_load_status,
run_id, git_head_available); sub-command contexts (SeedContext,
ProposeChangeContext, etc.) embed `DoctorContext` rather than
inheriting.

v032 TDD redo cycle 29: widened from cycle 21's `project_root`-
only minimum to add `spec_root: Path` and `template_name: str` —
the two fields the orchestrator's `(spec_root, template_name)`
pair iteration consumes per PROPOSAL.md lines 2513-2542.
`spec_root` is the absolute path to the tree's root (e.g.,
`<project_root>/SPECIFICATION/` for the main tree;
`<project_root>/SPECIFICATION/templates/livespec/` for a livespec
sub-spec tree). `template_name` is `"main"` for the main spec
tree or the sub-spec directory name (e.g., `"livespec"`,
`"minimal"`) for sub-spec trees, used by the orchestrator's
applicability table to dispatch main-tree-only checks
(`template-exists`, `template-files-present`).

Remaining fields land under future consumer pressure:
`config`/`config_load_status` when bootstrap-lenience is
exercised; `template_root`/`template_load_status` when
`template-exists` widens past the cycle-22 minimum;
`run_id` when structlog correlation becomes test-observable;
`git_head_available` when the eventual `out_of_band_edits`
check (Phase 7) consumes it.

Sub-command contexts (SeedContext, ProposeChangeContext, etc.)
similarly land under their respective consumer pressure.

The style doc names `spec_root: SpecRoot` (a `NewType` over
`Path` from `livespec/types.py`) for the canonical typed shape.
Cycle 29 keeps plain `Path`; the NewType discipline lands
when `check-newtype-domain-primitives` (Phase 4) forces it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

__all__: list[str] = ["DoctorContext"]


@dataclass(frozen=True, kw_only=True, slots=True)
class DoctorContext:
    """Immutable context for static-check `run(*, ctx)` invocations."""

    project_root: Path
    spec_root: Path
    template_name: str
