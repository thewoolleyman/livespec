"""Tests for livespec.doctor.static.accept_decision_snapshot_consistency.

Per `SPECIFICATION/spec.md` §"Sub-command lifecycle": for every
`history/vNNN/<stem>-revision.md` with decision in {accept,
modify} and a non-empty `## Resulting Changes` section, every
listed file MUST differ byte-for-byte between vNNN/ and
v(NNN-1)/. Byte-identical pairs indicate a silent
resulting_files[] write failure.
"""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import accept_decision_snapshot_consistency
from livespec.schemas.dataclasses.finding import Finding
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def _make_ctx(*, tmp_path: Path) -> DoctorContext:
    """Construct a DoctorContext with a populated spec_root and history/ dir."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    (spec_root / "history").mkdir()
    return DoctorContext(project_root=project_root, spec_root=spec_root)


def _write_revision(
    *,
    version_dir: Path,
    stem: str,
    decision: str,
    resulting_files: list[str],
) -> Path:
    """Write a `<stem>-revision.md` file with front-matter and Resulting Changes."""
    proposed_changes = version_dir / "proposed_changes"
    proposed_changes.mkdir(parents=True, exist_ok=True)
    body_lines = ["---", f"decision: {decision}", "---", "", "## Resulting Changes", ""]
    if resulting_files:
        body_lines.extend(f"- {p}" for p in resulting_files)
    else:
        body_lines.append("(none)")
    body_lines.append("")
    revision_path = proposed_changes / f"{stem}-revision.md"
    _ = revision_path.write_text("\n".join(body_lines), encoding="utf-8")
    return revision_path


def _run_and_unwrap(*, ctx: DoctorContext) -> Finding:
    """Helper: run the check and unwrap the IOResult to a Finding."""
    return unsafe_perform_io(accept_decision_snapshot_consistency.run(ctx=ctx)).unwrap()


def test_run_returns_pass_for_well_formed_history(
    *,
    tmp_path: Path,
) -> None:
    """An accept revision with byte-different snapshots passes the check."""
    ctx = _make_ctx(tmp_path=tmp_path)
    v001 = ctx.spec_root / "history" / "v001"
    v002 = ctx.spec_root / "history" / "v002"
    v001.mkdir()
    v002.mkdir()
    _ = (v001 / "spec.md").write_text("v001 content", encoding="utf-8")
    _ = (v002 / "spec.md").write_text("v002 different content", encoding="utf-8")
    _ = _write_revision(
        version_dir=v002,
        stem="topic",
        decision="accept",
        resulting_files=["spec.md"],
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_returns_fail_for_byte_identical_snapshot(
    *,
    tmp_path: Path,
) -> None:
    """An accept revision with byte-identical snapshots fails the check."""
    ctx = _make_ctx(tmp_path=tmp_path)
    v001 = ctx.spec_root / "history" / "v001"
    v002 = ctx.spec_root / "history" / "v002"
    v001.mkdir()
    v002.mkdir()
    _ = (v001 / "spec.md").write_text("identical", encoding="utf-8")
    _ = (v002 / "spec.md").write_text("identical", encoding="utf-8")
    _ = _write_revision(
        version_dir=v002,
        stem="topic",
        decision="accept",
        resulting_files=["spec.md"],
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "fail"
    assert "byte-identical" in finding.message
    assert "spec.md" in finding.message


def test_run_returns_fail_for_modify_decision_byte_identical(
    *,
    tmp_path: Path,
) -> None:
    """A modify revision (not just accept) with byte-identical snapshots fails."""
    ctx = _make_ctx(tmp_path=tmp_path)
    v001 = ctx.spec_root / "history" / "v001"
    v002 = ctx.spec_root / "history" / "v002"
    v001.mkdir()
    v002.mkdir()
    _ = (v001 / "spec.md").write_text("same", encoding="utf-8")
    _ = (v002 / "spec.md").write_text("same", encoding="utf-8")
    _ = _write_revision(
        version_dir=v002,
        stem="topic",
        decision="modify",
        resulting_files=["spec.md"],
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "fail"


def test_run_returns_pass_for_pruned_marker_version(
    *,
    tmp_path: Path,
) -> None:
    """A vNNN with PRUNED_HISTORY.json is exempt from the check."""
    ctx = _make_ctx(tmp_path=tmp_path)
    v001 = ctx.spec_root / "history" / "v001"
    v002 = ctx.spec_root / "history" / "v002"
    v001.mkdir()
    v002.mkdir()
    _ = (v002 / "PRUNED_HISTORY.json").write_text("{}", encoding="utf-8")
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_returns_pass_for_reject_revision(
    *,
    tmp_path: Path,
) -> None:
    """A reject revision is skipped even with byte-identical snapshots."""
    ctx = _make_ctx(tmp_path=tmp_path)
    v001 = ctx.spec_root / "history" / "v001"
    v002 = ctx.spec_root / "history" / "v002"
    v001.mkdir()
    v002.mkdir()
    _ = (v001 / "spec.md").write_text("same", encoding="utf-8")
    _ = (v002 / "spec.md").write_text("same", encoding="utf-8")
    _ = _write_revision(
        version_dir=v002,
        stem="topic",
        decision="reject",
        resulting_files=[],
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_returns_pass_for_none_resulting_changes(
    *,
    tmp_path: Path,
) -> None:
    """An accept revision with `(none)` placeholder skips the byte-check."""
    ctx = _make_ctx(tmp_path=tmp_path)
    v001 = ctx.spec_root / "history" / "v001"
    v002 = ctx.spec_root / "history" / "v002"
    v001.mkdir()
    v002.mkdir()
    _ = (v001 / "spec.md").write_text("same", encoding="utf-8")
    _ = (v002 / "spec.md").write_text("same", encoding="utf-8")
    _ = _write_revision(
        version_dir=v002,
        stem="topic",
        decision="accept",
        resulting_files=[],
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_returns_pass_when_listed_file_missing_in_current(
    *,
    tmp_path: Path,
) -> None:
    """A listed file missing in the current version is skipped."""
    ctx = _make_ctx(tmp_path=tmp_path)
    v001 = ctx.spec_root / "history" / "v001"
    v002 = ctx.spec_root / "history" / "v002"
    v001.mkdir()
    v002.mkdir()
    _ = (v001 / "missing.md").write_text("a", encoding="utf-8")
    _ = _write_revision(
        version_dir=v002,
        stem="topic",
        decision="accept",
        resulting_files=["missing.md"],
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_returns_pass_when_listed_file_missing_in_prior(
    *,
    tmp_path: Path,
) -> None:
    """A listed file missing in the prior version is skipped."""
    ctx = _make_ctx(tmp_path=tmp_path)
    v001 = ctx.spec_root / "history" / "v001"
    v002 = ctx.spec_root / "history" / "v002"
    v001.mkdir()
    v002.mkdir()
    _ = (v002 / "added.md").write_text("a", encoding="utf-8")
    _ = _write_revision(
        version_dir=v002,
        stem="topic",
        decision="accept",
        resulting_files=["added.md"],
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_returns_pass_for_v001_only(
    *,
    tmp_path: Path,
) -> None:
    """When only v001 exists (N < 2), the check has nothing to compare."""
    ctx = _make_ctx(tmp_path=tmp_path)
    (ctx.spec_root / "history" / "v001").mkdir()
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_returns_pass_when_prior_version_missing(
    *,
    tmp_path: Path,
) -> None:
    """v002 with no v001 (history gap) skips the comparison."""
    ctx = _make_ctx(tmp_path=tmp_path)
    v002 = ctx.spec_root / "history" / "v002"
    v002.mkdir()
    _ = _write_revision(
        version_dir=v002,
        stem="topic",
        decision="accept",
        resulting_files=["spec.md"],
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_handles_resulting_changes_as_last_section(
    *,
    tmp_path: Path,
) -> None:
    """The Resulting Changes section bounded by EOF (no following heading)."""
    ctx = _make_ctx(tmp_path=tmp_path)
    v001 = ctx.spec_root / "history" / "v001"
    v002 = ctx.spec_root / "history" / "v002"
    v001.mkdir()
    v002.mkdir()
    _ = (v001 / "spec.md").write_text("a", encoding="utf-8")
    _ = (v002 / "spec.md").write_text("b", encoding="utf-8")
    proposed_changes = v002 / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "topic-revision.md").write_text(
        "---\ndecision: accept\n---\n\n## Resulting Changes\n\n- spec.md\n",
        encoding="utf-8",
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_handles_revision_with_no_resulting_changes_section(
    *,
    tmp_path: Path,
) -> None:
    """A revision missing the `## Resulting Changes` heading is skipped."""
    ctx = _make_ctx(tmp_path=tmp_path)
    v001 = ctx.spec_root / "history" / "v001"
    v002 = ctx.spec_root / "history" / "v002"
    v001.mkdir()
    v002.mkdir()
    _ = (v001 / "spec.md").write_text("same", encoding="utf-8")
    _ = (v002 / "spec.md").write_text("same", encoding="utf-8")
    proposed_changes = v002 / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "topic-revision.md").write_text(
        "---\ndecision: accept\n---\n\n## Decision and Rationale\n\nokay.\n",
        encoding="utf-8",
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_skips_malformed_front_matter(
    *,
    tmp_path: Path,
) -> None:
    """A revision file with malformed front-matter is skipped."""
    ctx = _make_ctx(tmp_path=tmp_path)
    v001 = ctx.spec_root / "history" / "v001"
    v002 = ctx.spec_root / "history" / "v002"
    v001.mkdir()
    v002.mkdir()
    _ = (v001 / "spec.md").write_text("same", encoding="utf-8")
    _ = (v002 / "spec.md").write_text("same", encoding="utf-8")
    proposed_changes = v002 / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "topic-revision.md").write_text(
        "no front matter here\n",
        encoding="utf-8",
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_skips_non_vnnn_history_entries(
    *,
    tmp_path: Path,
) -> None:
    """Files and non-vNNN dirs under history/ are skipped."""
    ctx = _make_ctx(tmp_path=tmp_path)
    history = ctx.spec_root / "history"
    (history / "v001").mkdir()
    (history / "v002").mkdir()
    _ = (history / "README.md").write_text("readme", encoding="utf-8")
    (history / "not-a-version").mkdir()
    _ = (history / "v001" / "spec.md").write_text("a", encoding="utf-8")
    _ = (history / "v002" / "spec.md").write_text("b", encoding="utf-8")
    _ = _write_revision(
        version_dir=history / "v002",
        stem="topic",
        decision="accept",
        resulting_files=["spec.md"],
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_skips_version_dir_without_proposed_changes(
    *,
    tmp_path: Path,
) -> None:
    """A vNNN with no proposed_changes/ subdir contributes no revisions."""
    ctx = _make_ctx(tmp_path=tmp_path)
    (ctx.spec_root / "history" / "v001").mkdir()
    (ctx.spec_root / "history" / "v002").mkdir()
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_skips_bullet_with_literal_none_placeholder_text(
    *,
    tmp_path: Path,
) -> None:
    """A bullet `- (none)` (defensive against parser corner) yields no path."""
    ctx = _make_ctx(tmp_path=tmp_path)
    v001 = ctx.spec_root / "history" / "v001"
    v002 = ctx.spec_root / "history" / "v002"
    v001.mkdir()
    v002.mkdir()
    _ = (v001 / "spec.md").write_text("same", encoding="utf-8")
    _ = (v002 / "spec.md").write_text("same", encoding="utf-8")
    proposed_changes = v002 / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "topic-revision.md").write_text(
        "---\ndecision: accept\n---\n\n## Resulting Changes\n\n- (none)\n",
        encoding="utf-8",
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_skips_non_revision_files_and_subdirs(
    *,
    tmp_path: Path,
) -> None:
    """Files not matching `*-revision.md` and any subdirs in proposed_changes/ are skipped."""
    ctx = _make_ctx(tmp_path=tmp_path)
    v001 = ctx.spec_root / "history" / "v001"
    v002 = ctx.spec_root / "history" / "v002"
    v001.mkdir()
    v002.mkdir()
    _ = (v001 / "spec.md").write_text("a", encoding="utf-8")
    _ = (v002 / "spec.md").write_text("b", encoding="utf-8")
    proposed_changes = v002 / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "topic.md").write_text("not a revision", encoding="utf-8")
    (proposed_changes / "subdir").mkdir()
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"
