"""Tests for livespec.doctor.static.out_of_band_edits.

Per Plan Phase 7 sub-step 7.a + PROPOSAL.md §"`doctor` →
Static-phase checks": the `out-of-band-edits` check detects
working-tree spec files whose contents have diverged from their
HEAD blob. It is the only check whose `run()` has a narrow
auto-backfill write path (per `static/CLAUDE.md`); divergence
detection + auto-backfill land in 7.a.iii / 7.a.iv.

Cycle 7.a.ii lands the skeleton + registry wiring + the first
two pinned behaviors:

  - When `ctx.spec_root` is NOT inside a git working tree, the
    check emits a skipped-Finding (`status="skipped"`). Non-git
    projects are an expected business outcome (PROPOSAL §"`doctor`":
    "skip the out-of-band check, the project isn't versioned");
    they MUST NOT lift to an IOFailure (memory:
    feedback_domain_errors_vs_bugs).

  - When `ctx.spec_root` IS inside a git working tree, the check
    emits a placeholder pass-Finding. Divergence detection lands
    in 7.a.iv; until then the placeholder keeps the aggregate
    `just check` gate green for the project itself (which IS a
    git repo).

The SLUG ↔ check_id literal mapping (`doctor-out-of-band-edits`)
is also pinned per the `static/CLAUDE.md` registry convention.

Cycle 7.a.iii widens the in-git-repo branch with a pre-backfill
guard, per PROPOSAL §"Static-phase checks" → out-of-band-edits
→ "Pre-backfill guard — uncommitted prior backfill present".
The guard detects two leftover-from-prior-run shapes BEFORE
running the divergence comparison (which lands in 7.a.iv) or
the auto-backfill write path (7.a.v):

  - Condition A: any
    `<spec-root>/proposed_changes/out-of-band-edit-*.md` file
    is already on disk (from a prior auto-backfill that the
    user did not commit).
  - Condition B: `<spec-root>/history/v(N+1)/` already exists,
    where N is the current highest-numbered version directory
    under `<spec-root>/history/`. If `<spec-root>/history/`
    itself does not exist, condition B is FALSE — there are
    no prior versions for any v(N+1) to claim. If `history/`
    exists but contains no `vNNN/` dirs (e.g., only README.md),
    N is 0 and condition B checks for `v001/`.

When either condition holds, the check emits a skipped-Finding
naming the manual-intervention requirement. The skipped-Finding
keeps the doctor non-destructive: it refuses to double-write a
fresh auto-backfill on top of an in-flight prior one (PROPOSAL
guard semantics — the user must commit-or-revert the prior
backfill before re-running). Per memory
feedback_domain_errors_vs_bugs the leftover state is an EXPECTED
business outcome, not a bug, so it stays on the IOSuccess track
with `status="skipped"` rather than lifting to IOFailure.

Per memory feedback_test_cwd_isolation, every git-fixture test
sets `monkeypatch.chdir(tmp_path)` so the surrounding livespec
repo's `.git/` directory cannot leak into the assertion target.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import out_of_band_edits
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def _git_init(*, repo_root: Path) -> None:
    """Initialize `repo_root` as a git working tree.

    The fixture-shared helper isolates `git init` from
    surrounding-shell state by passing `cwd=repo_root` and
    `check=True`. The init-only seed is sufficient for the
    `is_git_repo` discriminator: `git rev-parse --is-inside-
    work-tree` returns 0 in a freshly-initialized repo even
    before any commits land.
    """
    _ = subprocess.run(
        ["git", "init"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )


def test_run_returns_skipped_when_spec_root_is_not_in_git_repo(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) returns IOSuccess(skipped-Finding) when not in a git working tree.

    Non-git fixture: `tmp_path` is NOT initialized as a git
    repo. The check's first branch SHOULD detect this via
    `is_git_repo` and emit a skipped-Finding instead of
    attempting any divergence detection. Non-git is an
    expected business outcome — the doctor folds it into
    "skip the out-of-band check, the project isn't versioned"
    (PROPOSAL §"Static-phase checks").

    `monkeypatch.chdir(tmp_path)` isolates cwd per
    `feedback_test_cwd_isolation` so the `is_git_repo` check
    cannot accidentally walk up into the surrounding livespec
    repo's `.git/` directory.
    """
    monkeypatch.chdir(tmp_path)
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-out-of-band-edits",
        status="skipped",
        message="spec_root is not inside a git working tree",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert out_of_band_edits.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_placeholder_when_spec_root_is_in_git_repo(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) returns IOSuccess(pass-placeholder-Finding) inside a git working tree.

    Git-repo fixture: `tmp_path` is initialized as a git repo
    via `git init`. The check's second branch SHOULD detect
    this via `is_git_repo` and emit a placeholder pass-Finding
    (the divergence-detection logic itself lands in 7.a.iv;
    cycle 7.a.ii pins only the skeleton).

    `monkeypatch.chdir(tmp_path)` isolates cwd per
    `feedback_test_cwd_isolation`.
    """
    monkeypatch.chdir(tmp_path)
    _git_init(repo_root=tmp_path)
    project_root = tmp_path
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-out-of-band-edits",
        status="pass",
        message=(
            "no out-of-band edits detected (placeholder; divergence " "detection lands in 7.a.iv)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert out_of_band_edits.run(ctx=ctx) == IOSuccess(expected)


def test_slug_is_doctor_out_of_band_edits() -> None:
    """The module's `SLUG` constant is the canonical check_id.

    Pins the SLUG ↔ check_id mapping per the static/CLAUDE.md
    convention (slug `out-of-band-edits` ↔ module filename
    `out_of_band_edits.py` ↔ check_id
    `doctor-out-of-band-edits`).
    """
    assert out_of_band_edits.SLUG == "doctor-out-of-band-edits"


def _expected_pre_backfill_skipped(*, spec_root: Path) -> Finding:
    """Construct the canonical pre-backfill-guard skipped-Finding.

    The guard's skipped-Finding is shared across all four
    leftover-state fixture shapes (existing OOB proposed-change
    file with either a fresh-init repo or a history-tree repo;
    existing v(N+1) for N=0 or N=2). Building it via a single
    helper keeps the assertion target identical across the
    test cases and pins the literal message — the precise
    string lands as the message field per PROPOSAL §"`doctor`
    → out-of-band-edits → Pre-backfill guard".
    """
    return Finding(
        check_id="doctor-out-of-band-edits",
        status="skipped",
        message=(
            "auto-backfill artifact already present from prior run; manual intervention required"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )


def test_run_returns_skipped_when_existing_oob_proposed_change_file_present(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) returns IOSuccess(skipped-Finding) when an `out-of-band-edit-*.md` file is on disk.

    Condition A fixture: a freshly-initialized git repo whose
    `<spec_root>/proposed_changes/` directory carries one
    `out-of-band-edit-2026-05-05T06-15-00Z.md` file (a stand-in
    for an auto-backfill artifact left uncommitted by a prior
    `doctor` run). The check's pre-backfill guard MUST detect
    this leftover-from-prior-run state and refuse to proceed,
    emitting a skipped-Finding so the auto-backfill write path
    in 7.a.v never double-writes on top of the in-flight prior
    artifact.

    `monkeypatch.chdir(tmp_path)` isolates cwd per
    `feedback_test_cwd_isolation`.
    """
    monkeypatch.chdir(tmp_path)
    _git_init(repo_root=tmp_path)
    project_root = tmp_path
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    proposed_changes = spec_root / "proposed_changes"
    proposed_changes.mkdir()
    oob_file = proposed_changes / "out-of-band-edit-2026-05-05T06-15-00Z.md"
    _ = oob_file.write_text("# placeholder out-of-band-edit content\n")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = _expected_pre_backfill_skipped(spec_root=spec_root)
    assert out_of_band_edits.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_skipped_when_v001_already_exists_with_no_prior_versions(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) returns IOSuccess(skipped-Finding) when N=0 and v001/ already exists.

    Condition B fixture (N=0 case): `<spec_root>/history/`
    contains no `vNNN/` dirs at all (no prior versions exist),
    yet `<spec_root>/history/v001/` is on disk. Per the guard's
    "highest version" semantics, N=0 and v(N+1)=v001 — its
    presence indicates a prior auto-backfill claimed the v001
    slot but never committed. The check MUST detect this and
    emit a skipped-Finding.

    `monkeypatch.chdir(tmp_path)` isolates cwd per
    `feedback_test_cwd_isolation`.
    """
    monkeypatch.chdir(tmp_path)
    _git_init(repo_root=tmp_path)
    project_root = tmp_path
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history = spec_root / "history"
    history.mkdir()
    (history / "v001").mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = _expected_pre_backfill_skipped(spec_root=spec_root)
    assert out_of_band_edits.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_placeholder_when_history_has_only_non_version_children(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) falls through to pass when history/ has only non-vNNN/ entries.

    Condition B negative fixture: `<spec_root>/history/` is
    present but contains only entries the v-dir filter MUST
    skip — none of them are committed `vNNN/` snapshots and
    none of them is the v(N+1)=v001 leftover candidate:

      - `README.md` (a regular file, not a directory).
      - `notes/` (a directory whose name does not begin with
        `v` — exercises the `not name.startswith("v")` filter
        in `_parse_version_number`).
      - `vbeta/` (a directory whose name DOES begin with `v`
        but whose suffix is non-numeric — exercises the
        `not suffix.isdigit()` filter in
        `_parse_version_number`, which is critical because
        without it the integer parse would raise on a non-
        digit suffix and propagate as a bug).

    Per the guard's "highest version" semantics N=0
    (no parseable v-dirs); v(N+1)=v001 is NOT on disk;
    condition B is FALSE. Condition A is also FALSE (no
    proposed-change files at all). The check therefore
    advances to the placeholder pass branch landed in 7.a.ii.
    This pins the non-vNNN-children shape as a non-trigger so
    seeded-but-unrevised trees do not spuriously emit skipped.
    """
    monkeypatch.chdir(tmp_path)
    _git_init(repo_root=tmp_path)
    project_root = tmp_path
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history = spec_root / "history"
    history.mkdir()
    _ = (history / "README.md").write_text("# history dir description\n")
    (history / "notes").mkdir()
    (history / "vbeta").mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-out-of-band-edits",
        status="pass",
        message=(
            "no out-of-band edits detected (placeholder; divergence " "detection lands in 7.a.iv)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert out_of_band_edits.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_skipped_when_v003_exists_alongside_committed_v001_and_v002(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) returns IOSuccess(skipped-Finding) when N=2 + empty v003/ leads.

    Condition B fixture (mid-run state): `<spec_root>/history/`
    carries committed `v001/` + `v002/` snapshots (non-empty,
    each with at least one file standing in for the v-dir
    contents-required by `version-directories-complete`) plus
    an EMPTY `v003/` directory left over from a prior
    auto-backfill that claimed the next-version slot but did
    not commit. Per the guard's "highest version" semantics
    N=2 (v003 is empty so it does not count as a committed
    prior version) and v003=v(N+1) is on disk → trigger.

    The empty-v-dir-doesn't-count-as-prior-version rule keeps
    the guard non-circular: without it, max(set)=3 would
    yield N=3 and the guard would check v004 (which does not
    exist), missing the leftover v003. With it, max-of-
    non-empty=2 and the guard correctly checks v003.

    To avoid over-specifying the impl, this test pins only the
    INPUT/OUTPUT contract — three v-dirs on disk (v001 non-
    empty, v002 non-empty, v003 empty), no
    `out-of-band-edit-*.md` files, no other state — and
    asserts the skipped-Finding emerges.
    """
    monkeypatch.chdir(tmp_path)
    _git_init(repo_root=tmp_path)
    project_root = tmp_path
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history = spec_root / "history"
    history.mkdir()
    v001 = history / "v001"
    v001.mkdir()
    _ = (v001 / "spec.md").write_text("# v001 spec\n")
    v002 = history / "v002"
    v002.mkdir()
    _ = (v002 / "spec.md").write_text("# v002 spec\n")
    (history / "v003").mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = _expected_pre_backfill_skipped(spec_root=spec_root)
    assert out_of_band_edits.run(ctx=ctx) == IOSuccess(expected)
