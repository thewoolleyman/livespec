"""Static-phase doctor check: out_of_band_edits.

Per Plan Phase 7 sub-step 7.a + PROPOSAL.md §"`doctor` →
Static-phase checks": the `out-of-band-edits` check detects
working-tree spec files whose contents have diverged from their
HEAD blob (i.e., edits made directly to the working tree without
the propose-change → revise pipeline). It is the only doctor
check whose `run()` has a narrow auto-backfill write path (per
`static/CLAUDE.md`); divergence detection + auto-backfill land
in cycles 7.a.iv / 7.a.v.

Cycle 7.a.ii landed the smallest viable skeleton: it discriminates
on whether `ctx.spec_root` is inside a git working tree.

Cycle 7.a.iii widens the in-git-repo branch with a pre-backfill
guard. Per PROPOSAL §"Static-phase checks → out-of-band-edits →
Pre-backfill guard — uncommitted prior backfill present", the
guard fires on either of two leftover-from-prior-run shapes
BEFORE the divergence comparison (lands in 7.a.iv) or the
auto-backfill write path (lands in 7.a.v):

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
the IOSuccess track. Firing the guard in 7.a.iii (before the
write path lands in 7.a.v) is forward-compatible: once
divergence detection lands, the guard prevents double-writing
on top of an in-flight prior auto-backfill.

The non-git case still emits a skipped-Finding with a
distinct message (PROPOSAL §"Static-phase checks": "skip the
out-of-band check, the project isn't versioned"). The clean
in-git-repo case (no leftover state) still emits the
placeholder pass-Finding from 7.a.ii — divergence detection
replaces it in 7.a.iv.

Per v018 Q1: applies to all spec-text-bearing trees (main +
each sub-spec).
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io.git import is_git_repo
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "doctor-out-of-band-edits"

# Cycle 7.a.iii pre-backfill guard literals. The OOB proposed-change
# filename prefix matches the auto-backfill artifact form documented
# in PROPOSAL §"Filename forms" — `out-of-band-edit-<UTC-seconds>.md`.
# The version-dir-name pattern mirrors `version_directories_complete.
# _select_version_dirs`'s `v*` + `is_dir()` + numeric-suffix filter so
# both checks share one literal definition of "what counts as a v-dir".
_OOB_PROPOSED_CHANGE_GLOB: str = "out-of-band-edit-*.md"
_VERSION_DIR_PREFIX: str = "v"


def _skipped_finding_not_in_git_repo(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical skipped-status Finding for the not-in-git-repo case.

    Emitted when `ctx.spec_root` is not inside a git working
    tree. The non-versioned outcome is expected (PROPOSAL
    §"Static-phase checks": "skip the out-of-band check, the
    project isn't versioned") so it stays on the success rail
    with `status="skipped"`.
    """
    return Finding(
        check_id=SLUG,
        status="skipped",
        message="spec_root is not inside a git working tree",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _skipped_finding_pre_backfill_guard(*, ctx: DoctorContext) -> Finding:
    """Construct the pre-backfill-guard skipped-Finding.

    Emitted when either condition A (existing
    `out-of-band-edit-*.md` proposed-change file) or condition
    B (existing `history/v(N+1)/` leftover) holds. The guard
    keeps the doctor non-destructive: it refuses to double-
    write a fresh auto-backfill on top of an in-flight prior
    one. The message names the manual-intervention requirement
    so the operator knows to commit-or-revert the prior
    artifact before re-running.
    """
    return Finding(
        check_id=SLUG,
        status="skipped",
        message=(
            "auto-backfill artifact already present from prior run; " "manual intervention required"
        ),
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the placeholder pass-status Finding for this check.

    Cycle 7.a.ii placeholder reached only when both pre-
    backfill-guard conditions are FALSE (no leftover OOB
    proposed-change file and no leftover v(N+1) dir). Keeps
    the aggregate `just check` gate green for clean git-
    versioned projects until 7.a.iv replaces this with real
    divergence detection.
    """
    return Finding(
        check_id=SLUG,
        status="pass",
        message=(
            "no out-of-band edits detected (placeholder; divergence " "detection lands in 7.a.iv)"
        ),
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _has_oob_proposed_change_file(*, spec_root: Path) -> bool:
    """Return True iff condition A is satisfied.

    Condition A: at least one
    `<spec_root>/proposed_changes/out-of-band-edit-*.md` file
    is on disk. Reads the proposed_changes/ directory directly
    via `Path.glob` — the same direct-Path-read pattern
    `version_directories_complete._classify_version_dir` uses
    for read-only stat-level scans. If `proposed_changes/`
    does not exist, the glob is empty and the function
    returns False (no leftover artifact).
    """
    proposed_changes = spec_root / "proposed_changes"
    if not proposed_changes.is_dir():
        return False
    return any(proposed_changes.glob(_OOB_PROPOSED_CHANGE_GLOB))


def _parse_version_number(*, version_path: Path) -> int | None:
    """Parse the integer suffix from a `vNNN` directory name.

    Returns the parsed integer for names matching the
    `v<digits>` shape; returns None for non-matching names so
    the caller can filter them out. Mirrors the canonical
    v-dir filter pattern in
    `version_directories_complete._select_version_dirs`
    (which combines a `name.startswith("v")` + `is_dir()`
    test); this helper additionally requires the suffix to
    be numeric so `v(N+1)` arithmetic stays well-defined.
    """
    name = version_path.name
    if not name.startswith(_VERSION_DIR_PREFIX):
        return None
    suffix = name[len(_VERSION_DIR_PREFIX) :]
    if not suffix.isdigit():
        return None
    return int(suffix)


def _is_empty_dir(*, dir_path: Path) -> bool:
    """Return True iff `dir_path` is a directory with zero entries.

    Used to discriminate "committed prior version" v-dirs
    (have content) from "leftover-from-prior-backfill" v-dirs
    (empty). Empty v-dirs do not count toward the highest-N
    computation because they ARE the v(N+1) leftover candidate
    the guard is detecting.
    """
    return not any(dir_path.iterdir())


def _has_leading_empty_version_dir(*, spec_root: Path) -> bool:
    """Return True iff condition B is satisfied.

    Condition B: `<spec_root>/history/v(N+1)/` is on disk,
    where N is the max version-number among committed (non-
    empty) v-dirs under `<spec_root>/history/`. With no
    v-dirs at all, N=0 and the guard checks v001. Algorithm:

      1. If `<spec_root>/history/` does not exist, return
         False (no prior versions for v(N+1) to claim).
      2. Walk every direct child of `history/`. Filter to
         dirs whose name parses as `v<digits>`.
      3. Compute N = max number among the NON-EMPTY parsed
         v-dirs (default 0). Empty v-dirs do not count —
         they are the v(N+1) candidates the guard detects.
      4. Return whether `history/v(N+1):03d/` is on disk via
         `Path.is_dir()`.

    The empty/non-empty discriminator keeps the guard non-
    circular: without it, an empty v(N+1) would inflate N to
    N+1 and the guard would check v(N+2) (which is not
    present), missing the leftover. With it, the leftover
    v(N+1) sits outside the max computation and is detected.
    """
    history = spec_root / "history"
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
    candidate = history / f"v{highest_committed + 1:03d}"
    return candidate.is_dir()


def _select_finding_in_git_repo(*, ctx: DoctorContext) -> Finding:
    """Select the in-git-repo Finding via the pre-backfill guard.

    Pure helper: probes the working tree for either condition
    A (existing `out-of-band-edit-*.md` proposed-change file)
    or condition B (existing `history/v(N+1)/` leftover). If
    either holds, emits the pre-backfill-guard skipped-
    Finding; otherwise falls through to the placeholder pass
    branch from 7.a.ii. The `is_git_repo` check has already
    confirmed `ctx.spec_root` is inside a git working tree
    by the time this helper runs.
    """
    if _has_oob_proposed_change_file(spec_root=ctx.spec_root):
        return _skipped_finding_pre_backfill_guard(ctx=ctx)
    if _has_leading_empty_version_dir(spec_root=ctx.spec_root):
        return _skipped_finding_pre_backfill_guard(ctx=ctx)
    return _pass_finding(ctx=ctx)


def _select_finding(*, ctx: DoctorContext, in_git_repo: bool) -> Finding:
    """Select the skipped- or pass-Finding based on the git-repo discriminator.

    Pure helper: receives the `is_git_repo` boolean (already
    unwrapped from the IO track by the caller's `.map`) and
    dispatches to the appropriate Finding-selector. The non-
    git case yields the not-in-git-repo skipped-Finding; the
    in-git-repo case delegates to the pre-backfill-guard
    selector landed in cycle 7.a.iii.
    """
    if in_git_repo:
        return _select_finding_in_git_repo(ctx=ctx)
    return _skipped_finding_not_in_git_repo(ctx=ctx)


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the out-of-band-edits check against `ctx`.

    Composes `is_git_repo(project_root=ctx.spec_root)` with a
    pure finding-selector. The non-repo case yields
    IOSuccess(Finding(status="skipped")). The in-git-repo
    case runs the pre-backfill guard (cycle 7.a.iii); when
    neither condition A (`out-of-band-edit-*.md` present) nor
    condition B (`history/v(N+1)/` present) holds, falls
    through to the placeholder pass-Finding (replaced by
    real divergence detection in 7.a.iv).

    `ctx.spec_root` is passed to `is_git_repo` rather than
    `ctx.project_root` because `git rev-parse
    --is-inside-work-tree` resolves against any path inside
    the working tree — using `spec_root` lets the check work
    uniformly for the main spec tree AND each sub-spec tree
    (the sub-spec tree's `spec_root` may be a subdirectory
    of the main tree but is still inside the same git repo).

    The pre-backfill-guard read paths (`Path.glob`,
    `Path.iterdir`, `Path.is_dir`) are stat-level scans with
    no recoverable failure modes within this check's scope;
    OSError from those propagates as a bug per the io/-layer
    rule. The only railway-failing source remains
    `is_git_repo`'s underlying `run_subprocess` (e.g., the
    `git` binary missing entirely).
    """
    return is_git_repo(project_root=ctx.spec_root).map(
        lambda in_git_repo: _select_finding(ctx=ctx, in_git_repo=in_git_repo),
    )
