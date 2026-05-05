"""Tests for livespec.doctor.static.out_of_band_edits.

Per Plan Phase 7 sub-step 7.a + PROPOSAL.md §"`doctor` →
Static-phase checks": the `out-of-band-edits` check detects
HEAD-committed spec files whose contents have diverged from
their HEAD-committed `history/vN/` snapshot. It is the only
check whose `run()` has a narrow auto-backfill write path (per
`static/CLAUDE.md`); auto-backfill on detected drift lands in
sub-step 7.a.v. Cycle 7.a.iv (redo) lands ONLY the detection
half — no writes.

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
    git repo). Cycle 7.a.iv (redo) replaces this placeholder
    with real HEAD-active-vs-HEAD-history-vN divergence
    detection.

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

Cycle 7.a.iv (redo) replaces the placeholder pass-Finding with
HEAD-committed-active-vs-HEAD-committed-history-vN comparison
(PROPOSAL §"Static-phase checks → out-of-band-edits →
Comparison": "diffs `git show HEAD:<spec-root>/<spec-file>`
against `git show HEAD:<spec-root>/history/vN/<spec-file>` for
each top-level spec file. Both sides are HEAD-committed
artifacts; working-tree WIP is ignored for the comparison.").

The "template-declared spec files" enumeration is realized as
"the immediate top-level files at HEAD under `<spec-root>/`",
walked via `livespec.io.git.list_at_head`. Subdirs
(`history/`, `proposed_changes/`, `templates/`) are excluded
by ls-tree's blob-only filter, so the enumeration matches the
top-level *.md files the seed materializes.

Edge case decisions (PROPOSAL is silent; codified here):

  - No `<spec-root>/history/` at HEAD: emits `status="pass"`
    with a "no history baseline" message. This is a benign
    "post-seed pre-revise" state — there's nothing to compare
    against — and the pre-backfill guard already covers the
    leftover-from-prior-backfill cases that would otherwise
    land here.
  - `history/` at HEAD with no `vNNN/` subdirs (only
    `README.md` or similar): same as above. Without a vN to
    diff against, "no drift" is the correct outcome.

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
    _ = subprocess.run(
        ["git", "config", "--local", "user.email", "fixture@example.com"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    _ = subprocess.run(
        ["git", "config", "--local", "user.name", "Fixture User"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )


def _git_commit_paths(*, repo_root: Path, paths: list[Path], message: str = "fixture") -> None:
    """Stage `paths` (relative to repo_root) and commit them.

    Each path must already exist under `repo_root` with the
    desired content; this helper only stages + commits. Used
    to land HEAD-committed state for the divergence-detection
    fixtures so the comparison runs against real HEAD blobs.
    """
    relative_paths = [str(path.relative_to(repo_root)) for path in paths]
    _ = subprocess.run(
        ["git", "add", *relative_paths],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    _ = subprocess.run(
        ["git", "commit", "--quiet", "-m", message],
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


def _seed_clean_active_and_history(
    *,
    repo_root: Path,
    spec_root: Path,
    files: dict[str, bytes],
    version_label: str = "v001",
) -> None:
    """Seed `spec_root` with byte-identical active + history/`<vNNN>/` content.

    Used by clean-baseline tests: writes each file twice (once
    at `<spec_root>/<name>` and once at
    `<spec_root>/history/<vNNN>/<name>`) with the same bytes,
    then commits both. The HEAD-active and HEAD-history-vN
    blobs are byte-identical (same SHA), so the divergence
    check MUST emit a pass-Finding.
    """
    spec_root.mkdir(parents=True, exist_ok=True)
    history_v = spec_root / "history" / version_label
    history_v.mkdir(parents=True, exist_ok=True)
    paths_to_commit: list[Path] = []
    for name, content in files.items():
        active = spec_root / name
        _ = active.write_bytes(content)
        paths_to_commit.append(active)
        history_file = history_v / name
        _ = history_file.write_bytes(content)
        paths_to_commit.append(history_file)
    _git_commit_paths(repo_root=repo_root, paths=paths_to_commit, message="seed clean")


def _expected_pass_clean(*, spec_root: Path) -> Finding:
    """Construct the canonical pass-Finding for the no-drift case.

    Emitted when every HEAD-active spec file matches its
    HEAD-history-vN counterpart byte-for-byte. The message is
    pinned literally so cosmetic changes surface as test
    failures rather than silent semantic drift.
    """
    return Finding(
        check_id="doctor-out-of-band-edits",
        status="pass",
        message="no out-of-band edits detected (HEAD-active matches HEAD-history-vN)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )


def _expected_pass_no_history_baseline(*, spec_root: Path) -> Finding:
    """Construct the canonical pass-Finding for the no-history-baseline case.

    Emitted when `<spec-root>/history/` is absent at HEAD or
    contains no `vNNN/` subdirs at HEAD. Per the edge-case
    decision documented in the module docstring, "no baseline"
    is treated as "no drift" (PROPOSAL is silent on this
    case; the pre-backfill guard already covers the leftover
    cases that would otherwise land here).
    """
    return Finding(
        check_id="doctor-out-of-band-edits",
        status="pass",
        message="no HEAD history baseline; nothing to compare",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )


def test_run_returns_pass_when_active_and_history_match_byte_for_byte(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) returns IOSuccess(pass) when HEAD-active matches HEAD-history-vN.

    Canonical no-drift fixture: a top-level `spec.md` is
    committed at HEAD with byte-identical content at
    `<spec_root>/spec.md` and `<spec_root>/history/v001/spec.md`.
    Per PROPOSAL §"Static-phase checks → out-of-band-edits →
    Comparison" both sides are HEAD-committed artifacts; the
    byte-equality check MUST emit a pass-Finding.
    """
    monkeypatch.chdir(tmp_path)
    _git_init(repo_root=tmp_path)
    project_root = tmp_path
    spec_root = project_root / "SPECIFICATION"
    _seed_clean_active_and_history(
        repo_root=tmp_path,
        spec_root=spec_root,
        files={"spec.md": b"# Spec\n\nIdentical bytes.\n"},
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    assert out_of_band_edits.run(ctx=ctx) == IOSuccess(_expected_pass_clean(spec_root=spec_root))


def test_run_returns_fail_when_active_diverges_from_history(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) returns IOSuccess(fail) when active and history-vN bytes differ.

    Canonical drift fixture: `<spec_root>/spec.md` is
    committed at HEAD with content X; `<spec_root>/history/v001/
    spec.md` is committed at HEAD with content Y where Y != X.
    This represents an out-of-band edit landing on the
    HEAD-active spec without a paired revise step (the user
    edited spec.md and committed without running revise to
    snapshot the new state into history/v002/).

    The check MUST emit a fail-Finding naming the diverging
    file (so the auto-backfill in 7.a.v knows which file to
    snapshot).
    """
    monkeypatch.chdir(tmp_path)
    _git_init(repo_root=tmp_path)
    project_root = tmp_path
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history_v = spec_root / "history" / "v001"
    history_v.mkdir(parents=True)
    active = spec_root / "spec.md"
    _ = active.write_bytes(b"# Active\n\nNew text after OOB edit.\n")
    snapshot = history_v / "spec.md"
    _ = snapshot.write_bytes(b"# Active\n\nOriginal text.\n")
    _git_commit_paths(repo_root=tmp_path, paths=[active, snapshot])
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = out_of_band_edits.run(ctx=ctx)
    expected_message = "out-of-band edits detected at HEAD against history/v001: spec.md"
    expected = Finding(
        check_id="doctor-out-of-band-edits",
        status="fail",
        message=expected_message,
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_run_returns_fail_when_active_present_history_missing_at_head(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) returns IOSuccess(fail) when active is at HEAD but history-vN is not.

    Drift case: a NEW top-level spec file landed at HEAD-active
    without a paired snapshot at HEAD-history-vN (e.g., user
    added `extras.md` directly without revising). PROPOSAL's
    comparison says "diff active against history/vN/<file>";
    when the history side is absent at HEAD, the file IS
    drift — it was added since vN's snapshot was taken without
    a revise pass.
    """
    monkeypatch.chdir(tmp_path)
    _git_init(repo_root=tmp_path)
    project_root = tmp_path
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history_v = spec_root / "history" / "v001"
    history_v.mkdir(parents=True)
    active_paired = spec_root / "spec.md"
    _ = active_paired.write_bytes(b"# Spec\n")
    snapshot_paired = history_v / "spec.md"
    _ = snapshot_paired.write_bytes(b"# Spec\n")
    active_unpaired = spec_root / "extras.md"
    _ = active_unpaired.write_bytes(b"# Extras\nadded out-of-band\n")
    _git_commit_paths(
        repo_root=tmp_path,
        paths=[active_paired, snapshot_paired, active_unpaired],
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = out_of_band_edits.run(ctx=ctx)
    expected_message = "out-of-band edits detected at HEAD against history/v001: extras.md"
    expected = Finding(
        check_id="doctor-out-of-band-edits",
        status="fail",
        message=expected_message,
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_run_returns_fail_when_history_present_active_missing_at_head(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) returns IOSuccess(fail) when history-vN holds a file but active is missing.

    Drift case: HEAD-history/v001/ snapshot still carries
    `removed.md`, but HEAD-active no longer carries it (user
    deleted it directly without revising). The check MUST
    detect this asymmetric file-set as drift.
    """
    monkeypatch.chdir(tmp_path)
    _git_init(repo_root=tmp_path)
    project_root = tmp_path
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history_v = spec_root / "history" / "v001"
    history_v.mkdir(parents=True)
    active_paired = spec_root / "spec.md"
    _ = active_paired.write_bytes(b"# Spec\n")
    snapshot_paired = history_v / "spec.md"
    _ = snapshot_paired.write_bytes(b"# Spec\n")
    snapshot_unpaired = history_v / "removed.md"
    _ = snapshot_unpaired.write_bytes(b"# Removed since v001\n")
    _git_commit_paths(
        repo_root=tmp_path,
        paths=[active_paired, snapshot_paired, snapshot_unpaired],
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = out_of_band_edits.run(ctx=ctx)
    expected_message = "out-of-band edits detected at HEAD against history/v001: removed.md"
    expected = Finding(
        check_id="doctor-out-of-band-edits",
        status="fail",
        message=expected_message,
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_run_returns_fail_naming_all_diverging_files_sorted(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) returns IOSuccess(fail) listing every diverging file (sorted).

    Multi-divergence fixture: spec.md modified (bytes differ);
    extras.md added without a v001 snapshot; removed.md
    snapshotted at v001 but absent from active. The fail
    message MUST list all three files in sorted order so
    downstream auto-backfill (7.a.v) can deterministically
    iterate.
    """
    monkeypatch.chdir(tmp_path)
    _git_init(repo_root=tmp_path)
    project_root = tmp_path
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history_v = spec_root / "history" / "v001"
    history_v.mkdir(parents=True)
    active_modified = spec_root / "spec.md"
    _ = active_modified.write_bytes(b"# Spec ACTIVE\n")
    snapshot_modified = history_v / "spec.md"
    _ = snapshot_modified.write_bytes(b"# Spec ORIGINAL\n")
    active_extras = spec_root / "extras.md"
    _ = active_extras.write_bytes(b"# Extras\n")
    snapshot_removed = history_v / "removed.md"
    _ = snapshot_removed.write_bytes(b"# Removed\n")
    _git_commit_paths(
        repo_root=tmp_path,
        paths=[
            active_modified,
            active_extras,
            snapshot_modified,
            snapshot_removed,
        ],
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = out_of_band_edits.run(ctx=ctx)
    expected_message = (
        "out-of-band edits detected at HEAD against history/v001: " "extras.md, removed.md, spec.md"
    )
    expected = Finding(
        check_id="doctor-out-of-band-edits",
        status="fail",
        message=expected_message,
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_run_returns_fail_against_latest_version_when_multiple_versions_exist(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) compares against the LATEST `vNNN/` when several exist at HEAD.

    Fixture: HEAD carries `history/v001/spec.md` AND
    `history/v002/spec.md` (both with content matching v001's
    seed), plus a top-level `spec.md` differing from both.
    The comparison MUST select v002 (the highest committed
    version) as the comparison target, not v001 — and the
    fail message MUST name v002 specifically.
    """
    monkeypatch.chdir(tmp_path)
    _git_init(repo_root=tmp_path)
    project_root = tmp_path
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history_v001 = spec_root / "history" / "v001"
    history_v001.mkdir(parents=True)
    history_v002 = spec_root / "history" / "v002"
    history_v002.mkdir(parents=True)
    active = spec_root / "spec.md"
    _ = active.write_bytes(b"# Spec ACTIVE\n")
    snapshot_v001 = history_v001 / "spec.md"
    _ = snapshot_v001.write_bytes(b"# Spec ORIGINAL\n")
    snapshot_v002 = history_v002 / "spec.md"
    _ = snapshot_v002.write_bytes(b"# Spec V002\n")
    _git_commit_paths(
        repo_root=tmp_path,
        paths=[active, snapshot_v001, snapshot_v002],
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = out_of_band_edits.run(ctx=ctx)
    expected_message = "out-of-band edits detected at HEAD against history/v002: spec.md"
    expected = Finding(
        check_id="doctor-out-of-band-edits",
        status="fail",
        message=expected_message,
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_run_returns_pass_when_history_has_only_non_version_children(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) returns IOSuccess(pass) with no-history-baseline message when history/ has no vNNN/ at HEAD.

    Edge case codified in the module docstring: when
    `<spec_root>/history/` exists at HEAD but contains only
    non-vNNN children (a `README.md`, a `notes/` dir, a
    `vbeta/` dir whose suffix isn't numeric), there is no vN
    against which to compare. The check MUST emit a
    pass-Finding (no drift detectable). The pre-backfill
    guard already covers the leftover-from-prior-backfill
    cases that would otherwise need different handling here.
    """
    monkeypatch.chdir(tmp_path)
    _git_init(repo_root=tmp_path)
    project_root = tmp_path
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history = spec_root / "history"
    history.mkdir()
    readme = history / "README.md"
    _ = readme.write_text("# history dir description\n")
    notes_file = history / "notes" / "note.md"
    notes_file.parent.mkdir()
    _ = notes_file.write_text("# notes\n")
    vbeta_file = history / "vbeta" / "placeholder.md"
    vbeta_file.parent.mkdir()
    _ = vbeta_file.write_text("# vbeta placeholder\n")
    _git_commit_paths(
        repo_root=tmp_path,
        paths=[readme, notes_file, vbeta_file],
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = _expected_pass_no_history_baseline(spec_root=spec_root)
    assert out_of_band_edits.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_when_history_dir_is_absent_at_head(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) returns IOSuccess(pass) with no-history-baseline message when history/ is absent at HEAD.

    Edge case codified in the module docstring: when
    `<spec_root>/history/` does NOT exist at HEAD at all (the
    "post-seed pre-revise" state where the seed materialized
    top-level files but no v001 snapshot has been written
    yet via revise), there is no comparison target. The check
    MUST emit a pass-Finding (no drift detectable). The
    pre-backfill guard's condition B is also FALSE in this
    state (no `history/`), so this branch reaches the
    no-history-baseline pass.
    """
    monkeypatch.chdir(tmp_path)
    _git_init(repo_root=tmp_path)
    project_root = tmp_path
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    active = spec_root / "spec.md"
    _ = active.write_bytes(b"# Spec\n")
    _git_commit_paths(repo_root=tmp_path, paths=[active])
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = _expected_pass_no_history_baseline(spec_root=spec_root)
    assert out_of_band_edits.run(ctx=ctx) == IOSuccess(expected)
