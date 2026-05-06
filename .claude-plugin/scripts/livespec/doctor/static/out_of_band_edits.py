"""Static-phase doctor check: out_of_band_edits.

Per Plan Phase 7 sub-step 7.a + PROPOSAL.md §"`doctor` →
Static-phase checks": the `out-of-band-edits` check detects
HEAD-committed spec files whose contents have diverged from
their HEAD-committed `history/vN/` snapshot (i.e., edits made
to the active spec without the propose-change → revise pipeline
that would otherwise land a paired snapshot at history/v(N+1)).
It is the only doctor check whose `run()` has a narrow
auto-backfill write path (per `static/CLAUDE.md`); auto-backfill
on detected drift lands in cycle 7.a.v.

Cycle 7.a.ii landed the smallest viable skeleton: it
discriminates on whether `ctx.spec_root` is inside a git
working tree.

Cycle 7.a.iii widens the in-git-repo branch with a pre-backfill
guard. Per PROPOSAL §"Static-phase checks → out-of-band-edits →
Pre-backfill guard — uncommitted prior backfill present", the
guard fires on either of two leftover-from-prior-run shapes
BEFORE the divergence comparison or the auto-backfill write
path:

  - Condition A: any `<spec-root>/proposed_changes/
    out-of-band-edit-*.md` file is on disk (a prior auto-
    backfill artifact the user did not commit).
  - Condition B: `<spec-root>/history/v(N+1)/` is on disk,
    where N is the highest committed version-snapshot.
    Empty v-dirs are NOT counted as committed prior versions
    — they ARE the leftover-from-prior-backfill candidate. If
    `<spec-root>/history/` itself is absent, condition B is
    FALSE (no prior versions for any v(N+1) to claim). If
    `history/` exists but contains no v-dirs (only README.md
    or similar), N=0 and the guard checks v001.

Either condition emits IOSuccess(Finding(status="skipped")).
Per memory feedback_domain_errors_vs_bugs the leftover state
is an EXPECTED business outcome, not a bug, so it stays on
the IOSuccess track.

Cycle 7.a.iv (redo) replaces the placeholder pass-Finding with
HEAD-active-vs-HEAD-history-vN comparison per PROPOSAL
§"Static-phase checks → out-of-band-edits → Comparison":
"diffs `git show HEAD:<spec-root>/<spec-file>` against `git
show HEAD:<spec-root>/history/vN/<spec-file>` for each
template-declared spec file. Both sides are HEAD-committed
artifacts; working-tree WIP is ignored for the comparison."

This redo replaces the prior wrong-divergence-semantics 7.a.iv
attempt (orphan tag `wrong-7a-impl-2026-05-05`) which
incorrectly compared working-tree state against HEAD. Per
PROPOSAL the comparison runs entirely on git HEAD content;
working-tree WIP is irrelevant.

The "template-declared spec files" enumeration is realized as
"the immediate top-level files at HEAD under `<spec-root>/`",
walked via `livespec.io.git.list_at_head`. Subdirs
(`history/`, `proposed_changes/`, `templates/`) are excluded
by ls-tree's blob-only filter, so the enumeration matches
the top-level *.md files the seed materializes.

Latest-vNNN-at-HEAD is resolved by probing `show_at_head` on
each candidate `<spec_root>/history/vNNN` path: `git show`
exits 0 for both blobs and trees that exist at HEAD, so the
IOResult success/fail signal cleanly tracks "this v-dir
exists at HEAD". The probe walks v001 forward and stops at
the first absent candidate; the highest successful N is the
comparison target.

Edge case decisions (PROPOSAL silent; codified here):

  - No `<spec-root>/history/` at HEAD: emits `status="pass"`
    with a "no HEAD history baseline" message. Benign post-
    seed pre-revise state — nothing to compare against. The
    pre-backfill guard already covers leftover cases.
  - `history/` at HEAD with no `vNNN/` subdirs at HEAD: same.
    Without a vN snapshot to diff against, "no drift" is the
    correct outcome.

NO writes happen in this cycle — the auto-backfill write path
(`<spec-root>/proposed_changes/out-of-band-edit-<UTC>.md` +
`<spec-root>/history/v(N+1)/...`) lands at 7.a.v.

Per v018 Q1: applies to all spec-text-bearing trees (main +
each sub-spec).
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.doctor.static._out_of_band_edits_pure import (
    _is_empty_dir,
    _make_finding,
    _parse_version_number,
)
from livespec.doctor.static._out_of_band_edits_writes import (
    route_drift_outcome,
)
from livespec.errors import LivespecError
from livespec.io.git import is_git_repo, list_at_head, show_at_head
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "doctor-out-of-band-edits"

_OOB_PROPOSED_CHANGE_GLOB: str = "out-of-band-edit-*.md"
_VERSION_DIR_PREFIX: str = "v"
_HISTORY_SUBDIR_NAME: str = "history"
# Width for zero-padded vNNN directory naming (e.g., "v001" → 3).
_VERSION_DIR_PADDING: int = 3


def _has_oob_proposed_change_file(*, spec_root: Path) -> bool:
    """Return True iff condition A is satisfied (existing OOB proposed-change file)."""
    proposed_changes = spec_root / "proposed_changes"
    if not proposed_changes.is_dir():
        return False
    return any(proposed_changes.glob(_OOB_PROPOSED_CHANGE_GLOB))


def _has_leading_empty_version_dir(*, spec_root: Path) -> bool:
    """Return True iff condition B is satisfied (leading empty `v(N+1)/`).

    N is the max version-number among NON-EMPTY parsed v-dirs
    (default 0). Empty v-dirs do not count toward N because
    they ARE the v(N+1) leftover candidate the guard detects.
    With no v-dirs at all, N=0 and the guard checks v001.
    """
    history = spec_root / _HISTORY_SUBDIR_NAME
    if not history.is_dir():
        return False
    non_empty_versions: list[int] = []
    for child in history.iterdir():
        if not child.is_dir():
            continue
        parsed = _parse_version_number(version_path=child)
        if parsed is None:
            continue
        if _is_empty_dir(dir_path=child):
            continue
        non_empty_versions.append(parsed)
    highest_committed = max(non_empty_versions, default=0)
    candidate = history / f"{_VERSION_DIR_PREFIX}{highest_committed + 1:0{_VERSION_DIR_PADDING}d}"
    return candidate.is_dir()


def _spec_root_repo_relative(*, ctx: DoctorContext) -> Path:
    """Return `ctx.spec_root` as a path relative to `ctx.project_root`.

    Required by `git -C <project_root> show HEAD:<path>` and
    `git -C <project_root> ls-tree HEAD <dir>/`, which both
    take repo-root-relative paths. The orchestrator
    constructs `spec_root` as a subpath of `project_root`,
    so `relative_to` is straight-line at this call site.
    """
    return ctx.spec_root.relative_to(ctx.project_root)


def _show_or_none(*, ctx: DoctorContext, path: Path) -> IOResult[bytes | None, LivespecError]:
    """IOSuccess(bytes) when path is at HEAD; IOSuccess(None) on any HEAD-side failure.

    The .lash absorbs the path-missing-at-HEAD failure (the only
    failure mode the comparison treats as a domain signal) into
    a None marker on the success rail.
    """
    return show_at_head(project_root=ctx.project_root, repo_relative_path=path).lash(
        lambda _err: IOSuccess(None),
    )


def _probe_v_dirs(
    *,
    ctx: DoctorContext,
    history_repo_rel: Path,
    n: int,
    acc: tuple[str, ...],
) -> IOResult[tuple[str, ...], LivespecError]:
    """Probe v001, v002, ... at HEAD; halt at first absent; return accumulator.

    `git show HEAD:<path>` exits 0 for both blobs and trees that
    exist at HEAD, so the IOSuccess/IOFailure signal cleanly
    tracks "this v-dir exists at HEAD". The .lash combinator
    bottoms the recursion out at the first absent candidate.
    """
    name = f"{_VERSION_DIR_PREFIX}{n:0{_VERSION_DIR_PADDING}d}"
    return (
        show_at_head(
            project_root=ctx.project_root,
            repo_relative_path=history_repo_rel / name,
        )
        .bind(
            lambda _b: _probe_v_dirs(
                ctx=ctx,
                history_repo_rel=history_repo_rel,
                n=n + 1,
                acc=(*acc, name),
            ),
        )
        .lash(lambda _err: IOSuccess(acc))
    )


def _latest_committed_version_at_head(
    *,
    ctx: DoctorContext,
) -> IOResult[str | None, LivespecError]:
    """Latest `vNNN` dir at HEAD under `<spec_root>/history/`, or None when no v-dir exists."""
    history_repo_rel = _spec_root_repo_relative(ctx=ctx) / _HISTORY_SUBDIR_NAME
    return _probe_v_dirs(ctx=ctx, history_repo_rel=history_repo_rel, n=1, acc=()).map(
        lambda v_names: max(v_names, default=None),
    )


def _compare_one_file(
    *,
    ctx: DoctorContext,
    file_basename: str,
    latest_version_label: str,
) -> IOResult[bool, LivespecError]:
    """IOSuccess(True) iff active and history-vN diverge for the file at HEAD.

    Both-None cannot reach this helper (the union enumeration
    only emits basenames present on at least one side); so
    one-None or unequal-bytes cleanly map to True.
    """
    spec_rel = _spec_root_repo_relative(ctx=ctx)
    active = spec_rel / file_basename
    history = spec_rel / _HISTORY_SUBDIR_NAME / latest_version_label / file_basename
    return _show_or_none(ctx=ctx, path=active).bind(
        lambda a: _show_or_none(ctx=ctx, path=history).map(
            lambda h: a is None or h is None or a != h,
        ),
    )


def _enumerate_union_file_basenames(
    *,
    ctx: DoctorContext,
    latest_version_label: str,
) -> IOResult[tuple[str, ...], LivespecError]:
    """Return the sorted union of file basenames at HEAD under active and history-vN.

    The comparison must consider files present on EITHER side
    (active-only or history-only counts as drift). Both
    `list_at_head` calls return IOSuccess(()) for empty/
    missing subtrees, so the union+sort works regardless.
    """
    spec_root_repo_rel = _spec_root_repo_relative(ctx=ctx)
    history_v_path = spec_root_repo_rel / _HISTORY_SUBDIR_NAME / latest_version_label
    return list_at_head(
        project_root=ctx.project_root,
        repo_relative_dir=spec_root_repo_rel,
    ).bind(
        lambda active_names: list_at_head(
            project_root=ctx.project_root,
            repo_relative_dir=history_v_path,
        ).map(
            lambda history_names: tuple(sorted(set(active_names) | set(history_names))),
        ),
    )


def _aggregate_drifts(
    *,
    ctx: DoctorContext,
    latest_version_label: str,
    file_basenames: tuple[str, ...],
) -> IOResult[list[str], LivespecError]:
    """Aggregate per-file drift outcomes into a sorted list of diverging basenames."""
    accumulator: IOResult[list[str], LivespecError] = IOSuccess([])
    for basename in file_basenames:
        accumulator = accumulator.bind(
            lambda current, b=basename: _compare_one_file(
                ctx=ctx,
                file_basename=b,
                latest_version_label=latest_version_label,
            ).map(
                lambda diverged, c=current, name=b: [*c, name] if diverged else c,
            ),
        )
    return accumulator


def _run_divergence_or_no_baseline(
    *,
    ctx: DoctorContext,
    latest: str | None,
) -> IOResult[Finding, LivespecError]:
    """Run the comparison for `latest`, or emit the no-baseline pass when `latest` is None.

    On non-empty divergence the writes-module's `route_drift_outcome`
    auto-backfills under `<spec_root>/history/v(N+1)/` before
    composing the fail-Finding, per PROPOSAL §"Backfill on drift".
    """
    if latest is None:
        return IOSuccess(
            _make_finding(
                ctx=ctx,
                status="pass",
                message="no HEAD history baseline; nothing to compare",
            ),
        )
    return _enumerate_union_file_basenames(
        ctx=ctx,
        latest_version_label=latest,
    ).bind(
        lambda names: _aggregate_drifts(
            ctx=ctx,
            latest_version_label=latest,
            file_basenames=names,
        ).bind(
            lambda diverging, names=names: route_drift_outcome(
                ctx=ctx,
                make_finding=_make_finding,
                latest_version_label=latest,
                enumerated_files=names,
                diverging_files=diverging,
            ),
        ),
    )


def _run_in_git_repo_after_guard(
    *,
    ctx: DoctorContext,
) -> IOResult[Finding, LivespecError]:
    """Resolve the latest vN at HEAD and dispatch to comparison or no-baseline pass."""
    return _latest_committed_version_at_head(ctx=ctx).bind(
        lambda latest: _run_divergence_or_no_baseline(ctx=ctx, latest=latest),
    )


_PRE_BACKFILL_GUARD_MESSAGE: str = (
    "auto-backfill artifact already present from prior run; manual intervention required"
)
_NOT_IN_GIT_REPO_MESSAGE: str = "spec_root is not inside a git working tree"


def _skipped(*, ctx: DoctorContext, message: str) -> IOResult[Finding, LivespecError]:
    """Return IOSuccess(skipped-Finding) with `message`."""
    return IOSuccess(_make_finding(ctx=ctx, status="skipped", message=message))


def _select_finding_in_git_repo(
    *,
    ctx: DoctorContext,
) -> IOResult[Finding, LivespecError]:
    """Apply the pre-backfill guard, then run the comparison if it cleared."""
    if _has_oob_proposed_change_file(spec_root=ctx.spec_root):
        return _skipped(ctx=ctx, message=_PRE_BACKFILL_GUARD_MESSAGE)
    if _has_leading_empty_version_dir(spec_root=ctx.spec_root):
        return _skipped(ctx=ctx, message=_PRE_BACKFILL_GUARD_MESSAGE)
    return _run_in_git_repo_after_guard(ctx=ctx)


def _select_finding(
    *,
    ctx: DoctorContext,
    in_git_repo: bool,
) -> IOResult[Finding, LivespecError]:
    """Dispatch to the in-git-repo comparison or the not-in-git-repo skipped-Finding."""
    if in_git_repo:
        return _select_finding_in_git_repo(ctx=ctx)
    return _skipped(ctx=ctx, message=_NOT_IN_GIT_REPO_MESSAGE)


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the out-of-band-edits check against `ctx`.

    Composes `is_git_repo(project_root=ctx.spec_root)` with
    the in-git-repo dispatcher. Non-repo case yields
    IOSuccess(skipped-Finding). In-git-repo case runs the
    pre-backfill guard (cycle 7.a.iii); when the guard
    clears, runs HEAD-active-vs-HEAD-history-vN divergence
    detection (cycle 7.a.iv-redo). No-drift → pass-Finding;
    drift → fail-Finding listing every diverging basename.
    No-history-baseline → no-baseline pass-Finding.

    `ctx.spec_root` is passed to `is_git_repo` rather than
    `ctx.project_root` because `git rev-parse
    --is-inside-work-tree` resolves against any path inside
    the working tree — using `spec_root` lets the check work
    uniformly for the main spec tree AND each sub-spec tree.

    Pre-backfill-guard read paths (`Path.glob`, `Path.iterdir`,
    `Path.is_dir`) are stat-level scans whose OSError
    propagates as a bug per the io/-layer rule. Git seams
    (`is_git_repo`, `list_at_head`, `show_at_head`) lift their
    OSError + non-zero-exit failures to IOFailure at the
    io/git boundary.
    """
    return is_git_repo(project_root=ctx.spec_root).bind(
        lambda in_git_repo: _select_finding(ctx=ctx, in_git_repo=in_git_repo),
    )
