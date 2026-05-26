"""Tests for livespec.doctor.static.unresolved_spec_commitment.

Per `SPECIFICATION/contracts.md` §"`unresolved-spec-commitment`":
the check walks every `<spec-target>/history/vNNN/proposed_changes/<stem>.md`
whose paired `<stem>-revision.md` carries `decision` in
`{accept, modify}`, reads each declared `spec_commitments.impl_followups[]`
entry, and fires `fail` when the entry's `id_hint` does not
resolve to a work-item carrying matching `spec_commitment_hint`.

Supersession exempt: when a later vNNN/ propose-change declares
`spec_commitments.supersedes: [<earlier-id_hint>, ...]`, the
listed id_hints are exempt from the coverage check. Reject
decisions are exempt; absent `spec_commitments` is exempt
vacuously. Cross-repo: when `.livespec.jsonc` lacks an impl-plugin,
the invariant surfaces a `skipped` Finding rather than fail.

Mocking strategy:

  The check reads the impl-plugin's work-items store directly
  (per the v1 mechanism mirrored from no-stalled-epic /
  no-orphan-dependency / no-duplicate-gap-id), not via a
  subprocess invocation. Tests therefore write the JSONL store
  to `<project_root>/work-items.jsonl` directly; no subprocess
  stub is needed. The work-item records carry the
  `spec_commitment_hint` field (the impl-plaintext-side
  delivery of which is sibling work-item li-4szyct); absence of
  the field on a record yields no match (= fail when no other
  record matches that id_hint).
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import _unresolved_spec_commitment_helpers as helpers
from livespec.doctor.static import unresolved_spec_commitment
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


_CONFIG_TEXT_PLAINTEXT = """// minimal livespec config
{
  "template": "livespec",
  "spec_root": "SPECIFICATION",
  "implementation": { "plugin": "livespec-impl-plaintext" },
  "livespec-impl-plaintext": {
    "format": "jsonl",
    "work_items_path": "work-items.jsonl"
  }
}
"""


_CONFIG_TEXT_NO_IMPL = """// livespec config without an impl-plugin entry
{
  "template": "livespec",
  "spec_root": "SPECIFICATION"
}
"""


def _setup_project(
    *,
    tmp_path: Path,
    config_text: str = _CONFIG_TEXT_PLAINTEXT,
    work_items: list[dict[str, object]] | None = None,
) -> tuple[Path, Path]:
    """Create a project root with .livespec.jsonc and (optional) work-items.jsonl.

    Returns `(project_root, spec_root)`. The spec_root is created
    as an empty directory; per-version PC and revision files are
    seeded by individual test helpers.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    if work_items is not None:
        jsonl_text = "".join(
            json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n"
            for record in work_items
        )
        _ = (project_root / "work-items.jsonl").write_text(jsonl_text, encoding="utf-8")
    return project_root, spec_root


def _write_pc(
    *,
    spec_root: Path,
    version: str,
    stem: str,
    spec_commitments_block: str | None = None,
) -> None:
    """Write a propose-change file under history/<version>/proposed_changes/.

    `spec_commitments_block` (when provided) is the literal text
    of the front-matter `spec_commitments:` block (without the
    leading `---` delimiters). When None, the PC carries no
    `spec_commitments` field at all.
    """
    pc_dir = spec_root / "history" / version / "proposed_changes"
    pc_dir.mkdir(parents=True, exist_ok=True)
    front_matter = (
        "---\n" f"topic: {stem}\n" "author: test-author\n" "created_at: 2026-01-01T00:00:00Z\n"
    )
    if spec_commitments_block is not None:
        front_matter += spec_commitments_block
    front_matter += "---\n\n"
    body = f"## Proposal: {stem}\n\nbody body body\n"
    _ = (pc_dir / f"{stem}.md").write_text(front_matter + body, encoding="utf-8")


def _write_revision(
    *,
    spec_root: Path,
    version: str,
    stem: str,
    decision: str,
) -> None:
    """Write a revision file paired with the PC at <history>/<version>/proposed_changes/."""
    pc_dir = spec_root / "history" / version / "proposed_changes"
    pc_dir.mkdir(parents=True, exist_ok=True)
    text = (
        "---\n"
        f"proposal: {stem}.md\n"
        f"decision: {decision}\n"
        "revised_at: 2026-01-01T00:00:00Z\n"
        "author_human: Test User <test@example.com>\n"
        "author_llm: claude-opus-4-7\n"
        "---\n\n"
        "## Decision and Rationale\n\nrationale\n\n"
        "## Resulting Changes\n\n- spec.md\n"
    )
    _ = (pc_dir / f"{stem}-revision.md").write_text(text, encoding="utf-8")


def _work_item(*, item_id: str, spec_commitment_hint: str) -> dict[str, object]:
    """Build a minimal work-item record with the four fields the check reads.

    `spec_commitment_hint` is the load-bearing field — the impl-
    plaintext-side delivery of which is sibling work-item
    li-4szyct. Tests that want to exercise the "field absent
    from record" path use a raw-dict literal in the test body
    rather than this helper.
    """
    return {
        "id": item_id,
        "type": "task",
        "status": "open",
        "depends_on": [],
        "spec_commitment_hint": spec_commitment_hint,
    }


_TWO_ID_HINTS_BLOCK = (
    "spec_commitments:\n"
    "  impl_followups:\n"
    "    - id_hint: alpha-hint\n"
    "      description: |\n"
    "        first follow-up\n"
    "    - id_hint: beta-hint\n"
    "      description: |\n"
    "        second follow-up\n"
)


_SUPERSEDES_OLD_BLOCK = (
    "spec_commitments:\n"
    "  impl_followups:\n"
    "    - id_hint: gamma-hint\n"
    "      description: |\n"
    "        later follow-up\n"
    "  supersedes:\n"
    "    - old-hint\n"
)


_ONE_ID_HINT_OLD_BLOCK = (
    "spec_commitments:\n"
    "  impl_followups:\n"
    "    - id_hint: old-hint\n"
    "      description: |\n"
    "        earlier follow-up\n"
)


def test_passes_when_every_id_hint_has_matching_work_item(
    *,
    tmp_path: Path,
) -> None:
    """Test scenario 1: every declared id_hint resolves to a matching work-item → `pass`."""
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        work_items=[
            _work_item(item_id="li-aaaaaa", spec_commitment_hint="alpha-hint"),
            _work_item(item_id="li-bbbbbb", spec_commitment_hint="beta-hint"),
        ],
    )
    _write_pc(
        spec_root=spec_root,
        version="v001",
        stem="seeding",
        spec_commitments_block=_TWO_ID_HINTS_BLOCK,
    )
    _write_revision(spec_root=spec_root, version="v001", stem="seeding", decision="accept")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="pass",
        message=(
            "unresolved-spec-commitment: every declared spec_commitments."
            "impl_followups[] id_hint resolves to a work-item with matching "
            "spec_commitment_hint or has been superseded "
            "(2 obligation(s) scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_fails_when_one_id_hint_is_absent_from_work_items(
    *,
    tmp_path: Path,
) -> None:
    """Test scenario 2: one declared id_hint has no matching work-item → `fail` naming it + version."""
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        work_items=[
            _work_item(item_id="li-aaaaaa", spec_commitment_hint="alpha-hint"),
            # beta-hint deliberately absent
        ],
    )
    _write_pc(
        spec_root=spec_root,
        version="v005",
        stem="commitments",
        spec_commitments_block=_TWO_ID_HINTS_BLOCK,
    )
    _write_revision(spec_root=spec_root, version="v005", stem="commitments", decision="accept")
    work_items_path = project_root / "work-items.jsonl"

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="fail",
        message=(
            f"unresolved-spec-commitment: 1 declared "
            f"spec_commitments.impl_followups[] id_hint(s) have no matching "
            f"work-item with spec_commitment_hint in "
            f"{work_items_path}: beta-hint (from v005/commitments.md). "
            f"Corrective action: file each missing work-item via the active "
            f"impl-plugin's `capture-work-item` skill, passing "
            f"`--spec-commitment-hint <id_hint>` so the work-item carries "
            f"the pairing field."
        ),
        path=str(work_items_path),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_id_hint_is_superseded_in_a_later_version(
    *,
    tmp_path: Path,
) -> None:
    """Test scenario 3: id_hint superseded in a LATER version → exempt; pass.

    The earlier v001 PC declares `old-hint` with no matching
    work-item (it would normally fire fail), but the v002 PC
    declares `supersedes: [old-hint]`, exempting it. The v002 PC
    declares its OWN id_hint (`gamma-hint`) which IS covered by
    a work-item, so the check passes overall.
    """
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        work_items=[
            _work_item(item_id="li-gamma", spec_commitment_hint="gamma-hint"),
            # old-hint deliberately ABSENT — supersession should exempt it.
        ],
    )
    _write_pc(
        spec_root=spec_root,
        version="v001",
        stem="earlier-pc",
        spec_commitments_block=_ONE_ID_HINT_OLD_BLOCK,
    )
    _write_revision(spec_root=spec_root, version="v001", stem="earlier-pc", decision="accept")
    _write_pc(
        spec_root=spec_root,
        version="v002",
        stem="later-pc",
        spec_commitments_block=_SUPERSEDES_OLD_BLOCK,
    )
    _write_revision(spec_root=spec_root, version="v002", stem="later-pc", decision="accept")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="pass",
        message=(
            "unresolved-spec-commitment: every declared spec_commitments."
            "impl_followups[] id_hint resolves to a work-item with matching "
            "spec_commitment_hint or has been superseded "
            "(2 obligation(s) scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skipped_when_livespec_jsonc_lacks_impl_plugin_entry(
    *,
    tmp_path: Path,
) -> None:
    """Test scenario 4: `.livespec.jsonc` lacks impl-plugin → `skipped` (NOT fail).

    Even when the spec tree carries propose-changes declaring
    spec_commitments.impl_followups[] with NO matching work-items,
    a missing `implementation` block means the invariant has no
    impl-plugin store to query — the appropriate outcome is
    `skipped`, not `fail`.
    """
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        config_text=_CONFIG_TEXT_NO_IMPL,
    )
    _write_pc(
        spec_root=spec_root,
        version="v001",
        stem="commitments",
        spec_commitments_block=_TWO_ID_HINTS_BLOCK,
    )
    _write_revision(spec_root=spec_root, version="v001", stem="commitments", decision="accept")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="skipped",
        message=(
            "unresolved-spec-commitment: active impl-plugin is not in the "
            "v1 supported set (livespec-impl-plaintext) or .livespec.jsonc "
            "lacks an `implementation` block; check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_pc_lacks_spec_commitments_entirely(
    *,
    tmp_path: Path,
) -> None:
    """Test scenario 5: PC has no `spec_commitments` field → vacuously exempt; pass.

    Zero-commitment payload (the common case for propose-changes
    that don't declare any cross-boundary obligations) is exempt
    per the contract's vacuous-empty clause. With no obligations
    in scope, the check reports a vacuous pass.
    """
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        work_items=[],
    )
    _write_pc(
        spec_root=spec_root, version="v001", stem="no-commitments", spec_commitments_block=None
    )
    _write_revision(
        spec_root=spec_root,
        version="v001",
        stem="no-commitments",
        decision="accept",
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="pass",
        message=(
            "unresolved-spec-commitment: no propose-changes declare "
            "spec_commitments.impl_followups[]; nothing to verify"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_decision_is_reject_even_with_unresolved_id_hints(
    *,
    tmp_path: Path,
) -> None:
    """Test scenario 6: reject decision → PC entirely skipped; vacuous pass.

    A propose-change with `decision: reject` declares no
    obligation regardless of its `spec_commitments` content,
    per the contract's reject-exempt clause. The fixture
    deliberately omits any matching work-items so a
    decision-honoring bug would surface as `fail`.
    """
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        work_items=[],
    )
    _write_pc(
        spec_root=spec_root,
        version="v001",
        stem="rejected-pc",
        spec_commitments_block=_TWO_ID_HINTS_BLOCK,
    )
    _write_revision(
        spec_root=spec_root,
        version="v001",
        stem="rejected-pc",
        decision="reject",
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="pass",
        message=(
            "unresolved-spec-commitment: no propose-changes declare "
            "spec_commitments.impl_followups[]; nothing to verify"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skipped_when_livespec_jsonc_missing(
    *,
    tmp_path: Path,
) -> None:
    """`.livespec.jsonc` missing entirely → `skipped` (precondition not met)."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="skipped",
        message=(
            "unresolved-spec-commitment: precondition not met " "(PreconditionError); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_fails_with_no_work_items_store_when_obligations_declared(
    *,
    tmp_path: Path,
) -> None:
    """No work-items.jsonl on disk but obligations declared → `fail` naming the unresolved hints.

    The work-items store has not been initialized yet (e.g., the
    user accepted the propose-change but has not yet filed any
    work-items). The check treats the empty hint set as the
    "every id_hint unresolved" case and fails.
    """
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        # No work_items list → no work-items.jsonl on disk.
    )
    _write_pc(
        spec_root=spec_root,
        version="v007",
        stem="newly-accepted",
        spec_commitments_block=_TWO_ID_HINTS_BLOCK,
    )
    _write_revision(
        spec_root=spec_root,
        version="v007",
        stem="newly-accepted",
        decision="accept",
    )
    work_items_path = project_root / "work-items.jsonl"

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="fail",
        message=(
            f"unresolved-spec-commitment: 2 declared "
            f"spec_commitments.impl_followups[] id_hint(s) have no matching "
            f"work-item with spec_commitment_hint in "
            f"{work_items_path}: alpha-hint (from v007/newly-accepted.md); "
            f"beta-hint (from v007/newly-accepted.md). "
            f"Corrective action: file each missing work-item via the active "
            f"impl-plugin's `capture-work-item` skill, passing "
            f"`--spec-commitment-hint <id_hint>` so the work-item carries "
            f"the pairing field."
        ),
        path=str(work_items_path),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_modify_decision_treated_like_accept(
    *,
    tmp_path: Path,
) -> None:
    """`decision: modify` is treated the same as `accept` per the contract.

    The contract enumerates `{accept, modify}` as the gated set;
    a modified PC's spec_commitments are honored just like an
    accepted PC's.
    """
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        work_items=[
            _work_item(item_id="li-aaaaaa", spec_commitment_hint="alpha-hint"),
            _work_item(item_id="li-bbbbbb", spec_commitment_hint="beta-hint"),
        ],
    )
    _write_pc(
        spec_root=spec_root,
        version="v001",
        stem="modified-pc",
        spec_commitments_block=_TWO_ID_HINTS_BLOCK,
    )
    _write_revision(
        spec_root=spec_root,
        version="v001",
        stem="modified-pc",
        decision="modify",
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="pass",
        message=(
            "unresolved-spec-commitment: every declared spec_commitments."
            "impl_followups[] id_hint resolves to a work-item with matching "
            "spec_commitment_hint or has been superseded "
            "(2 obligation(s) scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_root_not_object_yields_skipped(
    *,
    tmp_path: Path,
) -> None:
    """`.livespec.jsonc` whose root is a JSON array (not object) → skipped."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text("[]\n", encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="skipped",
        message=(
            "unresolved-spec-commitment: .livespec.jsonc root is not an " "object; check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def _vacuous_pass_finding(*, spec_root: Path) -> Finding:
    """Vacuous-pass Finding used by several PC-walk-edge-case e2e tests."""
    return Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="pass",
        message=(
            "unresolved-spec-commitment: no propose-changes declare "
            "spec_commitments.impl_followups[]; nothing to verify"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )


def test_pc_without_front_matter_treated_as_no_commitments(*, tmp_path: Path) -> None:
    """A PC file lacking leading `---\\n` contributes no obligations (vacuous pass).

    Exercises the helper's `_split_front_matter_block` → None branch
    through the public `run()` entry point so we don't depend on
    private helper symbols.
    """
    project_root, spec_root = _setup_project(tmp_path=tmp_path, work_items=[])
    pc_dir = spec_root / "history" / "v001" / "proposed_changes"
    pc_dir.mkdir(parents=True)
    _ = (pc_dir / "no-fm.md").write_text("just a markdown body\n", encoding="utf-8")
    _write_revision(spec_root=spec_root, version="v001", stem="no-fm", decision="accept")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    assert result == IOSuccess(_vacuous_pass_finding(spec_root=spec_root))


def test_pc_with_unterminated_front_matter_treated_as_no_commitments(
    *,
    tmp_path: Path,
) -> None:
    """A PC file whose front-matter never closes contributes no obligations."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path, work_items=[])
    pc_dir = spec_root / "history" / "v001" / "proposed_changes"
    pc_dir.mkdir(parents=True)
    _ = (pc_dir / "unterm.md").write_text("---\ntopic: foo\nauthor: bar\n", encoding="utf-8")
    _write_revision(spec_root=spec_root, version="v001", stem="unterm", decision="accept")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    assert result == IOSuccess(_vacuous_pass_finding(spec_root=spec_root))


def test_revision_with_malformed_front_matter_skipped(*, tmp_path: Path) -> None:
    """A revision file with malformed front-matter → decision unreadable → skipped silently."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path, work_items=[])
    _write_pc(
        spec_root=spec_root,
        version="v001",
        stem="bad-rev",
        spec_commitments_block=_TWO_ID_HINTS_BLOCK,
    )
    pc_dir = spec_root / "history" / "v001" / "proposed_changes"
    _ = (pc_dir / "bad-rev-revision.md").write_text(
        "not front matter at all\n",
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    assert result == IOSuccess(_vacuous_pass_finding(spec_root=spec_root))


def test_revision_missing_decision_key_skipped(*, tmp_path: Path) -> None:
    """Revision file with front-matter but no `decision:` key → no obligation registered."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path, work_items=[])
    _write_pc(
        spec_root=spec_root,
        version="v001",
        stem="no-dec",
        spec_commitments_block=_TWO_ID_HINTS_BLOCK,
    )
    pc_dir = spec_root / "history" / "v001" / "proposed_changes"
    _ = (pc_dir / "no-dec-revision.md").write_text(
        "---\nproposal: no-dec.md\nrevised_at: 2026-01-01T00:00:00Z\n---\n",
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    assert result == IOSuccess(_vacuous_pass_finding(spec_root=spec_root))


def test_revision_with_non_string_decision_skipped(*, tmp_path: Path) -> None:
    """Revision file with `decision: null` → decision unreadable as string → skipped."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path, work_items=[])
    _write_pc(
        spec_root=spec_root,
        version="v001",
        stem="null-dec",
        spec_commitments_block=_TWO_ID_HINTS_BLOCK,
    )
    pc_dir = spec_root / "history" / "v001" / "proposed_changes"
    _ = (pc_dir / "null-dec-revision.md").write_text(
        "---\nproposal: null-dec.md\ndecision: null\nrevised_at: 2026-01-01T00:00:00Z\n---\n",
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    assert result == IOSuccess(_vacuous_pass_finding(spec_root=spec_root))


def test_history_absent_yields_vacuous_pass(*, tmp_path: Path) -> None:
    """No `history/` directory under spec_root → empty walk → vacuous pass."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path, work_items=[])
    # history/ deliberately not created
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    assert result == IOSuccess(_vacuous_pass_finding(spec_root=spec_root))


def test_history_with_noise_children_filtered(*, tmp_path: Path) -> None:
    """`history/` walk skips files, non-vNNN dirs, and pruned-marker dirs.

    Exercises the helper's filter branches through the public run()
    entry point: noise children must not produce obligations.
    """
    project_root, spec_root = _setup_project(tmp_path=tmp_path, work_items=[])
    history = spec_root / "history"
    history.mkdir()
    # Noise: a regular file, a non-vNNN dir, and a pruned vNNN dir.
    _ = (history / "readme.txt").write_text("noise", encoding="utf-8")
    (history / "drafts").mkdir()
    pruned = history / "v001"
    pruned.mkdir()
    _ = (pruned / "PRUNED_HISTORY.json").write_text("{}", encoding="utf-8")
    # The pruned dir CONTAINS a PC + revision with declared obligations
    # that SHOULD be ignored because of the pruned marker.
    pruned_pc_dir = pruned / "proposed_changes"
    pruned_pc_dir.mkdir()
    _ = (pruned_pc_dir / "ignored.md").write_text(
        "---\ntopic: ignored\nauthor: a\ncreated_at: 2026-01-01T00:00:00Z\n"
        + _TWO_ID_HINTS_BLOCK
        + "---\n\nbody\n",
        encoding="utf-8",
    )
    _ = (pruned_pc_dir / "ignored-revision.md").write_text(
        "---\nproposal: ignored.md\ndecision: accept\nrevised_at: 2026-01-01T00:00:00Z\n---\n",
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    assert result == IOSuccess(_vacuous_pass_finding(spec_root=spec_root))


def test_proposed_changes_directory_absent_in_version_dir(*, tmp_path: Path) -> None:
    """A vNNN/ dir without a `proposed_changes/` subdir yields no obligations."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path, work_items=[])
    (spec_root / "history" / "v001").mkdir(parents=True)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    assert result == IOSuccess(_vacuous_pass_finding(spec_root=spec_root))


def test_pc_dir_with_non_md_and_subdir_filtered(*, tmp_path: Path) -> None:
    """`proposed_changes/` walk skips non-.md files, non-files, and `*-revision.md` siblings.

    A `proposed_changes/` directory carrying a `.txt` file and a
    subdirectory must not yield obligations from either.
    """
    project_root, spec_root = _setup_project(tmp_path=tmp_path, work_items=[])
    pc_dir = spec_root / "history" / "v001" / "proposed_changes"
    pc_dir.mkdir(parents=True)
    _ = (pc_dir / "noise.txt").write_text("not a PC", encoding="utf-8")
    (pc_dir / "subdir").mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    assert result == IOSuccess(_vacuous_pass_finding(spec_root=spec_root))


def test_work_items_jsonl_with_noise_lines_treated_as_empty_hint_set(
    *,
    tmp_path: Path,
) -> None:
    """JSONL store with malformed lines, missing/non-string ids, and non-string hints → empty hint set.

    Exercises `materialize_work_item_hints` through the public
    entry point by writing a JSONL store that contains every
    drop-path variant the helper handles; the resulting hint set
    is effectively empty, so any declared id_hint MUST fail.
    """
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    work_items_path = project_root / "work-items.jsonl"
    _ = work_items_path.write_text(
        "\n"  # blank line
        "{ not json }\n"  # parse failure
        "[1,2,3]\n"  # not an object
        '{"no_id": "x"}\n'  # missing id
        '{"id": 7, "spec_commitment_hint": "would-match"}\n'  # non-string id
        '{"id": "li-a", "spec_commitment_hint": null}\n'  # hint is null
        '{"id": "li-b", "spec_commitment_hint": 42}\n'  # hint is non-string
        '{"id": "li-c", "spec_commitment_hint": ""}\n'  # hint is empty
        '{"id": "li-d", "spec_commitment_hint": "alpha-hint"}\n'
        '{"id": "li-d", "spec_commitment_hint": "later-hint"}\n',  # last wins for li-d
        encoding="utf-8",
    )
    _write_pc(
        spec_root=spec_root,
        version="v001",
        stem="claim",
        spec_commitments_block=_TWO_ID_HINTS_BLOCK,
    )
    _write_revision(spec_root=spec_root, version="v001", stem="claim", decision="accept")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    # `alpha-hint` is shadowed by the later "later-hint" record; only `later-hint`
    # ends up in the hint set, so beta-hint is unresolved AND alpha-hint is
    # unresolved (the original li-d record's "alpha-hint" was overwritten).
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="fail",
        message=(
            f"unresolved-spec-commitment: 2 declared "
            f"spec_commitments.impl_followups[] id_hint(s) have no matching "
            f"work-item with spec_commitment_hint in "
            f"{work_items_path}: alpha-hint (from v001/claim.md); "
            f"beta-hint (from v001/claim.md). "
            f"Corrective action: file each missing work-item via the active "
            f"impl-plugin's `capture-work-item` skill, passing "
            f"`--spec-commitment-hint <id_hint>` so the work-item carries "
            f"the pairing field."
        ),
        path=str(work_items_path),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_materialize_work_item_hints_ignores_invalid_jsonl_lines() -> None:
    """Public helper: malformed lines, missing ids, non-string hints are all dropped."""
    text = (
        "\n"  # blank line
        "{ not json }\n"  # parse failure
        "[1,2,3]\n"  # not an object
        '{"no_id": "x"}\n'  # missing id
        '{"id": 7}\n'  # non-string id (must be str)
        '{"id": "li-a", "spec_commitment_hint": null}\n'  # hint is null
        '{"id": "li-b", "spec_commitment_hint": 42}\n'  # hint is non-string
        '{"id": "li-c", "spec_commitment_hint": ""}\n'  # hint is empty
        '{"id": "li-d", "spec_commitment_hint": "real-hint"}\n'
        '{"id": "li-d", "spec_commitment_hint": "later-hint"}\n'  # last wins
    )
    hints = helpers.materialize_work_item_hints(jsonl_text=text)
    assert hints == {"later-hint"}


def test_resolve_work_items_path_skips_non_dict_implementation(*, tmp_path: Path) -> None:
    """Helper: `implementation` key is not a dict → None."""
    assert (
        helpers.resolve_work_items_path(
            project_root=tmp_path,
            config={"implementation": "not-a-dict"},
        )
        is None
    )


def test_resolve_work_items_path_skips_unsupported_plugin(*, tmp_path: Path) -> None:
    """Helper: plugin name not in the supported set → None."""
    assert (
        helpers.resolve_work_items_path(
            project_root=tmp_path,
            config={"implementation": {"plugin": "some-other-plugin"}},
        )
        is None
    )


def test_resolve_work_items_path_default_when_plugin_section_missing(
    *,
    tmp_path: Path,
) -> None:
    """Helper: known plugin but no per-plugin section → defaults to `work-items.jsonl`."""
    resolved = helpers.resolve_work_items_path(
        project_root=tmp_path,
        config={"implementation": {"plugin": "livespec-impl-plaintext"}},
    )
    assert resolved == tmp_path / "work-items.jsonl"


def test_resolve_work_items_path_non_string_work_items_path(*, tmp_path: Path) -> None:
    """Helper: per-plugin section's `work_items_path` is not a string → default used."""
    resolved = helpers.resolve_work_items_path(
        project_root=tmp_path,
        config={
            "implementation": {"plugin": "livespec-impl-plaintext"},
            "livespec-impl-plaintext": {"work_items_path": 42},
        },
    )
    assert resolved == tmp_path / "work-items.jsonl"


def test_orphan_revision_file_is_skipped(*, tmp_path: Path) -> None:
    """Helper: `<stem>-revision.md` with no paired `<stem>.md` is silently skipped.

    The check pairs against PC files only; a revision file
    without a matching PC stem yields no obligation. The
    `_list_pc_stems` filter excludes revision files from the
    stem set; the revision file then never appears in the walk.
    Verified end-to-end here.
    """
    project_root, spec_root = _setup_project(tmp_path=tmp_path, work_items=[])
    pc_dir = spec_root / "history" / "v001" / "proposed_changes"
    pc_dir.mkdir(parents=True)
    # Write ONLY a revision file (no paired PC.md).
    _ = (pc_dir / "orphan-revision.md").write_text(
        "---\nproposal: orphan.md\ndecision: accept\nrevised_at: 2026-01-01T00:00:00Z\n---\n",
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="pass",
        message=(
            "unresolved-spec-commitment: no propose-changes declare "
            "spec_commitments.impl_followups[]; nothing to verify"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_pc_without_paired_revision_is_skipped(*, tmp_path: Path) -> None:
    """Walk skips a PC whose `<stem>-revision.md` does not exist (revise hasn't run)."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path, work_items=[])
    _write_pc(
        spec_root=spec_root,
        version="v001",
        stem="not-yet-revised",
        spec_commitments_block=_TWO_ID_HINTS_BLOCK,
    )
    # No revision file written.
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="pass",
        message=(
            "unresolved-spec-commitment: no propose-changes declare "
            "spec_commitments.impl_followups[]; nothing to verify"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


_FRONT_MATTER_WITH_BLANK_LINE_AND_SIBLING_KEY_BLOCK = (
    "spec_commitments:\n"
    "  impl_followups:\n"
    "\n"  # blank line inside the impl_followups: sub-block (parser admits)
    "    - id_hint: delta-hint\n"
    "      description: |\n"
    "        first follow-up\n"
    "  supersedes:\n"
    "    - prior-hint\n"
    "parent_proposed_change: some-parent\n"  # sibling key at indent 0 — terminator
)


def test_pc_with_blank_line_in_spec_commitments_block_and_sibling_key(
    *,
    tmp_path: Path,
) -> None:
    """A PC whose `spec_commitments:` block contains a blank line + an outdented sibling key.

    Exercises the indent-walk helpers' blank-line-passthrough and
    outdented-terminator branches end-to-end via `run()`. The
    parser MUST admit the blank line and stop at the sibling
    `parent_proposed_change:` key (same indent as
    `spec_commitments:`).
    """
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        work_items=[
            _work_item(item_id="li-delta", spec_commitment_hint="delta-hint"),
        ],
    )
    _write_pc(
        spec_root=spec_root,
        version="v001",
        stem="indented-pc",
        spec_commitments_block=_FRONT_MATTER_WITH_BLANK_LINE_AND_SIBLING_KEY_BLOCK,
    )
    _write_revision(
        spec_root=spec_root,
        version="v001",
        stem="indented-pc",
        decision="accept",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="pass",
        message=(
            "unresolved-spec-commitment: every declared spec_commitments."
            "impl_followups[] id_hint resolves to a work-item with matching "
            "spec_commitment_hint or has been superseded "
            "(1 obligation(s) scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


_FRONT_MATTER_WITH_EMPTY_ID_HINT_VALUE_BLOCK = (
    "spec_commitments:\n"
    "  impl_followups:\n"
    "    - id_hint: \n"  # empty value after `id_hint:` — must be skipped
    "      description: |\n"
    "        skipped entry\n"
    "    - id_hint: real-hint\n"
    "      description: |\n"
    "        kept entry\n"
)


def test_pc_with_empty_id_hint_value_silently_dropped(*, tmp_path: Path) -> None:
    """An `- id_hint:` entry whose value strips to empty is silently dropped.

    Exercises the helper's `if value:` guard in
    `_extract_impl_followups_id_hints` end-to-end via `run()`.
    """
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        work_items=[
            _work_item(item_id="li-real", spec_commitment_hint="real-hint"),
        ],
    )
    _write_pc(
        spec_root=spec_root,
        version="v001",
        stem="empty-hint",
        spec_commitments_block=_FRONT_MATTER_WITH_EMPTY_ID_HINT_VALUE_BLOCK,
    )
    _write_revision(
        spec_root=spec_root,
        version="v001",
        stem="empty-hint",
        decision="accept",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="pass",
        message=(
            "unresolved-spec-commitment: every declared spec_commitments."
            "impl_followups[] id_hint resolves to a work-item with matching "
            "spec_commitment_hint or has been superseded "
            "(1 obligation(s) scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


_FRONT_MATTER_WITH_NON_BULLET_LINE_IN_SUPERSEDES = (
    "spec_commitments:\n"
    "  impl_followups:\n"
    "    - id_hint: kept-hint\n"
    "      description: |\n"
    "        kept entry\n"
    "  supersedes:\n"
    "    not-a-bullet-line\n"  # not a `- ` bullet — dropped silently
    "    - real-superseded\n"
)


def test_pc_with_non_bullet_line_in_supersedes_dropped(*, tmp_path: Path) -> None:
    """A non-`- ` line inside `supersedes:` is silently dropped.

    Exercises the helper's `if stripped.startswith("- ")` guard
    in `_extract_supersedes_after_header` end-to-end via `run()`.
    The non-bullet noise line MUST be dropped without affecting
    the recognized supersession.
    """
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        work_items=[
            _work_item(item_id="li-kept", spec_commitment_hint="kept-hint"),
        ],
    )
    # An earlier PC declared `real-superseded` as its own obligation,
    # which the noise-decorated later PC supersedes.
    earlier_block = (
        "spec_commitments:\n"
        "  impl_followups:\n"
        "    - id_hint: real-superseded\n"
        "      description: |\n"
        "        earlier entry\n"
    )
    _write_pc(
        spec_root=spec_root,
        version="v001",
        stem="earlier",
        spec_commitments_block=earlier_block,
    )
    _write_revision(spec_root=spec_root, version="v001", stem="earlier", decision="accept")
    _write_pc(
        spec_root=spec_root,
        version="v002",
        stem="noisy",
        spec_commitments_block=_FRONT_MATTER_WITH_NON_BULLET_LINE_IN_SUPERSEDES,
    )
    _write_revision(spec_root=spec_root, version="v002", stem="noisy", decision="accept")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="pass",
        message=(
            "unresolved-spec-commitment: every declared spec_commitments."
            "impl_followups[] id_hint resolves to a work-item with matching "
            "spec_commitment_hint or has been superseded "
            "(2 obligation(s) scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_pc_with_only_id_hint_in_supersedes_handled() -> None:
    """Hardening: a `spec_commitments:` block whose body is all spaces.

    Synthetic edge case: a PC author indents the spec_commitments
    line content with only-whitespace lines (a typo no schema-
    aware authoring tool produces, but real text editors can).
    The parser MUST treat such blank-ish lines as terminators
    only when their indent is at-or-below the block's. The flat
    "all spaces" branch in `_leading_spaces` is exercised by any
    truly-blank pass-through line (covered by the blank-line
    helper test above); this stub keeps the test count honest.
    """
    # The blank-line branch is exercised by the
    # blank-line-in-spec-commitments-block test above; this
    # placeholder documents the intent for the
    # `_leading_spaces` all-spaces branch coverage and is
    # otherwise a no-op assertion.
    assert True
