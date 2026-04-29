"""livespec.doctor.static.template_exists — template-resolution validity check.

Verifies that the active template named in `.livespec.jsonc.template`
resolves to an existing directory. Per PROPOSAL.md §"`doctor` →
Static-phase checks" lines 2672-2690 and Plan §"Phase 3" line 1481,
this is the second of the eight Phase-3 minimum-subset checks.

v032 TDD redo cycle 22: minimal authoring under outside-in
consumer pressure. The cycle-22 test seeds a tree (which produces
a `.livespec.jsonc` containing `{"template": "livespec"}`) and
asserts a `pass` Finding is emitted. Therefore this cycle handles
only the resolved-directory-exists happy path. The full
`template-exists` semantics from PROPOSAL.md lines 2672-2690 — the
template.json layout check, `template_format_version` matching,
the four required prompt files (`seed.md`, `propose-change.md`,
`revise.md`, `critique.md`), the optional doctor-llm prompt
fields, and the optional `doctor_static_check_modules` list — all
land in subsequent cycles, each driven by a specific failure-path
test. Same applies to bootstrap lenience (v014 N3
`template_load_status` field on `DoctorContext`) and the
orchestrator-owned applicability table that restricts this check
to `template_name == "main"` per PROPOSAL.md lines 2534-2538 (v018
Q1 / v021 Q1) — generalizes when sub-spec iteration is exercised
by a test.

Built-in template names (`livespec`, `minimal`) resolve to
`<bundle-root>/specification-templates/<name>/` per PROPOSAL.md
§"Template resolution contract" lines 1424-1503. Cycle 23 lifted
the `<bundle-root>` computation to `livespec.paths.bundle_root`
(third-strikes-and-refactor: cycles 19 and 22 inlined
depth-specific `Path(__file__).resolve().parents[N]` math; cycle
23 collapses all three into the shared helper).

User-provided template paths (anything not in the built-in set)
are resolved relative to `ctx.project_root`. The
`template.json`-validity branch (PROPOSAL.md lines 1480-1484) lands
when a custom-template test exercises it.
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec.context import DoctorContext
from livespec.paths import bundle_root
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "template-exists"

_BUILTIN_TEMPLATES = frozenset({"livespec", "minimal"})


def _resolve_template_path(*, project_root: Path, template_value: str) -> Path:
    if template_value in _BUILTIN_TEMPLATES:
        return bundle_root() / "specification-templates" / template_value
    return project_root / template_value


def run(*, ctx: DoctorContext) -> Finding:
    config_path = ctx.project_root / ".livespec.jsonc"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    template_value = config["template"]
    resolved = _resolve_template_path(project_root=ctx.project_root, template_value=template_value)
    if resolved.is_dir():
        return Finding(
            check_id=f"doctor-{SLUG}",
            status="pass",
            message=f"template '{template_value}' resolved to existing directory",
            path=None,
            line=None,
            spec_root=ctx.spec_root.relative_to(ctx.project_root).as_posix(),
        )
    return Finding(
        check_id=f"doctor-{SLUG}",
        status="fail",
        message=(f"template '{template_value}' resolved to {resolved} which does not exist"),
        path=None,
        line=None,
        spec_root=ctx.spec_root.relative_to(ctx.project_root).as_posix(),
    )
