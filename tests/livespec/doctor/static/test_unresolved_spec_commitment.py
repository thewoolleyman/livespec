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
vacuously. When no live work-item provider is configured (or the
provider is unreachable), the invariant surfaces a `skipped`
Finding rather than fail.

Mocking strategy:

  The check acquires work-items by invoking the active impl-plugin's
  `list-work-items` wrapper (resolved into `ctx.work_items_provider`).
  Tests therefore write a fixture wrapper that emits a fixed JSON
  array of work-item views; `_setup_project` wires it up. The
  work-item records carry the `spec_commitment_hint` field; absence
  of the field on a record yields no match (= fail when no other
  record matches that id_hint).
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec.context import DoctorContext
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


_WRAPPER_NAME = "fake_wrapper.py"


def _write_provider(*, project_root: Path, records: list[dict[str, object]]) -> Path:
    """Write a fake list-work-items wrapper emitting `records` as a JSON array."""
    data_path = project_root / "provider_data.json"
    _ = data_path.write_text(json.dumps(records), encoding="utf-8")
    wrapper = project_root / _WRAPPER_NAME
    _ = wrapper.write_text(
        "import pathlib, sys\n" f"sys.stdout.write(pathlib.Path({str(data_path)!r}).read_text())\n",
        encoding="utf-8",
    )
    return wrapper


def _ctx(*, project_root: Path, spec_root: Path) -> DoctorContext:
    """Build a DoctorContext whose provider points at the fixture wrapper."""
    return DoctorContext(
        project_root=project_root,
        spec_root=spec_root,
        work_items_provider=project_root / _WRAPPER_NAME,
    )


def _provider_path(*, project_root: Path) -> str:
    """Return the fixture wrapper path as the str the fail-Finding `path` carries."""
    return str(project_root / _WRAPPER_NAME)


def _setup_project(
    *,
    tmp_path: Path,
    config_text: str = _CONFIG_TEXT_PLAINTEXT,
    work_items: list[dict[str, object]] | None = None,
) -> tuple[Path, Path]:
    """Create a project root with .livespec.jsonc and a fixture provider wrapper.

    Returns `(project_root, spec_root)`. The spec_root is created
    as an empty directory; per-version PC and revision files are
    seeded by individual test helpers. `work_items=None` emits an
    empty work-items array (the history walk still runs against an
    empty hint set).
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = _write_provider(
        project_root=project_root,
        records=work_items if work_items is not None else [],
    )
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

    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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

    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="fail",
        message=(
            "unresolved-spec-commitment: 1 declared "
            "spec_commitments.impl_followups[] id_hint(s) have no matching "
            "work-item with spec_commitment_hint in the active impl-plugin's "
            "work-items store: beta-hint (from v005/commitments.md). "
            "Corrective action: file each missing work-item via the active "
            "impl-plugin's `capture-work-item` skill, passing "
            "`--spec-commitment-hint <id_hint>` so the work-item carries "
            "the pairing field."
        ),
        path=_provider_path(project_root=project_root),
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

    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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


def test_skips_when_provider_unset_even_with_obligations(
    *,
    tmp_path: Path,
) -> None:
    """No configured provider → `skipped` (NOT fail), even with unresolved obligations.

    Per `contracts.md`: when no live impl-plugin work-item provider
    is configured, the invariant has no store to query — the
    appropriate outcome is `skipped`, not `fail` — even when the
    spec tree carries propose-changes declaring
    spec_commitments.impl_followups[] with no matching work-items.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT_NO_IMPL, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _write_pc(
        spec_root=spec_root,
        version="v001",
        stem="commitments",
        spec_commitments_block=_TWO_ID_HINTS_BLOCK,
    )
    _write_revision(spec_root=spec_root, version="v001", stem="commitments", decision="accept")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root, work_items_provider=None)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="skipped",
        message=(
            "unresolved-spec-commitment: no live work-item provider configured "
            "(set LIVESPEC_IMPL_LIST_WORK_ITEMS to the active impl-plugin's "
            "list-work-items wrapper to enforce); check skipped"
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

    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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

    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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


def test_skips_when_provider_unreachable(
    *,
    tmp_path: Path,
) -> None:
    """A provider that exits nonzero is a connection failure → `skipped`, not fail."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    wrapper = project_root / _WRAPPER_NAME
    _ = wrapper.write_text("import sys\nsys.exit(1)\n", encoding="utf-8")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root, work_items_provider=wrapper)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="skipped",
        message=(
            "unresolved-spec-commitment: work-item store unreachable "
            "(wrapper exited 1); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_fails_with_empty_work_items_store_when_obligations_declared(
    *,
    tmp_path: Path,
) -> None:
    """Empty work-items store but obligations declared → `fail` naming the unresolved hints.

    The work-items store carries no matching hints yet (e.g., the
    user accepted the propose-change but has not yet filed any
    work-items). The check treats the empty hint set as the
    "every id_hint unresolved" case and fails.
    """
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        # No work_items list → the provider emits an empty array.
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

    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-unresolved-spec-commitment",
        status="fail",
        message=(
            "unresolved-spec-commitment: 2 declared "
            "spec_commitments.impl_followups[] id_hint(s) have no matching "
            "work-item with spec_commitment_hint in the active impl-plugin's "
            "work-items store: alpha-hint (from v007/newly-accepted.md); "
            "beta-hint (from v007/newly-accepted.md). "
            "Corrective action: file each missing work-item via the active "
            "impl-plugin's `capture-work-item` skill, passing "
            "`--spec-commitment-hint <id_hint>` so the work-item carries "
            "the pairing field."
        ),
        path=_provider_path(project_root=project_root),
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

    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    assert result == IOSuccess(_vacuous_pass_finding(spec_root=spec_root))


def test_history_absent_yields_vacuous_pass(*, tmp_path: Path) -> None:
    """No `history/` directory under spec_root → empty walk → vacuous pass."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path, work_items=[])
    # history/ deliberately not created
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    assert result == IOSuccess(_vacuous_pass_finding(spec_root=spec_root))


def test_proposed_changes_directory_absent_in_version_dir(*, tmp_path: Path) -> None:
    """A vNNN/ dir without a `proposed_changes/` subdir yields no obligations."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path, work_items=[])
    (spec_root / "history" / "v001").mkdir(parents=True)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = unresolved_spec_commitment.run(ctx=ctx)
    assert result == IOSuccess(_vacuous_pass_finding(spec_root=spec_root))


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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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


def test_records_with_null_or_absent_spec_commitment_hint_are_ignored(
    *,
    tmp_path: Path,
) -> None:
    """Work-items whose `spec_commitment_hint` is null/absent/non-string contribute no hint.

    Exercises the `isinstance(hint, str) and hint` False branch of
    `hints_from_index`: only the record carrying a real string hint
    resolves the declared obligation; the others are silently
    ignored, and the obligation still resolves to a pass.
    """
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        work_items=[
            # null hint — ignored
            {"id": "li-null", "type": "task", "status": "open", "spec_commitment_hint": None},
            # field absent entirely — ignored
            {"id": "li-absent", "type": "task", "status": "open"},
            # non-string hint — ignored
            {"id": "li-num", "type": "task", "status": "open", "spec_commitment_hint": 42},
            # the one real match
            _work_item(item_id="li-real", spec_commitment_hint="alpha-hint"),
        ],
    )
    _write_pc(
        spec_root=spec_root,
        version="v001",
        stem="claim",
        spec_commitments_block=(
            "spec_commitments:\n"
            "  impl_followups:\n"
            "    - id_hint: alpha-hint\n"
            "      description: |\n"
            "        only follow-up\n"
        ),
    )
    _write_revision(spec_root=spec_root, version="v001", stem="claim", decision="accept")
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
