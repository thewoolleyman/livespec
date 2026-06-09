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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="fail",
        message=(
            "no-duplicate-gap-id: 1 gap-id(s) claimed by multiple open work-items: "
            "gap-1: [a, b]. Consolidate or close the duplicates."
        ),
        path=_provider_path(project_root=project_root),
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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


def test_passes_when_provider_emits_empty_array(*, tmp_path: Path) -> None:
    """An empty work-items store passes vacuously."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=[])
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="pass",
        message=(
            "no-duplicate-gap-id: every open work-item's gap-id is unique " "(0 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_when_provider_unset(*, tmp_path: Path) -> None:
    """No configured provider (work_items_provider is None) yields a skipped Finding."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root, work_items_provider=None)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="skipped",
        message=(
            "no-duplicate-gap-id: no live work-item provider configured "
            "(set LIVESPEC_IMPL_LIST_WORK_ITEMS to the active impl-plugin's "
            "list-work-items wrapper to enforce); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_when_provider_unreachable(*, tmp_path: Path) -> None:
    """A provider that exits nonzero is a connection failure → skipped, not fail."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    wrapper = project_root / _WRAPPER_NAME
    _ = wrapper.write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root, work_items_provider=wrapper)
    result = no_duplicate_gap_id.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-duplicate-gap-id",
        status="skipped",
        message=(
            "no-duplicate-gap-id: work-item store unreachable " "(wrapper exited 1); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)
