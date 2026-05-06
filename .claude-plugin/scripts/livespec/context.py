"""DoctorContext — per-tree context value-object for static-phase checks.

Per Plan Phase 3 +: the orchestrator enumerates
`(spec_root, template_name)` pairs and builds one
`DoctorContext` per pair. Each static-phase check's `run()`
takes the context and returns a `Finding`.

Frozen + slots-+-kw_only per the project-wide dataclass rule.
Fields widen under consumer pressure: cycle 131 lands the
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
    """

    project_root: Path
    spec_root: Path
