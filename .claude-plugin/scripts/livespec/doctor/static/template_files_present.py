"""livespec.doctor.static.template_files_present — repo-root file presence check.

Verifies that every template-required file (derived by walking the
active template's `specification-template/` directory) exists at
its expected repo-root-relative path. Per PROPOSAL.md §"`doctor`
→ Static-phase checks" lines 2691-2694 and Plan §"Phase 3" line
1481, this is the third of the eight Phase-3 minimum-subset
checks.

Path-mapping rule (PROPOSAL.md lines 1416-1422): `specification-
template/<X>` mirrors verbatim to `<repo-root>/<X>`. The directory
structure UNDER `specification-template/` is the source of truth
— `template.json.spec_root` is for OTHER checks
(`proposed_changes_and_history_dirs`, `version_directories_complete`,
etc.). A template MAY place spec files directly at the repo root
(e.g., `specification-template/SPEC.md` → `<repo-root>/SPEC.md`)
or under any subdirectory structure.

v032 TDD redo cycle 23: minimal authoring under outside-in
consumer pressure. Per Plan §"Phase 2" lines 1211-1214, the
Phase-2 bootstrap state of the `livespec` template's
`specification-template/` is "an empty skeleton (directory tree
only, no starter content files). Starter content is generated
agentically in Phase 7 from the template's sub-spec." On disk
today, the only file is a `.gitkeep` placeholder — git-housekeeping
plumbing, NOT a "starter content file" per Plan line 1212. The
walker therefore excludes `.gitkeep`, leaving zero
template-required files for cycle 23. The check trivially passes.

When Phase 7 populates `specification-template/` with real
content (PROPOSAL.md §"Definition of Done (v1)" line 3902), this
check meaningfully validates that seed materialized those files
at their corresponding repo-root paths. The trivial-pass
Phase-3 behavior pins the check's plumbing (registry registration,
walker, repo-root-resolution, Finding shape) without depending on
Phase-7 content.

Out of cycle-23 scope (deferred to subsequent cycles per
outside-in walking direction):

- Bootstrap lenience (v014 N3): when `template_load_status !=
  "ok"`, this check should emit `skipped` with the load-status
  reason. Lands when a malformed-template-test exercises it.
- Orchestrator-owned applicability table (PROPOSAL.md lines
  2534-2538): `template-files-present` is main-tree-only, like
  `template-exists`. Generalizes when sub-spec iteration is
  exercised.
- Failure-path Findings: missing expected file, malformed
  `template.json`, etc. — each lands when a specific
  failure-path test forces it.
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec.context import DoctorContext
from livespec.paths import bundle_root
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "template-files-present"

_BUILTIN_TEMPLATES = frozenset({"livespec", "minimal"})

_GITKEEP_EXCLUSIONS = frozenset({".gitkeep"})
"""File names excluded from the walker. `.gitkeep` is git-housekeeping
plumbing for representing an empty directory in a git tree, NOT a
"starter content file" per Plan §"Phase 2" lines 1211-1214."""


def _resolve_template_path(*, project_root: Path, template_value: str) -> Path:
    if template_value in _BUILTIN_TEMPLATES:
        return bundle_root() / "specification-templates" / template_value
    return project_root / template_value


def _walk_template_required_paths(*, template_dir: Path) -> list[Path]:
    """Return repo-root-relative paths of every walked file in `specification-template/`.

    Excludes `.gitkeep` placeholders per the cycle-23 docstring.
    Returned paths are relative to `<template-dir>/specification-template/`,
    which (per PROPOSAL.md lines 1416-1422) IS the repo-root-relative
    path the file should mirror to.
    """
    spec_template_dir = template_dir / "specification-template"
    if not spec_template_dir.is_dir():
        return []
    walked: list[Path] = []
    for path in sorted(spec_template_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name in _GITKEEP_EXCLUSIONS:
            continue
        walked.append(path.relative_to(spec_template_dir))
    return walked


def run(*, ctx: DoctorContext) -> Finding:
    config_path = ctx.project_root / ".livespec.jsonc"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    template_value = config["template"]
    template_dir = _resolve_template_path(
        project_root=ctx.project_root, template_value=template_value
    )
    required_rel_paths = _walk_template_required_paths(template_dir=template_dir)
    missing = [
        rel for rel in required_rel_paths if not (ctx.project_root / rel).is_file()
    ]
    if not missing:
        return Finding(
            check_id=f"doctor-{SLUG}",
            status="pass",
            message=(
                f"all {len(required_rel_paths)} template-required files present"
            ),
            path=None,
            line=None,
            spec_root=ctx.spec_root.relative_to(ctx.project_root).as_posix(),
        )
    return Finding(
        check_id=f"doctor-{SLUG}",
        status="fail",
        message=(
            f"{len(missing)} template-required file(s) missing: "
            + ", ".join(str(p) for p in missing)
        ),
        path=None,
        line=None,
        spec_root=ctx.spec_root.relative_to(ctx.project_root).as_posix(),
    )
