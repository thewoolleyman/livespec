"""livespec.doctor.static.version_directories_complete — per-version completeness check.

Verifies that every `<spec-root>/history/vNNN/` directory contains
the full set of template-required files, a `proposed_changes/`
subdir, and (when the active template declares one) a per-version
`README.md`. The pruned-marker directory contains ONLY
`PRUNED_HISTORY.json`. Per PROPOSAL.md §"`doctor` → Static-phase
checks" lines 2699-2707 and Plan §"Phase 3" line 1481, this is
the fifth of the eight Phase-3 minimum-subset checks.

Template-required files are derived by walking the active
template's `specification-template/` directory (PROPOSAL.md
lines 1416-1422). Per Plan §"Phase 2" lines 1211-1214, that
directory is currently an "empty skeleton (directory tree only,
no starter content files)"; the walker excludes `.gitkeep`
git-housekeeping placeholders (same reasoning as cycle 23's
`template_files_present`). At Phase 3 the derived requirement
set is empty, so the check trivially passes the file-list
portion. The `proposed_changes/` subdir requirement remains
load-bearing — `seed.py` materializes
`<spec-root>/history/v001/proposed_changes/` (cycle 4 of the
seed redo). When Phase 7 populates `specification-template/`
with real content, the check meaningfully validates each
version directory's snapshot completeness.

The walk-helper duplicates `template_files_present`'s walker
(same `<template>/specification-template/` scan, same
`.gitkeep` exclusion). Two consumers don't yet justify
extraction per Kent Beck's three-strikes rule; the third
consumer of this walk (likely a sub-spec-targeting check or
the eventual `out-of-band-edits` Phase-7 check) will trigger
the lift to a shared helper.

v032 TDD redo cycle 25: minimal authoring under outside-in
consumer pressure. The cycle-25 test seeds a livespec-template
tree (which has only `v001` after seed) and asserts a `pass`
Finding. Failure-path branches and bootstrap lenience defer to
subsequent cycles, same pattern as cycles 21-24.

Out of cycle-25 scope (deferred):

- Pruned-marker handling (PROPOSAL.md lines 2705-2707): no
  `PRUNED_HISTORY.json` exists at Phase 3 — lands when a
  `prune-history` test forces it.
- Per-version README requirement (PROPOSAL.md lines 2702-2705):
  derived-from-walk and vacuously satisfied at Phase 3 because
  `specification-template/` is empty. Phase 7 makes this
  meaningful when `specification-template/SPECIFICATION/README.md`
  becomes a real walked file.
- Failure-path Findings: each missing file in a version
  directory could surface a path-and-name-specific Finding.
- Bootstrap lenience (v014 N3) for `template_load_status`.
- Sub-spec iteration: this check is uniform across spec trees
  per PROPOSAL.md §"Per-tree check applicability" — runs
  unconditionally for every spec tree, no main-tree-only
  restriction. Sub-spec coverage lands when orchestrator
  iteration drives it.

`spec_root` is hardcoded to `"SPECIFICATION"` per the `livespec`
template's default; data-driven `spec_root` resolution lands when
a `minimal`-template test or sub-spec test forces it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from livespec.context import DoctorContext
from livespec.paths import bundle_root
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "version-directories-complete"

_BUILTIN_TEMPLATES = frozenset({"livespec", "minimal"})

_GITKEEP_EXCLUSIONS = frozenset({".gitkeep"})

_VERSION_DIR_RE = re.compile(r"^v\d{3}$")


def _resolve_template_path(*, project_root: Path, template_value: str) -> Path:
    if template_value in _BUILTIN_TEMPLATES:
        return bundle_root() / "specification-templates" / template_value
    return project_root / template_value


def _walk_template_required_paths(*, template_dir: Path) -> list[Path]:
    """Walk `<template>/specification-template/` for required files.

    Excludes `.gitkeep`. Returns paths relative to
    `<template-dir>/specification-template/`. See cycle 23
    `template_files_present.py` for the same walker; duplicated
    here pending three-strikes refactor.
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


def _list_version_directories(*, history_dir: Path) -> list[Path]:
    if not history_dir.is_dir():
        return []
    return sorted(
        path for path in history_dir.iterdir()
        if path.is_dir() and _VERSION_DIR_RE.match(path.name)
    )


def _missing_in_version_dir(*, version_dir: Path, required_rel_paths: list[Path]) -> list[str]:
    missing: list[str] = []
    for rel in required_rel_paths:
        if not (version_dir / rel).is_file():
            missing.append(f"{version_dir.name}/{rel}")
    if not (version_dir / "proposed_changes").is_dir():
        missing.append(f"{version_dir.name}/proposed_changes/")
    return missing


def run(*, ctx: DoctorContext) -> Finding:
    config_path = ctx.project_root / ".livespec.jsonc"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    template_value = config["template"]
    template_dir = _resolve_template_path(
        project_root=ctx.project_root, template_value=template_value
    )
    required_rel_paths = _walk_template_required_paths(template_dir=template_dir)
    history_dir = ctx.spec_root / "history"
    version_dirs = _list_version_directories(history_dir=history_dir)
    missing: list[str] = []
    for version_dir in version_dirs:
        missing.extend(
            _missing_in_version_dir(
                version_dir=version_dir, required_rel_paths=required_rel_paths
            )
        )
    if not missing:
        return Finding(
            check_id=f"doctor-{SLUG}",
            status="pass",
            message=(
                f"all {len(version_dirs)} version director(y/ies) complete"
            ),
            path=None,
            line=None,
            spec_root=ctx.spec_root.relative_to(ctx.project_root).as_posix(),
        )
    return Finding(
        check_id=f"doctor-{SLUG}",
        status="fail",
        message=(
            f"{len(missing)} missing artifact(s) under <spec-root>/history/: "
            + ", ".join(missing)
        ),
        path=None,
        line=None,
        spec_root=ctx.spec_root.relative_to(ctx.project_root).as_posix(),
    )
