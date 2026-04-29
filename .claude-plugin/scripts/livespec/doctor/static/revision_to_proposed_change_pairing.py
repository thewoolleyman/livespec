"""livespec.doctor.static.revision_to_proposed_change_pairing — pairing check.

Verifies that for every `<stem>-revision.md` file in
`<spec-root>/history/vNNN/proposed_changes/`, a corresponding
`<stem>.md` file exists in the same directory. Per PROPOSAL.md
§"`doctor` → Static-phase checks" lines 2712-2720 and Plan
§"Phase 3" line 1481, this is the seventh of the eight Phase-3
minimum-subset checks.

Pairing walks **filename stems**, NOT front-matter `topic`
values (PROPOSAL.md lines 2715-2720 + 2974-2985). Under v014 N6
collision disambiguation, `<stem>` may include a `-N` suffix
(e.g., `foo-2-revision.md` pairs with `foo-2.md`). The
front-matter `topic` field carries the canonical topic WITHOUT
the `-N` suffix; multiple files sharing a canonical topic share
the same `topic` field but have distinct filename stems. This is
why stem-based pairing is the correct algorithm — front-matter
`topic` collisions are the entire reason the `-N` suffix exists.

Per PROPOSAL.md line 2712-2714, the check scope is the **history
subtree** (`<spec-root>/history/vNNN/proposed_changes/`), NOT
the working `<spec-root>/proposed_changes/`. After a successful
`revise`, the working directory is empty of in-flight proposals
(only the skill-owned `README.md` persists, per PROPOSAL.md
lines 2450-2452); paired `*-revision.md` files exist only in
history per the revise lifecycle (PROPOSAL.md lines 2421-2431
move proposed-change + revision pairs into
`<spec-root>/history/vN/proposed_changes/`).

Stem derivation: a filename ending in `-revision.md` carries
`<stem>-revision.md` shape; the stem is the filename minus the
literal `-revision.md` suffix. Files whose names DO NOT end in
`-revision.md` are not revision files — they are either
proposed-change files (`<stem>.md`) or auxiliary files (e.g.,
`README.md` in the working directory; deferred per
PROPOSAL.md line 2452). The check ignores non-`*-revision.md`
files in its iteration.

v032 TDD redo cycle 27: minimal authoring under outside-in
consumer pressure. The cycle-27 test seeds a livespec-template
tree (which produces an auto-captured pair at
`<spec-root>/history/v001/proposed_changes/`: `seed.md` +
`seed-revision.md`) and asserts a `pass` Finding. Failure-path
findings (orphan `*-revision.md` with no paired `<stem>.md`) and
bootstrap lenience defer to subsequent cycles, same pattern as
cycles 21-26.

Out of cycle-27 scope (deferred):

- Failure-path Findings naming each orphan revision in the
  message: structurally present (the `fail` branch enumerates
  paths) but no failure-path test forces the message shape yet.
- Sub-spec iteration: this check is uniform across spec trees
  per PROPOSAL.md §"Per-tree check applicability" — runs
  unconditionally, no main-tree-only restriction. Sub-spec
  coverage lands when orchestrator iteration drives it.
- Bootstrap lenience (v014 N3) for `template_load_status`.

`spec_root` is hardcoded to `"SPECIFICATION"` per the `livespec`
template's default; data-driven `spec_root` resolution lands
when a `minimal`-template test or sub-spec test forces it (same
transitional collapse as cycles 21-26).
"""

from __future__ import annotations

import re
from pathlib import Path

from livespec.context import DoctorContext
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "revision-to-proposed-change-pairing"

_REVISION_SUFFIX = "-revision.md"
_VERSION_DIR_RE = re.compile(r"^v\d{3,}$")


def _list_version_proposed_changes_dirs(*, history_dir: Path) -> list[Path]:
    """Return every `<history>/v???/proposed_changes/` that exists as a directory."""
    if not history_dir.is_dir():
        return []
    result: list[Path] = []
    for version_dir in sorted(history_dir.iterdir()):
        if not version_dir.is_dir():
            continue
        if _VERSION_DIR_RE.match(version_dir.name) is None:
            continue
        proposed_changes_dir = version_dir / "proposed_changes"
        if not proposed_changes_dir.is_dir():
            continue
        result.append(proposed_changes_dir)
    return result


def _scan_pairings(*, proposed_changes_dir: Path) -> tuple[int, list[str]]:
    """Return `(paired_count, orphan_descriptions)` for one proposed_changes dir."""
    paired_count = 0
    orphans: list[str] = []
    version_dir_name = proposed_changes_dir.parent.name
    for revision_path in sorted(proposed_changes_dir.iterdir()):
        if not revision_path.is_file():
            continue
        if not revision_path.name.endswith(_REVISION_SUFFIX):
            continue
        stem = revision_path.name[: -len(_REVISION_SUFFIX)]
        paired_path = proposed_changes_dir / f"{stem}.md"
        if paired_path.is_file():
            paired_count += 1
        else:
            orphans.append(
                f"{version_dir_name}/proposed_changes/{revision_path.name} "
                f"has no paired {stem}.md"
            )
    return paired_count, orphans


def run(*, ctx: DoctorContext) -> Finding:
    history_dir = ctx.spec_root / "history"
    proposed_changes_dirs = _list_version_proposed_changes_dirs(history_dir=history_dir)
    paired_total = 0
    orphans: list[str] = []
    for proposed_changes_dir in proposed_changes_dirs:
        paired_count, dir_orphans = _scan_pairings(
            proposed_changes_dir=proposed_changes_dir
        )
        paired_total += paired_count
        orphans.extend(dir_orphans)
    if not orphans:
        return Finding(
            check_id=f"doctor-{SLUG}",
            status="pass",
            message=(
                f"all {paired_total} <stem>-revision.md file(s) under "
                f"<spec-root>/history/v???/proposed_changes/ paired with <stem>.md"
            ),
            path=None,
            line=None,
            spec_root=ctx.spec_root.relative_to(ctx.project_root).as_posix(),
        )
    return Finding(
        check_id=f"doctor-{SLUG}",
        status="fail",
        message=(
            f"{len(orphans)} orphan revision file(s): " + "; ".join(orphans)
        ),
        path=None,
        line=None,
        spec_root=ctx.spec_root.relative_to(ctx.project_root).as_posix(),
    )
