"""Tests for livespec.doctor.static.depends_on_ref_wellformedness.

Per `SPECIFICATION/contracts.md` §"`depends_on-ref-wellformedness`":
for every open work-item's depends_on array, the invariant enforces:

1. Discriminator present — every entry MUST have a `kind` field
   whose value is one of `local`, `sibling_work_item`,
   `pull_request`, `branch`.
2. Per-kind required fields present.
3. `repo` resolves to a configured target in `cross_repo_targets`.

Closed records are out of scope (legacy entries tolerated).
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import depends_on_ref_wellformedness
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


def _setup_project(
    *,
    tmp_path: Path,
    jsonl_lines: list[dict[str, object]],
    config_text: str = _CONFIG_TEXT,
) -> tuple[Path, Path]:
    """Create a project root with .livespec.jsonc and a work-items.jsonl."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
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
    status: str = "open",
    depends_on: list[object] | None = None,
) -> dict[str, object]:
    """Minimal work-item record."""
    return {
        "id": item_id,
        "type": "task",
        "status": status,
        "depends_on": list(depends_on) if depends_on is not None else [],
    }


def test_passes_when_all_open_entries_wellformed(*, tmp_path: Path) -> None:
    """Open records with well-formed typed entries (local + non-local) pass."""
    records = [
        _record(
            item_id="a",
            status="open",
            depends_on=[
                {"kind": "local", "work_item_id": "li-x"},
                {"kind": "pull_request", "repo": "runtime", "number": 5},
            ],
        ),
    ]
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        jsonl_lines=records,
        config_text=_CONFIG_TEXT_WITH_MANIFEST,
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="pass",
        message=(
            "depends_on-ref-wellformedness: every open work-item's depends_on "
            "entries are well-formed (1 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_fails_when_entry_is_bare_string(*, tmp_path: Path) -> None:
    """A bare-string entry on an open record fires fail (non-typed-dict form)."""
    records = [_record(item_id="a", status="open", depends_on=["li-x"])]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="fail",
        message=(
            "depends_on-ref-wellformedness: 1 ill-formed depends_on entry(ies): "
            "a#0: entry is not a typed object (got str); v072 requires typed-dict form."
        ),
        path=str(project_root / "work-items.jsonl"),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_fails_when_kind_missing(*, tmp_path: Path) -> None:
    """A typed dict missing the `kind` discriminator fires fail."""
    records = [_record(item_id="a", status="open", depends_on=[{"work_item_id": "li-x"}])]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="fail",
        message=(
            "depends_on-ref-wellformedness: 1 ill-formed depends_on entry(ies): "
            "a#0: cross_repo depends_on entry: depends_on entry missing required field 'kind'."
        ),
        path=str(project_root / "work-items.jsonl"),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_fails_when_kind_unknown(*, tmp_path: Path) -> None:
    """A typed dict with an unknown `kind` value fires fail."""
    records = [
        _record(
            item_id="a",
            status="open",
            depends_on=[{"kind": "bogus", "work_item_id": "li-x"}],
        )
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="fail",
        message=(
            "depends_on-ref-wellformedness: 1 ill-formed depends_on entry(ies): "
            "a#0: cross_repo depends_on entry: depends_on entry has unknown kind 'bogus'; "
            "expected one of: local, sibling_work_item, pull_request, branch."
        ),
        path=str(project_root / "work-items.jsonl"),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_fails_when_per_kind_field_missing(*, tmp_path: Path) -> None:
    """A typed pull_request without `number` fires fail."""
    records = [
        _record(
            item_id="a",
            status="open",
            depends_on=[{"kind": "pull_request", "repo": "runtime"}],
        )
    ]
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        jsonl_lines=records,
        config_text=_CONFIG_TEXT_WITH_MANIFEST,
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="fail",
        message=(
            "depends_on-ref-wellformedness: 1 ill-formed depends_on entry(ies): "
            "a#0: cross_repo depends_on entry: depends_on entry of kind 'pull_request' "
            "missing required field 'number'."
        ),
        path=str(project_root / "work-items.jsonl"),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_fails_when_repo_not_in_manifest(*, tmp_path: Path) -> None:
    """An entry whose `repo` is absent from cross_repo_targets fires fail."""
    records = [
        _record(
            item_id="a",
            status="open",
            depends_on=[{"kind": "branch", "repo": "missing", "name": "feat/x"}],
        )
    ]
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        jsonl_lines=records,
        config_text=_CONFIG_TEXT_WITH_MANIFEST,
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="fail",
        message=(
            "depends_on-ref-wellformedness: 1 ill-formed depends_on entry(ies): "
            "a#0: repo 'missing' not in .livespec.jsonc's `cross_repo_targets` block."
        ),
        path=str(project_root / "work-items.jsonl"),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_closed_record_has_malformed_entry(*, tmp_path: Path) -> None:
    """Closed records are out of scope — malformed entries tolerated."""
    records = [
        _record(item_id="a", status="closed", depends_on=["bare-string", {"bad": "shape"}]),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="pass",
        message=(
            "depends_on-ref-wellformedness: every open work-item's depends_on "
            "entries are well-formed (1 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_open_record_has_empty_depends_on(*, tmp_path: Path) -> None:
    """Open records with empty depends_on pass vacuously."""
    records = [_record(item_id="a", status="open", depends_on=[])]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="pass",
        message=(
            "depends_on-ref-wellformedness: every open work-item's depends_on "
            "entries are well-formed (1 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_depends_on_is_not_a_list(*, tmp_path: Path) -> None:
    """When `depends_on` is malformed (not a list), the record is silently skipped."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    raw_jsonl = '{"id":"a","type":"task","status":"open","depends_on":"not-a-list"}\n'
    _ = (project_root / "work-items.jsonl").write_text(raw_jsonl, encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="pass",
        message=(
            "depends_on-ref-wellformedness: every open work-item's depends_on "
            "entries are well-formed (1 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_when_active_plugin_unrecognized(*, tmp_path: Path) -> None:
    """When the active impl-plugin is outside the v1 supported set, the check skips."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_text = '{\n  "implementation": { "plugin": "livespec-impl-beads" }\n}\n'
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="skipped",
        message=(
            "depends_on-ref-wellformedness: active impl-plugin is not in the v1 "
            "supported set (livespec-impl-plaintext); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_when_livespec_jsonc_missing(*, tmp_path: Path) -> None:
    """When .livespec.jsonc is missing, the railway lashes back into a skipped Finding."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="skipped",
        message=(
            "depends_on-ref-wellformedness: precondition not met "
            "(PreconditionError); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_when_livespec_jsonc_root_is_not_object(*, tmp_path: Path) -> None:
    """When .livespec.jsonc root parses to a non-object, the check skips."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text("[1, 2, 3]\n", encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="skipped",
        message=(
            "depends_on-ref-wellformedness: .livespec.jsonc root is not an " "object; check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_uses_default_work_items_path_when_plugin_section_missing(*, tmp_path: Path) -> None:
    """Plugin section absent — falls back to default `work-items.jsonl` at project root."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"template":"livespec","implementation":{"plugin":"livespec-impl-plaintext"}}\n',
        encoding="utf-8",
    )
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = (project_root / "work-items.jsonl").write_text(
        '{"id":"a","type":"task","status":"closed","depends_on":[]}\n',
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="pass",
        message=(
            "depends_on-ref-wellformedness: every open work-item's depends_on "
            "entries are well-formed (1 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_falls_back_when_work_items_path_is_not_string(*, tmp_path: Path) -> None:
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
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="pass",
        message=(
            "depends_on-ref-wellformedness: every open work-item's depends_on "
            "entries are well-formed (1 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_tolerates_malformed_jsonl_lines(*, tmp_path: Path) -> None:
    """Malformed JSONL lines (blank, non-JSON, non-object, no `id`) are skipped silently."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    jsonl_text = (
        "\n"
        '{"id": "bad-line\n'
        "[1, 2, 3]\n"
        '{"type": "task", "status": "open"}\n'
        '{"id":"x","type":"task","status":"closed","depends_on":[]}\n'
    )
    _ = (project_root / "work-items.jsonl").write_text(jsonl_text, encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="pass",
        message=(
            "depends_on-ref-wellformedness: every open work-item's depends_on "
            "entries are well-formed (1 work-items scanned)"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_work_items_jsonl_not_yet_present(*, tmp_path: Path) -> None:
    """When work-items.jsonl is configured but absent, the check passes."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    work_items_path = project_root / "work-items.jsonl"
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="pass",
        message=(
            f"depends_on-ref-wellformedness: work-items store at "
            f"{work_items_path} not present yet; no entries to check"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)
