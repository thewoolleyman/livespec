"""livespec.doctor.static.version_contiguity — version sequence contiguity check.

Verifies that version directories under `<spec-root>/history/`
form a contiguous monotonic sequence. Per PROPOSAL.md §"`doctor`
→ Static-phase checks" lines 2708-2711 and Plan §"Phase 3" line
1481, this is the sixth of the eight Phase-3 minimum-subset
checks.

Per PROPOSAL.md lines 1715-1726: version numbers are integer-
numbered, zero-padded to ≥3 digits as `vNNN`; new versions are
zero-padded to `max(3, width-of-previous-highest-on-disk)`; mixed
widths within `history/` are valid (the `v999` → `v1000`
widening preserves historic widths). Numeric parsing applies —
not lexical (PROPOSAL.md lines 1718-1720). The check uses
numeric parsing so `v009` < `v010` < `v100` < `v1000` order
correctly.

Per PROPOSAL.md lines 2708-2711, contiguity applies "from
`pruned_range.end + 1`" when `PRUNED_HISTORY.json` exists at
the oldest surviving `vN-1` directory; otherwise from `v001`
upward. The pruned-marker branch (PROPOSAL.md lines 1781-1784:
"reads the marker file and applies contiguity only to surviving
versions") defers until a `prune-history` test forces it — no
`PRUNED_HISTORY.json` exists at Phase 3.

v032 TDD redo cycle 26: minimal authoring under outside-in
consumer pressure. The cycle-26 test seeds a livespec-template
tree (which has only `v001` after seed) and asserts a `pass`
Finding. A single-version sequence is trivially contiguous.
Multi-version coverage (v001 + v002 after `revise`) lands when
an integration test exercises the post-revise tree shape.
Failure-path findings (gap-detection, with the missing version
named in the message) and bootstrap lenience defer, same
pattern as cycles 21-25.

Out of cycle-26 scope (deferred):

- Pruned-marker handling: read `PRUNED_HISTORY.json` at the
  oldest surviving `vN-1` directory, anchor contiguity at
  `pruned_range.end + 1` per PROPOSAL.md lines 1781-1784. No
  consumer pressure yet.
- Failure-path Finding messages naming the specific missing
  version(s): land when a gap-detection test forces them.
- Sub-spec iteration: this check is uniform across spec trees
  per PROPOSAL.md §"Per-tree check applicability" — runs
  unconditionally, no main-tree-only restriction.

The `_VERSION_DIR_RE` regex matches `vNNN` with ≥3 digits
(`^v\\d{3,}$`), per PROPOSAL.md line 1721's "Width starts at 3
digits" + line 1726's "Mixed widths within `history/` are
valid". Cycle 25's `version_directories_complete` uses a
narrower `^v\\d{3}$` regex that doesn't match `v1000`+; that
narrower regex is itself a transitional minimum (no `v1000`+
exists at Phase 3) which a future width-widening test will
tighten.

`spec_root` is hardcoded to `"SPECIFICATION"` per the `livespec`
template's default; data-driven `spec_root` resolution lands
when a `minimal`-template test or sub-spec test forces it.
"""

from __future__ import annotations

import re

from livespec.context import DoctorContext
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "version-contiguity"

_VERSION_DIR_RE = re.compile(r"^v(\d{3,})$")


def run(*, ctx: DoctorContext) -> Finding:
    history_dir = ctx.spec_root / "history"
    if not history_dir.is_dir():
        return Finding(
            check_id=f"doctor-{SLUG}",
            status="pass",
            message="no <spec-root>/history/ directory; contiguity vacuously satisfied",
            path=None,
            line=None,
            spec_root=ctx.spec_root.relative_to(ctx.project_root).as_posix(),
        )
    version_numbers: list[int] = []
    for path in history_dir.iterdir():
        if not path.is_dir():
            continue
        match = _VERSION_DIR_RE.match(path.name)
        if match is None:
            continue
        version_numbers.append(int(match.group(1)))
    version_numbers.sort()
    if not version_numbers:
        return Finding(
            check_id=f"doctor-{SLUG}",
            status="pass",
            message="no version directories under <spec-root>/history/; vacuously satisfied",
            path=None,
            line=None,
            spec_root=ctx.spec_root.relative_to(ctx.project_root).as_posix(),
        )
    expected = list(range(1, version_numbers[-1] + 1))
    missing = [n for n in expected if n not in version_numbers]
    if not missing:
        return Finding(
            check_id=f"doctor-{SLUG}",
            status="pass",
            message=(
                f"version sequence v001..v{version_numbers[-1]:03d} contiguous"
                if version_numbers[-1] >= 1
                else "version sequence contiguous"
            ),
            path=None,
            line=None,
            spec_root=ctx.spec_root.relative_to(ctx.project_root).as_posix(),
        )
    missing_names = ", ".join(f"v{n:03d}" for n in missing)
    return Finding(
        check_id=f"doctor-{SLUG}",
        status="fail",
        message=(
            f"version sequence has gap(s) under <spec-root>/history/: "
            f"missing {missing_names}"
        ),
        path=None,
        line=None,
        spec_root=ctx.spec_root.relative_to(ctx.project_root).as_posix(),
    )
