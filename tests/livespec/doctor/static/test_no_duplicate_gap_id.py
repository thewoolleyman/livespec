"""Tests for livespec.doctor.static.no_duplicate_gap_id.

Per `SPECIFICATION/contracts.md` §"`no-duplicate-gap-id`": no two OPEN
work-items MAY share the same `gap_id`. Closed items sharing a gap_id
with an open item are exempt; the historical sharing is fine.
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import no_duplicate_gap_id
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


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
    """Create a project root with .livespec.jsonc and work-items.jsonl."""
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
    status: str = "closed",
    gap_id: str | None = None,
) -> dict[str, object]:
    """Minimal work-item record with id, status, gap_id."""
    return {
        "id": item_id,
        "type": "task",
        "status": status,
        "depends_on": [],
        "gap_id": gap_id,
    }


def test_fails_when_two_open_items_share_gap_id(
    *,
    tmp_path: Path,
) -> None:
    """Two open items with the same gap_id MUST fire `fail`."""
    records = [
        _record(item_id="a", status="open", gap_id="gap-1"),
        _record(item_id="b", status="open", gap_id="gap-1"),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="fail",
        message=(
            "no-duplicate-gap-id: 1 gap-id(s) claimed by multiple open work-items: "
            "gap-1: [a, b]. Consolidate or close the duplicates."
        ),
        path=str(project_root / "work-items.jsonl"),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_closed_item_shares_gap_id_with_open(
    *,
    tmp_path: Path,
) -> None:
    """A closed item sharing a gap_id with an open item is exempt — historical sharing OK."""
    records = [
        _record(item_id="a", status="closed", gap_id="gap-1"),
        _record(item_id="b", status="open", gap_id="gap-1"),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="pass",
        message=(
            "no-duplicate-gap-id: every open work-item's gap-id is unique " "(2 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_no_gap_ids(
    *,
    tmp_path: Path,
) -> None:
    """When no work-items carry a gap_id, the check passes vacuously."""
    records = [
        _record(item_id="a", status="open"),
        _record(item_id="b", status="open"),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="pass",
        message=(
            "no-duplicate-gap-id: every open work-item's gap-id is unique " "(2 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_open_items_have_distinct_gap_ids(
    *,
    tmp_path: Path,
) -> None:
    """Each open item with a unique gap_id is fine."""
    records = [
        _record(item_id="a", status="open", gap_id="gap-1"),
        _record(item_id="b", status="open", gap_id="gap-2"),
        _record(item_id="c", status="in_progress", gap_id="gap-3"),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="pass",
        message=(
            "no-duplicate-gap-id: every open work-item's gap-id is unique " "(3 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_non_string_gap_id_values(
    *,
    tmp_path: Path,
) -> None:
    """Non-string `gap_id` value (e.g., null) is treated as absent."""
    records = [
        _record(item_id="a", status="open", gap_id=None),
        _record(item_id="b", status="open", gap_id=None),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="pass",
        message=(
            "no-duplicate-gap-id: every open work-item's gap-id is unique " "(2 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_when_active_plugin_unrecognized(
    *,
    tmp_path: Path,
) -> None:
    """Unsupported impl-plugin triggers skip."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"implementation":{"plugin":"livespec-impl-beads"}}\n', encoding="utf-8"
    )
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="skipped",
        message=(
            "no-duplicate-gap-id: active impl-plugin is not in the v1 supported set "
            "(livespec-impl-plaintext); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_when_livespec_jsonc_missing(
    *,
    tmp_path: Path,
) -> None:
    """Missing .livespec.jsonc triggers skip via lash recovery."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="skipped",
        message="no-duplicate-gap-id: precondition not met (PreconditionError); check skipped",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_work_items_jsonl_not_yet_present(
    *,
    tmp_path: Path,
) -> None:
    """Configured but absent work-items.jsonl is normal — pass."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    work_items_path = project_root / "work-items.jsonl"
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="pass",
        message=(
            f"no-duplicate-gap-id: work-items store at {work_items_path} not present yet; "
            "no gap-ids to check"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_when_livespec_jsonc_root_is_not_object(
    *,
    tmp_path: Path,
) -> None:
    """Non-object root in .livespec.jsonc triggers skip."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text("[1,2,3]\n", encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="skipped",
        message="no-duplicate-gap-id: .livespec.jsonc root is not an object; check skipped",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_when_implementation_section_absent(
    *,
    tmp_path: Path,
) -> None:
    """Missing `implementation` key triggers skip."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text('{"template":"livespec"}\n', encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="skipped",
        message=(
            "no-duplicate-gap-id: active impl-plugin is not in the v1 supported set "
            "(livespec-impl-plaintext); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_when_plugin_name_is_not_string(
    *,
    tmp_path: Path,
) -> None:
    """Non-string plugin name triggers skip."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"implementation":{"plugin":42}}\n', encoding="utf-8"
    )
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="skipped",
        message=(
            "no-duplicate-gap-id: active impl-plugin is not in the v1 supported set "
            "(livespec-impl-plaintext); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_uses_default_work_items_path_when_section_absent(
    *,
    tmp_path: Path,
) -> None:
    """Falls back to default when plugin section is absent."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"implementation":{"plugin":"livespec-impl-plaintext"}}\n',
        encoding="utf-8",
    )
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = (project_root / "work-items.jsonl").write_text(
        '{"id":"a","type":"task","status":"open","depends_on":[],"gap_id":null}\n',
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="pass",
        message=(
            "no-duplicate-gap-id: every open work-item's gap-id is unique " "(1 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_falls_back_when_work_items_path_is_not_string(
    *,
    tmp_path: Path,
) -> None:
    """Non-string `work_items_path` falls back to default."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"implementation":{"plugin":"livespec-impl-plaintext"},'
        '"livespec-impl-plaintext":{"work_items_path":42}}\n',
        encoding="utf-8",
    )
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = (project_root / "work-items.jsonl").write_text(
        '{"id":"a","type":"task","status":"open","depends_on":[],"gap_id":null}\n',
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="pass",
        message=(
            "no-duplicate-gap-id: every open work-item's gap-id is unique " "(1 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_tolerates_malformed_jsonl_lines(
    *,
    tmp_path: Path,
) -> None:
    """Malformed JSONL lines are silently skipped."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    jsonl_text = (
        "\n"
        '{"id": "bad-line\n'
        "[1, 2]\n"
        '{"type":"task"}\n'
        '{"id":"x","type":"task","status":"closed","depends_on":[],"gap_id":null}\n'
    )
    _ = (project_root / "work-items.jsonl").write_text(jsonl_text, encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="pass",
        message=(
            "no-duplicate-gap-id: every open work-item's gap-id is unique " "(1 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)
