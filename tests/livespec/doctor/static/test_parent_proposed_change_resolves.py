"""Tests for livespec.doctor.static.parent_proposed_change_resolves.

Per work-item li-ixin2s (PC #2 follow-up of v081
`coordinating-epic-stale-revise-enforcement`, paired with
li-ymwpk2 which widened the proposed-change front-matter schema):
for every PC in `<spec-root>/proposed_changes/` AND every accepted
PC in `<spec-root>/history/vNNN/proposed_changes/` (audit-trail
traversal) that carries `parent_proposed_change`:

  - Local form (no `#` prefix) MUST resolve to a PC with the
    cited topic stem in the same spec_root's `proposed_changes/`
    OR any `history/vNNN/proposed_changes/`; otherwise `fail`.
  - Cross-repo form (`<repo>#<topic>`) is noted (status
    `skipped`), NEVER failed — cross-repo lookup is deferred to
    a follow-up per the PC body.

Acceptance scenarios (mirrored from the work-item description):

(1) PC with local-form citation pointing at existing PC in
    `proposed_changes/` → pass.
(2) PC with local-form citation pointing at PC in
    `history/vNNN/proposed_changes/` → pass.
(3) PC with local-form citation pointing at a nonexistent topic
    → fail naming the citing PC + the unresolved topic.
(4) PC with cross-repo form (`some-repo#topic`) → V1 skipped
    finding (NOT fail).
(5) PC with no `parent_proposed_change` field at all → pass
    (field is optional).
(6) Multiple PCs with mixed-form citations → fail aggregating
    every local-form violation; cross-repo notes folded into
    the message only when no local-form fails dominate.
"""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import parent_proposed_change_resolves
from livespec.schemas.dataclasses.finding import Finding
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


_VALID_FRONT_MATTER_TEMPLATE = """\
---
topic: {topic}
author: tester
created_at: 2026-05-26T12:00:00Z
---

# {topic}

body
"""


_WITH_PARENT_TEMPLATE = """\
---
topic: {topic}
author: tester
created_at: 2026-05-26T12:00:00Z
parent_proposed_change: {parent}
---

# {topic}

body
"""

_PASS_MESSAGE = (
    "parent-proposed-change-resolves: every `parent_proposed_change` "
    "local-form citation resolves to a PC in `proposed_changes/` or "
    "`history/vNNN/proposed_changes/`"
)


def _write_pc(*, directory: Path, topic: str, parent: str | None = None) -> Path:
    """Write a PC `<topic>.md` to `directory` with the given parent citation."""
    directory.mkdir(parents=True, exist_ok=True)
    pc_path = directory / f"{topic}.md"
    if parent is None:
        text = _VALID_FRONT_MATTER_TEMPLATE.format(topic=topic)
    else:
        text = _WITH_PARENT_TEMPLATE.format(topic=topic, parent=parent)
    _ = pc_path.write_text(text, encoding="utf-8")
    return pc_path


def _make_ctx(*, tmp_path: Path) -> DoctorContext:
    """Construct a DoctorContext rooted at a fresh project+spec layout."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    (spec_root / "proposed_changes").mkdir()
    (spec_root / "history").mkdir()
    return DoctorContext(project_root=project_root, spec_root=spec_root)


def _run_and_unwrap(*, ctx: DoctorContext) -> Finding:
    """Run the check and unwrap the IOResult to a Finding."""
    return unsafe_perform_io(parent_proposed_change_resolves.run(ctx=ctx)).unwrap()


def test_run_returns_pass_for_local_form_pointing_at_existing_pc(
    *,
    tmp_path: Path,
) -> None:
    """Scenario 1: local-form parent citation resolves to a PC in proposed_changes/.

    Seeds `proposed_changes/parent-topic.md` + `proposed_changes/child-topic.md`
    where the child cites the parent in local form. Asserts pass.
    """
    ctx = _make_ctx(tmp_path=tmp_path)
    _ = _write_pc(directory=ctx.spec_root / "proposed_changes", topic="parent-topic")
    _ = _write_pc(
        directory=ctx.spec_root / "proposed_changes",
        topic="child-topic",
        parent="parent-topic",
    )
    expected = Finding(
        check_id="doctor-parent-proposed-change-resolves",
        status="pass",
        message=_PASS_MESSAGE,
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )
    assert _run_and_unwrap(ctx=ctx) == expected


def test_run_returns_pass_for_local_form_pointing_at_history_pc(
    *,
    tmp_path: Path,
) -> None:
    """Scenario 2: local-form parent citation resolves to a PC in history/vNNN/proposed_changes/.

    Seeds `history/v001/proposed_changes/historical-parent.md` and
    `proposed_changes/child.md` citing the historical parent in
    local form. Asserts pass.
    """
    ctx = _make_ctx(tmp_path=tmp_path)
    _ = _write_pc(
        directory=ctx.spec_root / "history" / "v001" / "proposed_changes",
        topic="historical-parent",
    )
    _ = _write_pc(
        directory=ctx.spec_root / "proposed_changes",
        topic="child",
        parent="historical-parent",
    )
    expected = Finding(
        check_id="doctor-parent-proposed-change-resolves",
        status="pass",
        message=_PASS_MESSAGE,
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )
    assert _run_and_unwrap(ctx=ctx) == expected


def test_run_returns_fail_for_local_form_pointing_at_nonexistent_topic(
    *,
    tmp_path: Path,
) -> None:
    """Scenario 3: local-form parent citation has no matching PC anywhere → fail.

    Seeds `proposed_changes/child.md` citing `phantom-parent` which
    exists in neither `proposed_changes/` nor any `history/vNNN/`.
    Asserts fail naming the citing PC + the unresolved topic.
    """
    ctx = _make_ctx(tmp_path=tmp_path)
    _ = _write_pc(
        directory=ctx.spec_root / "proposed_changes",
        topic="child",
        parent="phantom-parent",
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.check_id == "doctor-parent-proposed-change-resolves"
    assert finding.status == "fail"
    assert "phantom-parent" in finding.message
    assert "child.md" in finding.message
    assert finding.path == "proposed_changes/child.md"


def test_run_returns_skipped_for_cross_repo_form_citation(
    *,
    tmp_path: Path,
) -> None:
    """Scenario 4: cross-repo form (`some-repo#topic`) → V1 skipped, NEVER fail.

    Seeds `proposed_changes/child.md` citing `some-repo#some-topic`.
    Asserts the finding is `skipped` (informational), NOT fail.
    """
    ctx = _make_ctx(tmp_path=tmp_path)
    _ = _write_pc(
        directory=ctx.spec_root / "proposed_changes",
        topic="child",
        parent="some-repo#some-topic",
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.check_id == "doctor-parent-proposed-change-resolves"
    assert finding.status == "skipped"
    assert "some-repo#some-topic" in finding.message
    assert "cross-repo" in finding.message.lower()
    assert finding.path == "proposed_changes/child.md"


def test_run_returns_pass_when_no_parent_proposed_change_field_present(
    *,
    tmp_path: Path,
) -> None:
    """Scenario 5: PC without `parent_proposed_change` field → pass (field optional).

    Seeds two PCs in `proposed_changes/` neither of which carries
    a `parent_proposed_change` field. Asserts pass.
    """
    ctx = _make_ctx(tmp_path=tmp_path)
    _ = _write_pc(directory=ctx.spec_root / "proposed_changes", topic="standalone-a")
    _ = _write_pc(directory=ctx.spec_root / "proposed_changes", topic="standalone-b")
    expected = Finding(
        check_id="doctor-parent-proposed-change-resolves",
        status="pass",
        message=_PASS_MESSAGE,
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )
    assert _run_and_unwrap(ctx=ctx) == expected


def test_run_aggregates_multiple_local_form_fails(
    *,
    tmp_path: Path,
) -> None:
    """Scenario 6 (subset): multiple unresolved local-form citations → fail aggregated.

    Seeds two children citing two distinct phantom parents. Asserts
    the single Finding is fail, mentions both citing children and
    both unresolved topics.
    """
    ctx = _make_ctx(tmp_path=tmp_path)
    _ = _write_pc(
        directory=ctx.spec_root / "proposed_changes",
        topic="child-a",
        parent="phantom-one",
    )
    _ = _write_pc(
        directory=ctx.spec_root / "proposed_changes",
        topic="child-b",
        parent="phantom-two",
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "fail"
    assert "child-a.md" in finding.message
    assert "child-b.md" in finding.message
    assert "phantom-one" in finding.message
    assert "phantom-two" in finding.message


def test_run_fail_dominates_cross_repo_when_both_present(
    *,
    tmp_path: Path,
) -> None:
    """Scenario 6 (mixed): local-form fail + cross-repo citation → fail wins.

    Seeds one child with a local-form citation to a nonexistent
    topic AND one child with a cross-repo citation. Asserts the
    single Finding is fail (local-form fail dominates) and the
    fail message mentions the unresolved local citation. The
    cross-repo citation is silently absorbed in this aggregate
    finding (user fixes the fail first; on re-run the cross-repo
    note surfaces).
    """
    ctx = _make_ctx(tmp_path=tmp_path)
    _ = _write_pc(
        directory=ctx.spec_root / "proposed_changes",
        topic="child-local",
        parent="phantom-local",
    )
    _ = _write_pc(
        directory=ctx.spec_root / "proposed_changes",
        topic="child-cross",
        parent="other-repo#other-topic",
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "fail"
    assert "phantom-local" in finding.message
    # Cross-repo entry not surfaced when fail dominates.
    assert "other-repo" not in finding.message


def test_run_traverses_history_for_citing_pcs_too(
    *,
    tmp_path: Path,
) -> None:
    """A PC INSIDE history/vNNN/proposed_changes/ also gets walked for citations.

    Seeds `history/v001/proposed_changes/historical-child.md`
    citing `phantom-history-parent` (not present). Asserts the
    check fires fail naming the history-relative path.
    """
    ctx = _make_ctx(tmp_path=tmp_path)
    _ = _write_pc(
        directory=ctx.spec_root / "history" / "v001" / "proposed_changes",
        topic="historical-child",
        parent="phantom-history-parent",
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "fail"
    assert "phantom-history-parent" in finding.message
    assert "history/v001/proposed_changes/historical-child.md" in finding.message


def test_run_ignores_revision_files_in_history(
    *,
    tmp_path: Path,
) -> None:
    """Revision files (`*-revision.md`) are not PCs; they are not walked as citers.

    Seeds `history/v001/proposed_changes/some-topic-revision.md`
    (a revision artifact, not a PC) carrying a bogus
    `parent_proposed_change` value. Asserts pass — revision files
    are excluded from both the citer list and the known-topics
    union.
    """
    ctx = _make_ctx(tmp_path=tmp_path)
    revision_dir = ctx.spec_root / "history" / "v001" / "proposed_changes"
    revision_dir.mkdir(parents=True)
    _ = (revision_dir / "some-topic-revision.md").write_text(
        _WITH_PARENT_TEMPLATE.format(topic="some-topic", parent="phantom-from-revision"),
        encoding="utf-8",
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_skips_subdirectories_inside_proposed_changes(
    *,
    tmp_path: Path,
) -> None:
    """Subdirectories inside `proposed_changes/` (e.g., misplaced folders) are skipped.

    Seeds a subdirectory under `proposed_changes/` (an
    out-of-format artifact some flows briefly produce). The
    check tolerates the presence; non-file entries are filtered
    out of the PC walk and the known-topics union. Asserts pass.
    """
    ctx = _make_ctx(tmp_path=tmp_path)
    misplaced_dir = ctx.spec_root / "proposed_changes" / "misplaced-subdir"
    misplaced_dir.mkdir()
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_skips_non_md_files_inside_proposed_changes(
    *,
    tmp_path: Path,
) -> None:
    """Non-`.md` files inside `proposed_changes/` are not treated as PCs.

    Seeds a `.json` file under `proposed_changes/` (e.g., a stray
    artifact). The `_is_pc_file` helper returns False for entries
    whose name does not end with `.md`; the check ignores them.
    Asserts pass.
    """
    ctx = _make_ctx(tmp_path=tmp_path)
    stray = ctx.spec_root / "proposed_changes" / "stray.json"
    _ = stray.write_text("{}", encoding="utf-8")
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "pass"


def test_run_returns_pass_when_no_pcs_present_at_all(
    *,
    tmp_path: Path,
) -> None:
    """A spec_root with empty proposed_changes/ and empty history/ → pass.

    No PCs anywhere means nothing to walk and nothing to fail; the
    pass-Finding is the canonical "every citation resolves"
    message (vacuously true).
    """
    ctx = _make_ctx(tmp_path=tmp_path)
    expected = Finding(
        check_id="doctor-parent-proposed-change-resolves",
        status="pass",
        message=_PASS_MESSAGE,
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )
    assert _run_and_unwrap(ctx=ctx) == expected
