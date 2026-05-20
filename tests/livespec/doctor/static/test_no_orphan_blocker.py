"""Tests for livespec.doctor.static.no_orphan_blocker.

Per `SPECIFICATION/contracts.md` §"`no-orphan-blocker`": every work-item's
declared `depends_on` (the schema's `blocked_by` equivalent) MUST resolve
to an existing work-item id in the same impl-plugin's store. The check
fires `fail` when a `depends_on` reference targets a non-existent id.
Closed blockers are NOT orphans; only missing-from-store ids fire.
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import no_orphan_blocker
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
    status: str = "closed",
    depends_on: list[str] | None = None,
) -> dict[str, object]:
    """Minimal work-item record."""
    return {
        "id": item_id,
        "type": "task",
        "status": status,
        "depends_on": list(depends_on) if depends_on is not None else [],
    }


def test_fails_when_depends_on_references_missing_id(
    *,
    tmp_path: Path,
) -> None:
    """A depends_on entry that doesn't resolve to a work-item MUST fire `fail`."""
    records = [
        _record(item_id="a", status="open", depends_on=["missing-1"]),
        _record(item_id="b", status="open", depends_on=["a", "missing-2"]),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_orphan_blocker.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-blocker",
        status="fail",
        message=(
            "no-orphan-blocker: 2 unresolved depends_on reference(s): "
            "a→missing-1, b→missing-2. Either add the missing work-item(s) or "
            "remove the stale depends_on entry."
        ),
        path=str(project_root / "work-items.jsonl"),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_all_depends_on_resolve(
    *,
    tmp_path: Path,
) -> None:
    """When every depends_on resolves, the check passes — closed deps are fine."""
    records = [
        _record(item_id="a", status="closed"),
        _record(item_id="b", status="open", depends_on=["a"]),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_orphan_blocker.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-blocker",
        status="pass",
        message=(
            "no-orphan-blocker: every depends_on reference resolves to an existing "
            "work-item (2 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_all_depends_on_empty(
    *,
    tmp_path: Path,
) -> None:
    """When no work-item has depends_on, the check passes vacuously."""
    records = [
        _record(item_id="a", status="open"),
        _record(item_id="b", status="open"),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_orphan_blocker.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-blocker",
        status="pass",
        message=(
            "no-orphan-blocker: every depends_on reference resolves to an existing "
            "work-item (2 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_non_string_depends_on_entries(
    *,
    tmp_path: Path,
) -> None:
    """A non-string depends_on entry is ignored (schema validation isn't this check's job)."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    raw_jsonl = (
        '{"id":"a","type":"task","status":"open","depends_on":["b",42]}\n'
        '{"id":"b","type":"task","status":"closed","depends_on":[]}\n'
    )
    _ = (project_root / "work-items.jsonl").write_text(raw_jsonl, encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_orphan_blocker.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-blocker",
        status="pass",
        message=(
            "no-orphan-blocker: every depends_on reference resolves to an existing "
            "work-item (2 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_when_depends_on_is_not_a_list(
    *,
    tmp_path: Path,
) -> None:
    """When `depends_on` is malformed (not a list), the check ignores the record."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    raw_jsonl = '{"id":"a","type":"task","status":"open","depends_on":"not-a-list"}\n'
    _ = (project_root / "work-items.jsonl").write_text(raw_jsonl, encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_orphan_blocker.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-blocker",
        status="pass",
        message=(
            "no-orphan-blocker: every depends_on reference resolves to an existing "
            "work-item (1 work-items scanned)"
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
    """When the active impl-plugin is outside the v1 supported set, the check skips."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_text = '{\n  "implementation": { "plugin": "livespec-impl-beads" }\n}\n'
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_orphan_blocker.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-blocker",
        status="skipped",
        message=(
            "no-orphan-blocker: active impl-plugin is not in the v1 supported set "
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
    """When .livespec.jsonc is missing, the railway lashes back into a skipped Finding."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_orphan_blocker.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-blocker",
        status="skipped",
        message="no-orphan-blocker: precondition not met (PreconditionError); check skipped",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_work_items_jsonl_not_yet_present(
    *,
    tmp_path: Path,
) -> None:
    """When the work-items.jsonl is configured but the file doesn't exist yet, check passes."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_orphan_blocker.run(ctx=ctx)
    work_items_path = project_root / "work-items.jsonl"
    expected = Finding(
        check_id="doctor-no-orphan-blocker",
        status="pass",
        message=(
            f"no-orphan-blocker: work-items store at {work_items_path} not present yet; "
            "no blockers to check"
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
    """When .livespec.jsonc root parses to a non-object, the check skips."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text("[1,2,3]\n", encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_orphan_blocker.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-blocker",
        status="skipped",
        message="no-orphan-blocker: .livespec.jsonc root is not an object; check skipped",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_when_implementation_section_absent(
    *,
    tmp_path: Path,
) -> None:
    """When `implementation` key is absent, the check skips."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text('{"template":"livespec"}\n', encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_orphan_blocker.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-blocker",
        status="skipped",
        message=(
            "no-orphan-blocker: active impl-plugin is not in the v1 supported set "
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
    """Non-string `implementation.plugin` value triggers skip."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"implementation":{"plugin":42}}\n', encoding="utf-8"
    )
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_orphan_blocker.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-blocker",
        status="skipped",
        message=(
            "no-orphan-blocker: active impl-plugin is not in the v1 supported set "
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
    """Falls back to default `work-items.jsonl` when plugin section is absent."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"implementation":{"plugin":"livespec-impl-plaintext"}}\n',
        encoding="utf-8",
    )
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = (project_root / "work-items.jsonl").write_text(
        '{"id":"a","type":"task","status":"closed","depends_on":[]}\n',
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_orphan_blocker.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-blocker",
        status="pass",
        message=(
            "no-orphan-blocker: every depends_on reference resolves to an existing "
            "work-item (1 work-items scanned)"
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
        '{"id":"a","type":"task","status":"closed","depends_on":[]}\n',
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_orphan_blocker.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-blocker",
        status="pass",
        message=(
            "no-orphan-blocker: every depends_on reference resolves to an existing "
            "work-item (1 work-items scanned)"
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
        '{"id": "bad-line\n'  # malformed JSON
        "[1, 2, 3]\n"  # non-object
        '{"type": "task", "status": "open"}\n'  # no id
        '{"id":"x","type":"task","status":"closed","depends_on":[]}\n'  # valid
    )
    _ = (project_root / "work-items.jsonl").write_text(jsonl_text, encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_orphan_blocker.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-blocker",
        status="pass",
        message=(
            "no-orphan-blocker: every depends_on reference resolves to an existing "
            "work-item (1 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)
