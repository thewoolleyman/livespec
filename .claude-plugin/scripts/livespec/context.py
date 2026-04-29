"""livespec.context — immutable context dataclasses.

Per `python-skill-script-style-requirements.md` §"Context
dataclasses", every context dataclass is
`@dataclass(frozen=True, kw_only=True, slots=True)`. The full
`DoctorContext` shape carries 8 fields (project_root, spec_root,
config, config_load_status, template_root, template_load_status,
run_id, git_head_available); sub-command contexts (SeedContext,
ProposeChangeContext, etc.) embed `DoctorContext` rather than
inheriting.

v032 TDD redo cycle 21: minimal authoring under outside-in
consumer pressure. The cycle-21 test needs only the
`livespec_jsonc_valid` check, which reads `.livespec.jsonc` at
the project root — therefore `DoctorContext` carries only
`project_root` at this cycle. Every other field lands when a
check or orchestrator behavior consumes it: `spec_root` when a
spec-tree-relative check (e.g., `proposed_changes_and_history_dirs`)
is authored; `config`/`config_load_status` when bootstrap-lenience
is exercised; `template_root`/`template_load_status` when
`template_exists` is authored; `run_id` when structlog correlation
becomes test-observable; `git_head_available` when the eventual
`out_of_band_edits` check (Phase 7) consumes it.

Sub-command contexts (SeedContext, ProposeChangeContext, etc.)
similarly land under their respective consumer pressure.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

__all__: list[str] = ["DoctorContext"]


@dataclass(frozen=True, kw_only=True, slots=True)
class DoctorContext:
    """Immutable context for static-check `run(*, ctx)` invocations."""

    project_root: Path
