"""Per-spec-tree skill-owned README emissions for the `seed` sub-command.

Phase 7 sub-step 1.c: holds the per-tree skill-owned file
emissions that the v002 spec edit mandates — `history/README.md`
for the main spec at this cycle, and (in subsequent cycles)
`proposed_changes/README.md` + `history/README.md` per sub-spec
plus the empty-`history/v001/proposed_changes/` `.gitkeep` marker
for sub-specs.

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
]


_MIN_PARTS_MAIN_SPEC: int = 2


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
