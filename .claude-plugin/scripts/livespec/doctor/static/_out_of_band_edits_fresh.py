# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. Per-call cast
# or refactor to named typed functions is the canonical fix; this file's
# railway composition pattern means roughly half of all lines are bind
# targets, so file-level silencing keeps the source readable. Non-railway
# code in this tree retains full enforcement (other modules do not carry
# this pragma). reportArgumentType is left ON so non-HKT firings still
# surface; HKT-related reportArgumentType call sites carry per-line
# ignore markers attached to the offending argument's line below.
"""Fresh-working-tree-revision routing for the out-of-band-edits auto-backfill.

Extracted from `_out_of_band_edits_writes.py` so that file's LLOC
stays under the 250-LLOC hard ceiling enforced by
`dev-tooling/checks/file_lloc.py` (the same extraction precedent
that produced `_out_of_band_edits_writes.py` itself).

Ordering invariant (work-item livespec-6p9e defect 2): the
auto-backfill records PRE-EXISTING HEAD state, so it always claims
the HEAD-derived v(N+1) slot — chronologically BENEATH any
freshly-cut working-tree revision. When a non-empty working-tree
v-dir above the HEAD baseline exists (an in-flight revise),
`route_drift_outcome` never writes:

- absorbed (the newest fresh revision byte-covers every diverging
  file's HEAD-active state) → skipped-Finding notice; commit the
  in-flight revision and re-run.
- unabsorbed → skipped-Finding refusal prescribing backfill-first
  re-run order (relocate the fresh revision one slot up, re-run so
  the backfill claims the slot beneath it).

Both outcomes stay on the IOSuccess track as skipped-Findings,
mirroring the pre-backfill guard idiom: in-flight state is an
expected business outcome, and fail-Findings are reserved for
"backfill written; commit it".
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.doctor.static._out_of_band_edits_pure import (
    _is_empty_dir,
    _parse_version_number,
)
from livespec.errors import LivespecError
from livespec.io.git import show_at_head
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = [
    "_newest_fresh_working_tree_revision",
    "_route_fresh_revision_outcome",
]


# Type alias for the parent check's `_make_finding` callable, threaded
# through `_route_fresh_revision_outcome` so this module does not
# duplicate the Finding-construction formula. Keyword-only signature
# mirrors the parent helper one-to-one.
_MakeFinding = Callable[..., Finding]


_HISTORY_SUBDIR_NAME: str = "history"


def _fresh_candidate_number(*, child: Path, head_n: int) -> int | None:
    """Version number when `child` is a non-empty vNNN dir above `head_n`, else None.

    Filters one `history/` child for the fresh-working-tree-revision
    scan: non-dirs, non-vNNN names, versions at-or-below the HEAD
    baseline, and empty leftover dirs (the pre-backfill guard's
    condition-B shape, not a freshly-cut snapshot) are all
    non-candidates.
    """
    if not child.is_dir():
        return None
    parsed = _parse_version_number(version_path=child)
    if parsed is None or parsed <= head_n:
        return None
    if _is_empty_dir(dir_path=child):
        return None
    return parsed


def _newest_fresh_working_tree_revision(
    *,
    spec_root: Path,
    head_latest_label: str,
) -> Path | None:
    """Newest NON-EMPTY working-tree `vNNN/` strictly above the HEAD-latest version.

    A non-empty v-dir above the HEAD baseline is a freshly-cut,
    not-yet-committed revision (typically an in-flight revise).
    Returns the newest such dir, or None when the working tree has
    no fresh revision — including when `history/` itself is absent
    from the working tree (the comparison is HEAD-based; the write
    path recreates the directory tree).

    Supersedes the memo-mm-gzi7ej slot walk that skipped PAST fresh
    dirs into the slot above them (work-item livespec-6p9e defect 2:
    that ordering snapshotted stale HEAD content as the newest
    version). The non-clobbering guarantee is preserved by routing
    around the write path entirely instead.
    """
    head_n = int(head_latest_label[1:])
    history = spec_root / _HISTORY_SUBDIR_NAME
    if not history.is_dir():
        return None
    candidates = [
        parsed
        for child in history.iterdir()
        if (parsed := _fresh_candidate_number(child=child, head_n=head_n)) is not None
    ]
    if not candidates:
        return None
    return history / f"v{max(candidates):03d}"


def _show_or_none(
    *,
    ctx: DoctorContext,
    repo_relative_path: Path,
) -> IOResult[bytes | None, LivespecError]:
    """IOSuccess(bytes) when path is at HEAD; IOSuccess(None) when absent.

    `.lash` absorbs path-missing-at-HEAD failure into None on the
    success rail. Mirrors the same-named helpers in
    `out_of_band_edits.py` and `_out_of_band_edits_writes.py`.
    """
    return show_at_head(
        project_root=ctx.project_root,
        repo_relative_path=repo_relative_path,
    ).lash(
        lambda _err: IOSuccess(None),  # pyright: ignore[reportArgumentType]
    )


def _file_absorbed(*, active_bytes: bytes | None, fresh_file: Path) -> bool:
    """True iff the fresh revision's snapshot records exactly the HEAD-active state.

    `active_bytes is None` means the file is a missing-active
    divergence (deleted at HEAD-active); absorption then means the
    fresh snapshot dropped it too. Otherwise the fresh snapshot
    must carry the HEAD-active bytes byte-identically.
    """
    if active_bytes is None:
        return not fresh_file.is_file()
    return fresh_file.is_file() and fresh_file.read_bytes() == active_bytes


def _collect_unabsorbed(
    *,
    ctx: DoctorContext,
    fresh_dir: Path,
    diverging_files: list[str],
) -> IOResult[list[str], LivespecError]:
    """Aggregate the diverging basenames whose HEAD-active state `fresh_dir` does NOT cover."""
    spec_root_repo_rel = ctx.spec_root.relative_to(ctx.project_root)
    accumulator: IOResult[list[str], LivespecError] = IOSuccess([])
    for basename in diverging_files:
        active_path = spec_root_repo_rel / basename
        fresh_file = fresh_dir / basename
        accumulator = accumulator.bind(
            lambda unabsorbed, ap=active_path, ff=fresh_file, name=basename: _show_or_none(
                ctx=ctx,
                repo_relative_path=ap,
            ).map(
                lambda active_bytes, unabsorbed=unabsorbed, ff=ff, name=name: unabsorbed
                if _file_absorbed(active_bytes=active_bytes, fresh_file=ff)
                else [*unabsorbed, name],
            ),
        )
    return accumulator


def _absorbed_skip_message(*, fresh_label: str) -> str:
    """Compose the skipped-Finding message for an already-absorbed divergence."""
    return (
        f"HEAD divergence already absorbed by uncommitted history/{fresh_label}; "
        f"auto-backfill skipped — commit the in-flight revision and re-run"
    )


def _unabsorbed_refuse_message(*, fresh_label: str) -> str:
    """Compose the skipped-Finding message refusing to backfill above a fresh revision."""
    return (
        f"uncommitted history/{fresh_label} does not absorb the HEAD divergence; "
        f"auto-backfill refused — the backfill must precede the fresh revision: "
        f"relocate history/{fresh_label} one version slot up, re-run doctor so the "
        f"backfill claims the slot beneath it, then commit both"
    )


def _route_fresh_revision_outcome(
    *,
    ctx: DoctorContext,
    make_finding: _MakeFinding,
    fresh_dir: Path,
    diverging_files: list[str],
) -> IOResult[Finding, LivespecError]:
    """Skip (absorbed) or refuse (unabsorbed) instead of backfilling above a fresh cut.

    Work-item livespec-6p9e defect 2: a backfill records
    PRE-EXISTING HEAD state, so it belongs chronologically BENEATH
    any freshly-cut working-tree revision. Writing it above
    snapshots stale HEAD content as the newest version, reverting
    the freshly accepted files.
    """
    fresh_label = fresh_dir.name
    return _collect_unabsorbed(
        ctx=ctx,
        fresh_dir=fresh_dir,
        diverging_files=diverging_files,
    ).map(
        lambda unabsorbed: make_finding(
            ctx=ctx,
            status="skipped",
            message=_unabsorbed_refuse_message(fresh_label=fresh_label)
            if unabsorbed
            else _absorbed_skip_message(fresh_label=fresh_label),
        ),
    )
