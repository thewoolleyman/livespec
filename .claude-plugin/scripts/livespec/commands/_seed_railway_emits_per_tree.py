"""Per-spec-tree skill-owned README emissions for the `seed` sub-command.

Phase 7 sub-step 1.c: holds the per-tree skill-owned file
emissions that the v002 spec edit mandates — `history/README.md`
for the main spec (cycle 1) plus `proposed_changes/README.md`
per sub-spec (cycle 2) and (in subsequent cycles)
`history/README.md` per sub-spec plus the empty-
`history/v001/proposed_changes/` `.gitkeep` marker per sub-spec.

Extracted from `_seed_railway_emits.py` to keep that module under
the 200-LLOC ceiling enforced by `check-complexity`. The sibling
module re-exports each helper (so the existing
`from livespec.commands._seed_railway_emits import _emit_skill_owned_history_readme`
import surface continues to work).
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult

from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.seed_input import SeedInput

__all__: list[str] = [
    "_emit_skill_owned_history_readme",
    "_emit_skill_owned_sub_spec_history_readmes",
    "_emit_skill_owned_sub_spec_history_v001_gitkeeps",
    "_emit_skill_owned_sub_spec_proposed_changes_readmes",
]


_MIN_PARTS_MAIN_SPEC: int = 2
_MIN_PARTS_SUB_SPEC: int = 4
_SUB_SPEC_ROOT_PARTS_PREFIX: int = 3


_HISTORY_README_TEXT_MAIN_SPEC = (
    "# History\n"
    "\n"
    "This directory holds the immutable per-revision snapshots of the\n"
    "specification. Each `vNNN/` subdirectory contains a byte-identical\n"
    "copy of every spec file as it stood when revision `vNNN` was\n"
    "finalized. Versions are contiguous starting at `v001`. Each\n"
    "`vNNN/proposed_changes/` subdirectory contains the proposed-change\n"
    "files plus paired `-revision.md` records that drove that revision.\n"
    "The directory is skill-owned: `livespec` writes new versions on\n"
    "`/livespec:revise`, `/livespec:prune-history` removes the oldest\n"
    "contiguous block down to a caller-specified retention horizon, and\n"
    "the doctor static phase enforces version contiguity plus\n"
    "revision-pairing invariants.\n"
)


_PROPOSED_CHANGES_README_TEXT_SUB_SPEC = (
    "# Proposed Changes\n"
    "\n"
    "This directory holds in-flight proposed changes to the\n"
    "specification. Each file is named `<topic>.md` and contains\n"
    "one or more `## Proposal: <name>` sections with target\n"
    "specification files, summary, motivation, and proposed\n"
    "changes (prose or unified diff). Files are processed by\n"
    "`livespec revise` in creation-time order (YAML `created_at`\n"
    "front-matter field) and moved into\n"
    "`../history/vNNN/proposed_changes/` when revised. After a\n"
    "successful `revise`, this directory is empty.\n"
)


def _emit_skill_owned_history_readme(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Write `<main-spec-root>/history/README.md` (skill-owned dir marker)."""
    if not seed_input.files:
        return IOResult.from_value(seed_input)
    first_path = Path(seed_input.files[0]["path"])
    if len(first_path.parts) < _MIN_PARTS_MAIN_SPEC:
        return IOResult.from_value(seed_input)
    spec_root_name = first_path.parts[0]
    history_readme = project_root / spec_root_name / "history" / "README.md"
    return fs.write_text(
        path=history_readme,
        text=_HISTORY_README_TEXT_MAIN_SPEC,
    ).map(lambda _: seed_input)


def _resolve_sub_spec_readme_target(
    *,
    sub_spec: dict[str, object],
    project_root: Path,
) -> Path | None:
    """Derive `<sub-spec-root>/proposed_changes/README.md`, or None if invalid."""
    files_list = sub_spec["files"]
    if not isinstance(files_list, list):
        return None
    for entry in files_list:
        if not isinstance(entry, dict):
            continue
        original_path = Path(str(entry["path"]))
        if len(original_path.parts) < _MIN_PARTS_SUB_SPEC:
            continue
        sub_spec_root = project_root.joinpath(*original_path.parts[:_SUB_SPEC_ROOT_PARTS_PREFIX])
        return sub_spec_root / "proposed_changes" / "README.md"
    return None


def _emit_skill_owned_sub_spec_proposed_changes_readmes(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Write `<sub-spec-root>/proposed_changes/README.md` for every sub-spec."""
    accumulator: IOResult[SeedInput, LivespecError] = IOResult.from_value(seed_input)
    for sub_spec in seed_input.sub_specs:
        readme_target = _resolve_sub_spec_readme_target(
            sub_spec=sub_spec,
            project_root=project_root,
        )
        if readme_target is None:
            continue
        accumulator = accumulator.bind(
            lambda _value, target=readme_target: fs.write_text(
                path=target,
                text=_PROPOSED_CHANGES_README_TEXT_SUB_SPEC,
            ).map(lambda _: seed_input),
        )
    return accumulator


def _resolve_sub_spec_history_readme_target(
    *,
    sub_spec: dict[str, object],
    project_root: Path,
) -> Path | None:
    """Derive `<sub-spec-root>/history/README.md`, or None if invalid."""
    files_list = sub_spec["files"]
    if not isinstance(files_list, list):
        return None
    for entry in files_list:
        if not isinstance(entry, dict):
            continue
        original_path = Path(str(entry["path"]))
        if len(original_path.parts) < _MIN_PARTS_SUB_SPEC:
            continue
        sub_spec_root = project_root.joinpath(*original_path.parts[:_SUB_SPEC_ROOT_PARTS_PREFIX])
        return sub_spec_root / "history" / "README.md"
    return None


def _emit_skill_owned_sub_spec_history_readmes(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Write `<sub-spec-root>/history/README.md` for every sub-spec."""
    accumulator: IOResult[SeedInput, LivespecError] = IOResult.from_value(seed_input)
    for sub_spec in seed_input.sub_specs:
        readme_target = _resolve_sub_spec_history_readme_target(
            sub_spec=sub_spec,
            project_root=project_root,
        )
        if readme_target is None:
            continue
        accumulator = accumulator.bind(
            lambda _value, target=readme_target: fs.write_text(
                path=target,
                text=_HISTORY_README_TEXT_MAIN_SPEC,
            ).map(lambda _: seed_input),
        )
    return accumulator


def _resolve_sub_spec_history_v001_gitkeep_target(
    *,
    sub_spec: dict[str, object],
    project_root: Path,
) -> Path | None:
    """Derive `<sub-spec-root>/history/v001/proposed_changes/.gitkeep`, or None."""
    files_list = sub_spec["files"]
    if not isinstance(files_list, list):
        return None
    for entry in files_list:
        if not isinstance(entry, dict):
            continue
        original_path = Path(str(entry["path"]))
        if len(original_path.parts) < _MIN_PARTS_SUB_SPEC:
            continue
        sub_spec_root = project_root.joinpath(*original_path.parts[:_SUB_SPEC_ROOT_PARTS_PREFIX])
        return sub_spec_root / "history" / "v001" / "proposed_changes" / ".gitkeep"
    return None


def _emit_skill_owned_sub_spec_history_v001_gitkeeps(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Write `<sub-spec-root>/history/v001/proposed_changes/.gitkeep` per sub-spec."""
    accumulator: IOResult[SeedInput, LivespecError] = IOResult.from_value(seed_input)
    for sub_spec in seed_input.sub_specs:
        gitkeep_target = _resolve_sub_spec_history_v001_gitkeep_target(
            sub_spec=sub_spec,
            project_root=project_root,
        )
        if gitkeep_target is None:
            continue
        accumulator = accumulator.bind(
            lambda _value, target=gitkeep_target: fs.write_text(
                path=target,
                text="",
            ).map(lambda _: seed_input),
        )
    return accumulator
