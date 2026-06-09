"""DoctorContext — per-tree context value-object for static-phase checks.

Per Plan  +: the orchestrator enumerates
`(spec_root, template_name)` pairs and builds one
`DoctorContext` per pair. Each static-phase check's `run()`
takes the context and returns a `Finding`.

Frozen + slots-+-kw_only per the project-wide dataclass rule.
Fields widen under consumer pressure:  lands the
minimal pair (project_root + spec_root) that
`livespec_jsonc_valid` needs; later cycles add
`template_name`, `template_resolved_path`, etc. as additional
checks demand them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

__all__: list[str] = ["DoctorContext"]


@dataclass(frozen=True, kw_only=True, slots=True)
class DoctorContext:
    """Per-tree context for one static-check invocation.

    `project_root` is the project-root path (the directory
    holding `.livespec.jsonc`). `spec_root` is the spec-root
    path the orchestrator is currently checking — discriminates
    per-tree origin between the main spec tree and each
    sub-spec tree. Both are absolute Paths; the orchestrator
    is responsible for resolving relative inputs before
    constructing the context.

    `work_items_provider` is the resolved absolute path to the
    ACTIVE impl-plugin's `list-work-items` thin-transport wrapper
    (per `SPECIFICATION/contracts.md` §"Doctor cross-boundary
    invariants"), or `None` when no live work-item provider is
    configured. `run_static.py` resolves it once from the
    `LIVESPEC_IMPL_LIST_WORK_ITEMS` env var and threads it through
    so the cross-boundary work-item checks acquire their data
    plugin-agnostically (via the wrapper) instead of a direct
    JSONL file read. `None` makes those checks surface a
    `skipped` Finding. The field widens the context per the
    documented "fields widen under consumer pressure" rule.
    """

    project_root: Path
    spec_root: Path
    work_items_provider: Path | None = None
