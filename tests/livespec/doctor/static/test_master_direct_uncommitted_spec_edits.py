"""Tests for livespec.doctor.static.master_direct_uncommitted_spec_edits.

Per `SPECIFICATION/contracts.md` →: every
worktree (primary or secondary, per `git worktree list
--porcelain`) whose HEAD points at the default branch MUST NOT
carry uncommitted modifications under `<spec-root>/`. The check
fires `warn` (not `fail`) per the v079 prose at
`non-functional-requirements.md:746`.

Acceptance scenarios (mirrored verbatim from the work-item
description):

(a) Primary worktree HEAD on `master`, no spec-tree
    modifications `pass`.
(b) Primary worktree HEAD on `master`, one modified file under
    `<spec-root>/` `warn` naming the worktree + file.
(c) Primary worktree HEAD on a feature branch, modifications
    under `<spec-root>/` `pass` (HEAD not default branch).
(d) Secondary worktree HEAD on `master` (created via
    `git worktree add --force <path> master`), with spec-tree
    mods `warn`. Bypass case
    primary-checkout-commit-refuse-hook-installed cannot prevent.
(e) Multiple worktrees all on master, mixed state one `warn`
    finding summarizing every non-empty-status worktree.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import master_direct_uncommitted_spec_edits
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def _git_init_with_user(*, cwd: Path, name: str, email: str) -> None:
    """Initialize a git repo at `cwd` with local user.name/user.email set."""
    _ = subprocess.run(["git", "init", "--quiet"], cwd=cwd, check=True)
    _ = subprocess.run(
        ["git", "config", "--local", "user.name", name],
        cwd=cwd,
        check=True,
    )
    _ = subprocess.run(
        ["git", "config", "--local", "user.email", email],
        cwd=cwd,
        check=True,
    )


def _git_commit_file(*, cwd: Path, path: Path, content: bytes) -> None:
    """Write `content` to `path` and commit it."""
    _ = path.write_bytes(content)
    _ = subprocess.run(
        ["git", "add", str(path.relative_to(cwd))],
        cwd=cwd,
        check=True,
    )
    _ = subprocess.run(
        ["git", "commit", "--quiet", "-m", "fixture commit"],
        cwd=cwd,
        check=True,
    )


def _git_set_origin_head(*, cwd: Path, default_branch: str) -> None:
    """Stage a fake `origin` remote + set `origin/HEAD` to point at `default_branch`."""
    _ = subprocess.run(
        ["git", "remote", "add", "origin", str(cwd)],
        cwd=cwd,
        check=True,
    )
    _ = subprocess.run(
        ["git", "update-ref", f"refs/remotes/origin/{default_branch}", "HEAD"],
        cwd=cwd,
        check=True,
    )
    _ = subprocess.run(
        [
            "git",
            "symbolic-ref",
            "refs/remotes/origin/HEAD",
            f"refs/remotes/origin/{default_branch}",
        ],
        cwd=cwd,
        check=True,
    )


def _current_branch(*, cwd: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _seed_spec_root(*, project_root: Path) -> Path:
    """Create `<project_root>/SPECIFICATION/spec.md` and stage+commit it."""
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _git_commit_file(
        cwd=project_root,
        path=spec_root / "spec.md",
        content=b"# Spec\n",
    )
    return spec_root


def test_master_direct_uncommitted_spec_edits_passes_when_primary_on_master_clean(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """(a) `pass` when primary worktree HEAD is on master with no spec-tree mods."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    spec_root = _seed_spec_root(project_root=project_root)
    default_branch = _current_branch(cwd=project_root)
    _git_set_origin_head(cwd=project_root, default_branch=default_branch)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = master_direct_uncommitted_spec_edits.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-master-direct-uncommitted-spec-edits",
        status="pass",
        message=(
            f"master-direct-uncommitted-spec-edits: no worktrees on "
            f"`{default_branch}` carry uncommitted spec-tree or `plan/` edits "
            f"(1 worktree(s) on `{default_branch}` scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_master_direct_uncommitted_spec_edits_warns_when_primary_on_master_modified(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """(b) `warn` when primary on master has one modified file under <spec-root>/."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    spec_root = _seed_spec_root(project_root=project_root)
    default_branch = _current_branch(cwd=project_root)
    _git_set_origin_head(cwd=project_root, default_branch=default_branch)
    _ = (spec_root / "spec.md").write_bytes(b"# Spec\nmodified\n")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = master_direct_uncommitted_spec_edits.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-master-direct-uncommitted-spec-edits",
        status="warn",
        message=(
            f"master-direct-uncommitted-spec-edits: 1 worktree(s) on "
            f"`{default_branch}` carry uncommitted spec-tree or `plan/` edits: "
            f"{project_root}: spec: SPECIFICATION/spec.md. Corrective action: "
            f"move the edits to a feature branch and commit them there. "
            f"Unintentional `<spec-root>/` edits MAY instead be discarded "
            f"(`git checkout -- <files>`)."
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_master_direct_uncommitted_spec_edits_passes_when_primary_on_feature_branch(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """(c) `pass` when primary on a feature branch (HEAD not default branch)."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    spec_root = _seed_spec_root(project_root=project_root)
    default_branch = _current_branch(cwd=project_root)
    _git_set_origin_head(cwd=project_root, default_branch=default_branch)
    _ = subprocess.run(
        ["git", "checkout", "--quiet", "-b", "feature/work"],
        cwd=project_root,
        check=True,
    )
    _ = (spec_root / "spec.md").write_bytes(b"# Spec\nmodified-on-feature\n")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = master_direct_uncommitted_spec_edits.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-master-direct-uncommitted-spec-edits",
        status="pass",
        message=(
            f"master-direct-uncommitted-spec-edits: no worktrees on "
            f"`{default_branch}` carry uncommitted spec-tree or `plan/` edits "
            f"(0 worktree(s) on `{default_branch}` scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_master_direct_uncommitted_spec_edits_warns_when_secondary_on_master_modified(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """(d) `warn` when a secondary worktree is on master with spec-tree mods.

    Primary checks out a feature branch so the secondary worktree
    can take master via `git worktree add --force`. The check MUST
    flag the secondary worktree on master even though the primary
    is clean — this is the bypass case the
    `primary-checkout-commit-refuse-hook-installed` invariant
    cannot prevent.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    spec_root = _seed_spec_root(project_root=project_root)
    default_branch = _current_branch(cwd=project_root)
    _git_set_origin_head(cwd=project_root, default_branch=default_branch)
    _ = subprocess.run(
        ["git", "checkout", "--quiet", "-b", "feature/primary-elsewhere"],
        cwd=project_root,
        check=True,
    )
    wt_path = tmp_path / "wt-master"
    _ = subprocess.run(
        ["git", "worktree", "add", "--force", str(wt_path), default_branch],
        cwd=project_root,
        check=True,
    )
    secondary_spec_file = wt_path / "SPECIFICATION" / "spec.md"
    _ = secondary_spec_file.write_bytes(b"# Spec\nedited-on-secondary\n")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = master_direct_uncommitted_spec_edits.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-master-direct-uncommitted-spec-edits",
        status="warn",
        message=(
            f"master-direct-uncommitted-spec-edits: 1 worktree(s) on "
            f"`{default_branch}` carry uncommitted spec-tree or `plan/` edits: "
            f"{wt_path}: spec: SPECIFICATION/spec.md. Corrective action: "
            f"move the edits to a feature branch and commit them there. "
            f"Unintentional `<spec-root>/` edits MAY instead be discarded "
            f"(`git checkout -- <files>`)."
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_master_direct_uncommitted_spec_edits_warns_per_violating_worktree_on_master(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """(e) Multiple worktrees all on master, mixed state → one `warn` per violator.

    Fixture: primary on master (modified), one secondary on
    master (modified), one secondary on master (clean). The
    check must name both violators and omit the clean one.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    spec_root = _seed_spec_root(project_root=project_root)
    default_branch = _current_branch(cwd=project_root)
    _git_set_origin_head(cwd=project_root, default_branch=default_branch)
    _ = (spec_root / "spec.md").write_bytes(b"# Spec\nedited-on-primary\n")
    wt_dirty_path = tmp_path / "wt-master-dirty"
    _ = subprocess.run(
        ["git", "worktree", "add", "--force", str(wt_dirty_path), default_branch],
        cwd=project_root,
        check=True,
    )
    _ = (wt_dirty_path / "SPECIFICATION" / "spec.md").write_bytes(
        b"# Spec\nedited-on-secondary-dirty\n",
    )
    wt_clean_path = tmp_path / "wt-master-clean"
    _ = subprocess.run(
        ["git", "worktree", "add", "--force", str(wt_clean_path), default_branch],
        cwd=project_root,
        check=True,
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = master_direct_uncommitted_spec_edits.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-master-direct-uncommitted-spec-edits",
        status="warn",
        message=(
            f"master-direct-uncommitted-spec-edits: 2 worktree(s) on "
            f"`{default_branch}` carry uncommitted spec-tree or `plan/` edits: "
            f"{project_root}: spec: SPECIFICATION/spec.md; "
            f"{wt_dirty_path}: spec: SPECIFICATION/spec.md. Corrective action: "
            f"move the edits to a feature branch and commit them there. "
            f"Unintentional `<spec-root>/` edits MAY instead be discarded "
            f"(`git checkout -- <files>`)."
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_master_direct_uncommitted_spec_edits_skipped_when_not_a_git_repo(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`skipped` when `project_root` is not a git working tree."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    monkeypatch.chdir(project_root)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = master_direct_uncommitted_spec_edits.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-master-direct-uncommitted-spec-edits",
        status="skipped",
        message=(
            "master-direct-uncommitted-spec-edits: project_root is not a "
            "git working tree; check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_master_direct_uncommitted_spec_edits_warns_on_a_dirty_plan_file(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`warn` when a default-branch worktree carries an uncommitted `plan/` file.

    Spec v170 widened the invariant from `<spec-root>/` to
    `<spec-root>/` OR `plan/`. Before the widening this exact
    state reported `pass`: on 2026-07-19 the first
    `check-doctor-static` run of a session reported "no worktrees
    on master carry uncommitted spec-tree edits (1 worktree(s) on
    master scanned)" while that very worktree held a plan handoff
    carrying 153 unversioned lines.

    Note the corrective action carries NO discard suggestion here
    — see the sibling test for why that is contract, not style.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    spec_root = _seed_spec_root(project_root=project_root)
    default_branch = _current_branch(cwd=project_root)
    _git_set_origin_head(cwd=project_root, default_branch=default_branch)
    plan_dir = project_root / "plan" / "some-topic"
    plan_dir.mkdir(parents=True)
    _git_commit_file(
        cwd=project_root,
        path=plan_dir / "handoff.md",
        content=b"# Handoff\n",
    )
    _ = (plan_dir / "handoff.md").write_bytes(b"# Handoff\nunversioned findings\n")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = master_direct_uncommitted_spec_edits.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-master-direct-uncommitted-spec-edits",
        status="warn",
        message=(
            f"master-direct-uncommitted-spec-edits: 1 worktree(s) on "
            f"`{default_branch}` carry uncommitted spec-tree or `plan/` edits: "
            f"{project_root}: plan: plan/some-topic/handoff.md. "
            f"Corrective action: move the edits to a feature branch and commit "
            f"them there. NEVER discard `plan/` edits: an uncommitted handoff "
            f"is frequently the only copy of a planning thread."
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_master_direct_uncommitted_spec_edits_never_offers_discard_for_plan_paths(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The `plan/` narration MUST NOT present discard as a symmetric option.

    `SPECIFICATION/contracts.md`
    §`master-direct-uncommitted-spec-edits` item 3: for
    `<spec-root>/` paths the narration MAY additionally offer
    discarding unintentional edits; "For `plan/` paths it MUST
    NOT: a plan-thread handoff is the durable record of a
    planning thread and an uncommitted one is frequently the ONLY
    copy, so a discard suggestion against it risks destroying the
    very artifact the finding exists to protect."

    This is the acceptance criterion most likely to be lost in a
    refactor, because the natural implementation has ONE narration
    string. Both classes dirty at once is the case that would
    silently reintroduce a discard suggestion covering `plan/`.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    _git_init_with_user(cwd=project_root, name="Test User", email="test@example.com")
    monkeypatch.chdir(project_root)
    spec_root = _seed_spec_root(project_root=project_root)
    default_branch = _current_branch(cwd=project_root)
    _git_set_origin_head(cwd=project_root, default_branch=default_branch)
    plan_dir = project_root / "plan" / "some-topic"
    plan_dir.mkdir(parents=True)
    _git_commit_file(
        cwd=project_root,
        path=plan_dir / "handoff.md",
        content=b"# Handoff\n",
    )
    _ = (spec_root / "spec.md").write_bytes(b"# Spec\nedited\n")
    _ = (plan_dir / "handoff.md").write_bytes(b"# Handoff\nedited\n")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = master_direct_uncommitted_spec_edits.run(ctx=ctx)
    finding = result.unwrap()._inner_value  # noqa: SLF001 — IOSuccess unwrap in test
    message = finding.message

    # Both classes are named, each under its own label.
    assert "spec: SPECIFICATION/spec.md" in message
    assert "plan: plan/some-topic/handoff.md" in message
    # The discard offer is present, and SCOPED to <spec-root>/ — never bare.
    assert "Unintentional `<spec-root>/` edits MAY instead be discarded" in message
    # The plan/ prohibition rides along whenever a plan/ path is implicated.
    assert "NEVER discard `plan/` edits" in message
