"""Tests for livespec.doctor.static.no_stalled_epic.

Per `SPECIFICATION/contracts.md` §"`no-stalled-epic`": the check
fires `fail` when an epic carries `status` in `{open, in_progress}`
AND has a non-empty `depends_on` AND every `depends_on` entry
resolves to a closed work-item / PR / branch. Empty `depends_on` is
exempt (vacuous-truth guard); unresolvable entries delegate to
`no-orphan-dependency`; closed/non-epic items are out of scope.

When the epic's depends_on contains non-local typed entries
(sibling_work_item / pull_request / branch), the check walks them
via `livespec_runtime.cross_repo.resolve_ref`. OPEN external deps
suppress fail (legitimate stall reason); CLOSED count toward
all-closed; UNKNOWN suppresses (no-orphan-dependency's domain).

Provider calls (`gh_provider.query_pull_request_state`,
`gh_provider.branch_exists_on_remote`,
`gh_provider.branch_merged_into_default`) are monkeypatched at the
module attribute level so the tests don't shell out to `gh`.

The check reads `.livespec.jsonc` to find the impl-plugin's
work-items JSONL path. v1 supports only `livespec-impl-plaintext`;
other plugins receive a `skipped` Finding.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import no_stalled_epic
from livespec.schemas.dataclasses.finding import Finding
from livespec_runtime.cross_repo.providers import github as gh_provider
from returns.io import IOSuccess

__all__: list[str] = []


_CONFIG_TEXT_WITH_MANIFEST = """// livespec config with cross_repo_targets
{
  "template": "livespec",
  "spec_root": "SPECIFICATION",
  "implementation": { "plugin": "livespec-impl-plaintext" },
  "livespec-impl-plaintext": {
    "format": "jsonl",
    "work_items_path": "work-items.jsonl"
  },
  "cross_repo_targets": {
    "runtime": { "github_url": "https://github.com/example/runtime" }
  }
}
"""


_CONFIG_TEXT = """// minimal livespec config
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


def _setup_project(*, tmp_path: Path, jsonl_lines: list[dict[str, object]]) -> tuple[Path, Path]:
    """Create a project root with .livespec.jsonc and a work-items.jsonl."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    jsonl_text = "".join(
        json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n" for record in jsonl_lines
    )
    _ = (project_root / "work-items.jsonl").write_text(jsonl_text, encoding="utf-8")
    return project_root, spec_root


def _record(
    *,
    item_id: str,
    item_type: str = "task",
    status: str = "closed",
    depends_on: list[str] | None = None,
) -> dict[str, object]:
    """Minimal work-item record with the four fields the check reads."""
    return {
        "id": item_id,
        "type": item_type,
        "status": status,
        "depends_on": list(depends_on) if depends_on is not None else [],
    }


def test_fails_when_epic_open_and_all_depends_on_closed(
    *,
    tmp_path: Path,
) -> None:
    """An epic in_progress with every depends_on closed MUST fire `fail`.

    This is the canonical case the invariant was added for — exactly
    the li-6t5 drift observed in the dogfood store.
    """
    records = [
        _record(item_id="sub-1", status="closed"),
        _record(item_id="sub-2", status="closed"),
        _record(
            item_id="epic-A",
            item_type="epic",
            status="in_progress",
            depends_on=["sub-1", "sub-2"],
        ),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="fail",
        message=(
            "no-stalled-epic: 1 epic(s) with all depends_on entries closed but epic still open/in_progress: epic-A. "
            "Close the epic with an appropriate resolution OR add fresh depends_on entries."
        ),
        path=str(project_root / "work-items.jsonl"),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_passes_when_epic_has_open_dependency(
    *,
    tmp_path: Path,
) -> None:
    """An epic with at least one OPEN dependency MUST pass — work in flight."""
    records = [
        _record(item_id="sub-1", status="closed"),
        _record(item_id="sub-2", status="open"),
        _record(
            item_id="epic-B",
            item_type="epic",
            status="open",
            depends_on=["sub-1", "sub-2"],
        ),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="pass",
        message="no-stalled-epic: no epics with all-closed depends_on detected (3 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_passes_when_epic_has_empty_depends_on(
    *,
    tmp_path: Path,
) -> None:
    """An epic with empty `depends_on` is vacuous — MUST NOT fire."""
    records = [
        _record(
            item_id="fresh-epic",
            item_type="epic",
            status="open",
            depends_on=[],
        ),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="pass",
        message="no-stalled-epic: no epics with all-closed depends_on detected (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def _setup_project_with_manifest(
    *,
    tmp_path: Path,
    jsonl_lines: list[dict[str, object]],
) -> tuple[Path, Path]:
    """Same as _setup_project but writes a config with a cross_repo_targets block."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT_WITH_MANIFEST, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    jsonl_text = "".join(
        json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n" for record in jsonl_lines
    )
    _ = (project_root / "work-items.jsonl").write_text(jsonl_text, encoding="utf-8")
    return project_root, spec_root


def test_passes_when_typed_local_dep_is_open(*, tmp_path: Path) -> None:
    """A typed-dict local dep that points at an open work-item suppresses fail."""
    records = [
        _record(item_id="sub-1", status="open"),
        _record(
            item_id="epic-G",
            item_type="epic",
            status="open",
            depends_on=[{"kind": "local", "work_item_id": "sub-1"}],
        ),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="pass",
        message="no-stalled-epic: no epics with all-closed depends_on detected (2 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_fails_when_typed_local_deps_all_closed(*, tmp_path: Path) -> None:
    """Typed-dict local deps that all point at closed work-items fire `fail`."""
    records = [
        _record(item_id="sub-1", status="closed"),
        _record(
            item_id="epic-H",
            item_type="epic",
            status="open",
            depends_on=[{"kind": "local", "work_item_id": "sub-1"}],
        ),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="fail",
        message=(
            "no-stalled-epic: 1 epic(s) with all depends_on entries closed "
            "but epic still open/in_progress: epic-H. "
            "Close the epic with an appropriate resolution OR add fresh depends_on entries."
        ),
        path=str(project_root / "work-items.jsonl"),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_passes_when_open_pr_dep_suppresses_fail(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An OPEN PR dep is a legitimate stall reason — MUST NOT fire."""
    monkeypatch.setattr(gh_provider, "query_pull_request_state", lambda **_kwargs: "OPEN")
    records = [
        _record(item_id="sub-1", status="closed"),
        _record(
            item_id="epic-I",
            item_type="epic",
            status="open",
            depends_on=[
                {"kind": "local", "work_item_id": "sub-1"},
                {"kind": "pull_request", "repo": "runtime", "number": 5},
            ],
        ),
    ]
    project_root, spec_root = _setup_project_with_manifest(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="pass",
        message="no-stalled-epic: no epics with all-closed depends_on detected (2 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_fails_when_all_deps_closed_including_merged_pr(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When a MERGED PR + closed local both resolve closed, the epic stalls."""
    monkeypatch.setattr(gh_provider, "query_pull_request_state", lambda **_kwargs: "MERGED")
    records = [
        _record(item_id="sub-1", status="closed"),
        _record(
            item_id="epic-J",
            item_type="epic",
            status="open",
            depends_on=[
                {"kind": "local", "work_item_id": "sub-1"},
                {"kind": "pull_request", "repo": "runtime", "number": 5},
            ],
        ),
    ]
    project_root, spec_root = _setup_project_with_manifest(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="fail",
        message=(
            "no-stalled-epic: 1 epic(s) with all depends_on entries closed "
            "but epic still open/in_progress: epic-J. "
            "Close the epic with an appropriate resolution OR add fresh depends_on entries."
        ),
        path=str(project_root / "work-items.jsonl"),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_passes_when_typed_dep_is_schema_malformed(*, tmp_path: Path) -> None:
    """A typed dict with no `kind` is unresolvable — suppresses fail (no-orphan-dep's domain)."""
    records = [
        _record(
            item_id="epic-K",
            item_type="epic",
            status="open",
            depends_on=[{"work_item_id": "missing-kind"}],
        ),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="pass",
        message="no-stalled-epic: no epics with all-closed depends_on detected (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_passes_when_depends_on_entry_unresolvable(
    *,
    tmp_path: Path,
) -> None:
    """Unresolvable depends_on entries delegate to no-orphan-dependency — MUST NOT fire here."""
    records = [
        _record(item_id="sub-1", status="closed"),
        _record(
            item_id="epic-C",
            item_type="epic",
            status="open",
            depends_on=["sub-1", "missing-id"],
        ),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="pass",
        message="no-stalled-epic: no epics with all-closed depends_on detected (2 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_passes_when_epic_is_closed(
    *,
    tmp_path: Path,
) -> None:
    """A closed epic is out of scope (status filter) — MUST NOT fire."""
    records = [
        _record(item_id="sub-1", status="closed"),
        _record(
            item_id="epic-D",
            item_type="epic",
            status="closed",
            depends_on=["sub-1"],
        ),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="pass",
        message="no-stalled-epic: no epics with all-closed depends_on detected (2 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_passes_when_non_epic_has_all_closed_depends_on(
    *,
    tmp_path: Path,
) -> None:
    """A non-epic task with all closed deps is out of scope (type filter) — MUST NOT fire."""
    records = [
        _record(item_id="sub-1", status="closed"),
        _record(
            item_id="task-E",
            item_type="task",
            status="open",
            depends_on=["sub-1"],
        ),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="pass",
        message="no-stalled-epic: no epics with all-closed depends_on detected (2 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_materializes_latest_record_per_id(
    *,
    tmp_path: Path,
) -> None:
    """JSONL append-only semantics: latest record per id wins.

    The historical `li-6t5` case has TWO records for the epic id —
    an open initial record AND a closed transition record. The
    materialized view is `closed`. This test confirms the check
    correctly handles the multi-record-per-id pattern.
    """
    records = [
        _record(item_id="sub-1", status="closed"),
        # epic-F initially open with dep, then later transitioned to closed
        _record(item_id="epic-F", item_type="epic", status="in_progress", depends_on=["sub-1"]),
        _record(item_id="epic-F", item_type="epic", status="closed", depends_on=["sub-1"]),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="pass",
        message="no-stalled-epic: no epics with all-closed depends_on detected (2 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_skips_when_active_plugin_unrecognized(
    *,
    tmp_path: Path,
    monkeypatch,
) -> None:
    """When the active impl-plugin is outside the v1 supported set, the check skips.

    monkeypatch.chdir(tmp_path) isolates cwd so no project artifacts
    leak into the repo per the cwd-fallback test discipline.
    """
    monkeypatch.chdir(tmp_path)
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_text = (
        "{\n"
        '  "template": "livespec",\n'
        '  "implementation": { "plugin": "livespec-impl-beads" }\n'
        "}\n"
    )
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="skipped",
        message=(
            "no-stalled-epic: active impl-plugin is not in the v1 supported set "
            "(livespec-impl-plaintext); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_skips_when_livespec_jsonc_missing(
    *,
    tmp_path: Path,
) -> None:
    """When .livespec.jsonc is missing, the railway lashes back into a skipped Finding."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="skipped",
        message="no-stalled-epic: precondition not met (PreconditionError); check skipped",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_passes_when_work_items_jsonl_not_yet_present(
    *,
    tmp_path: Path,
) -> None:
    """When the work-items.jsonl path is configured but the file doesn't exist yet, the check passes.

    A fresh project before any work-items exist has nothing to check;
    the absence of the file is normal (the impl-plugin creates it on
    first append).
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    # No work-items.jsonl on disk.
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    work_items_path = project_root / "work-items.jsonl"
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="pass",
        message=(
            f"no-stalled-epic: work-items store at {work_items_path} not present yet; "
            "no epics to check"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_tolerates_malformed_jsonl_lines(
    *,
    tmp_path: Path,
) -> None:
    """Malformed JSONL lines (blank, non-JSON, non-object, no `id`) are skipped silently.

    Exercises the four defensive `continue` branches in `_materialize_records`:
    blank line, parse failure, non-object value, missing-id record.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    jsonl_text = (
        # 1. Blank line — exercises empty-stripped continue
        "\n"
        # 2. Malformed JSON (unterminated string)
        '{"id": "bad-line\n'
        # 3. Valid JSON but non-object (array at root)
        "[1, 2, 3]\n"
        # 4. Object but no `id` field
        '{"type": "task", "status": "open"}\n'
        # 5. Valid record (so the rest of the check has something to scan)
        '{"id": "task-only", "type": "task", "status": "closed", "depends_on": []}\n'
    )
    _ = (project_root / "work-items.jsonl").write_text(jsonl_text, encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="pass",
        message="no-stalled-epic: no epics with all-closed depends_on detected (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_passes_when_depends_on_entry_is_not_a_string(
    *,
    tmp_path: Path,
) -> None:
    """Non-string depends_on entries are treated as unresolvable — MUST NOT fire."""
    records = [
        _record(item_id="sub-1", status="closed"),
        # The "epic" depends_on a non-string (number). The check's _find_stalled_epics
        # walks the list looking for type errors and bails to all_closed=False.
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    # Append a malformed-deps epic record (raw json dump bypasses _record's typing).
    epic_record_text = (
        '{"id":"epic-malformed","type":"epic","status":"open","depends_on":["sub-1",42]}\n'
    )
    with (project_root / "work-items.jsonl").open("a", encoding="utf-8") as fh:
        _ = fh.write(epic_record_text)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="pass",
        message="no-stalled-epic: no epics with all-closed depends_on detected (2 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_uses_default_work_items_path_when_plugin_section_missing(
    *,
    tmp_path: Path,
) -> None:
    """When the impl-plugin section is absent or work_items_path is non-string, falls back to default.

    Covers the two `_resolve_work_items_path` fallback branches: missing
    plugin section, and a non-string `work_items_path`.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_text = (
        "// minimal config — no plugin section, no work_items_path override\n"
        "{\n"
        '  "template": "livespec",\n'
        '  "implementation": { "plugin": "livespec-impl-plaintext" }\n'
        "}\n"
    )
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    # Default path `work-items.jsonl` at project root with a benign record.
    _ = (project_root / "work-items.jsonl").write_text(
        '{"id":"x","type":"task","status":"closed","depends_on":[]}\n',
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="pass",
        message="no-stalled-epic: no epics with all-closed depends_on detected (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_skips_when_implementation_section_absent(
    *,
    tmp_path: Path,
) -> None:
    """When `.livespec.jsonc` has no `implementation` key, the check skips.

    Exercises the `not isinstance(impl_section, dict)` guard (None case).
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_text = '{\n  "template": "livespec"\n}\n'
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="skipped",
        message=(
            "no-stalled-epic: active impl-plugin is not in the v1 supported set "
            "(livespec-impl-plaintext); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_skips_when_plugin_name_is_not_string(
    *,
    tmp_path: Path,
) -> None:
    """When `implementation.plugin` is a non-string value, the check skips.

    Exercises the `not isinstance(plugin_name, str)` half of the
    plugin-resolution guard.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_text = "{\n" '  "template": "livespec",\n' '  "implementation": { "plugin": 42 }\n' "}\n"
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="skipped",
        message=(
            "no-stalled-epic: active impl-plugin is not in the v1 supported set "
            "(livespec-impl-plaintext); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_falls_back_to_default_path_when_work_items_path_is_not_string(
    *,
    tmp_path: Path,
) -> None:
    """Non-string `work_items_path` falls back to the default rather than crashing."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_text = (
        "{\n"
        '  "template": "livespec",\n'
        '  "implementation": { "plugin": "livespec-impl-plaintext" },\n'
        '  "livespec-impl-plaintext": { "work_items_path": 42 }\n'
        "}\n"
    )
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = (project_root / "work-items.jsonl").write_text(
        '{"id":"only","type":"task","status":"closed","depends_on":[]}\n',
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="pass",
        message="no-stalled-epic: no epics with all-closed depends_on detected (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_skips_when_livespec_jsonc_root_is_not_object(
    *,
    tmp_path: Path,
) -> None:
    """When .livespec.jsonc parses to a non-object (e.g., a JSON array at root), the check skips."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text("[1, 2, 3]\n", encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="skipped",
        message="no-stalled-epic: .livespec.jsonc root is not an object; check skipped",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)
