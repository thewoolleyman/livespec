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


def _setup_project(*, tmp_path: Path, jsonl_lines: list[dict[str, object]]) -> tuple[Path, Path]:
    """Create a project root with .livespec.jsonc and a fixture provider wrapper."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = _write_provider(project_root=project_root, records=jsonl_lines)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="fail",
        message=(
            "no-stalled-epic: 1 epic(s) with all depends_on entries closed but epic still open/in_progress: epic-A. "
            "Close the epic with an appropriate resolution OR add fresh depends_on entries."
        ),
        path=_provider_path(project_root=project_root),
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    _ = _write_provider(project_root=project_root, records=jsonl_lines)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="fail",
        message=(
            "no-stalled-epic: 1 epic(s) with all depends_on entries closed "
            "but epic still open/in_progress: epic-H. "
            "Close the epic with an appropriate resolution OR add fresh depends_on entries."
        ),
        path=_provider_path(project_root=project_root),
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="fail",
        message=(
            "no-stalled-epic: 1 epic(s) with all depends_on entries closed "
            "but epic still open/in_progress: epic-J. "
            "Close the epic with an appropriate resolution OR add fresh depends_on entries."
        ),
        path=_provider_path(project_root=project_root),
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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


def test_passes_when_depends_on_entry_is_not_a_string(
    *,
    tmp_path: Path,
) -> None:
    """Non-string depends_on entries are treated as unresolvable — MUST NOT fire."""
    records: list[dict[str, object]] = [
        _record(item_id="sub-1", status="closed"),
        # The "epic" depends on a non-string (number) → unresolvable → not stalled.
        {
            "id": "epic-malformed",
            "type": "epic",
            "status": "open",
            "depends_on": ["sub-1", 42],
        },
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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


def test_passes_when_provider_emits_empty_array(*, tmp_path: Path) -> None:
    """An empty work-items store passes vacuously (no epics to check)."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=[])
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="pass",
        message="no-stalled-epic: no epics with all-closed depends_on detected (0 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_skips_when_provider_unset(*, tmp_path: Path) -> None:
    """No configured provider (work_items_provider is None) yields a skipped Finding."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root, work_items_provider=None)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="skipped",
        message=(
            "no-stalled-epic: no live work-item provider configured "
            "(set LIVESPEC_IMPL_LIST_WORK_ITEMS to the active impl-plugin's "
            "list-work-items wrapper to enforce); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)


def test_skips_when_provider_unreachable(*, tmp_path: Path) -> None:
    """A provider that exits nonzero is a connection failure → skipped, not fail."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    wrapper = project_root / _WRAPPER_NAME
    _ = wrapper.write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root, work_items_provider=wrapper)
    result = no_stalled_epic.run(ctx=ctx)
    expected_finding = Finding(
        check_id="doctor-no-stalled-epic",
        status="skipped",
        message=(
            "no-stalled-epic: work-item store unreachable " "(wrapper exited 1); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected_finding)
