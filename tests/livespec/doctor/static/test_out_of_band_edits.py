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
