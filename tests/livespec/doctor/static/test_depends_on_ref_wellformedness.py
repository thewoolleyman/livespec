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
    jsonl_lines: list[dict[str, object]],
    config_text: str = _CONFIG_TEXT,
) -> tuple[Path, Path]:
    """Create a project root with .livespec.jsonc and a fixture provider wrapper."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = _write_provider(project_root=project_root, records=jsonl_lines)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="fail",
        message=(
            "depends_on-ref-wellformedness: 1 ill-formed depends_on entry(ies): "
            "a#0: entry is not a typed object (got str); v072 requires typed-dict form."
        ),
        path=_provider_path(project_root=project_root),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_fails_when_kind_missing(*, tmp_path: Path) -> None:
    """A typed dict missing the `kind` discriminator fires fail."""
    records = [_record(item_id="a", status="open", depends_on=[{"work_item_id": "li-x"}])]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="fail",
        message=(
            "depends_on-ref-wellformedness: 1 ill-formed depends_on entry(ies): "
            "a#0: cross_repo depends_on entry: depends_on entry missing required field 'kind'."
        ),
        path=_provider_path(project_root=project_root),
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="fail",
        message=(
            "depends_on-ref-wellformedness: 1 ill-formed depends_on entry(ies): "
            "a#0: cross_repo depends_on entry: depends_on entry has unknown kind 'bogus'; "
            "expected one of: local, sibling_work_item, pull_request, branch."
        ),
        path=_provider_path(project_root=project_root),
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="fail",
        message=(
            "depends_on-ref-wellformedness: 1 ill-formed depends_on entry(ies): "
            "a#0: cross_repo depends_on entry: depends_on entry of kind 'pull_request' "
            "missing required field 'number'."
        ),
        path=_provider_path(project_root=project_root),
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="fail",
        message=(
            "depends_on-ref-wellformedness: 1 ill-formed depends_on entry(ies): "
            "a#0: repo 'missing' not in .livespec.jsonc's `cross_repo_targets` block."
        ),
        path=_provider_path(project_root=project_root),
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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
    _ = _write_provider(
        project_root=project_root,
        records=[{"id": "a", "type": "task", "status": "open", "depends_on": "not-a-list"}],
    )
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
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


def test_passes_when_provider_emits_empty_array(*, tmp_path: Path) -> None:
    """An empty work-items store passes vacuously (no entries to check)."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=[])
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="pass",
        message=(
            "depends_on-ref-wellformedness: every open work-item's depends_on "
            "entries are well-formed (0 work-items scanned)"
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
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="skipped",
        message=(
            "depends_on-ref-wellformedness: no live work-item provider configured "
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
    result = depends_on_ref_wellformedness.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-depends_on-ref-wellformedness",
        status="skipped",
        message=(
            "depends_on-ref-wellformedness: work-item store unreachable "
            "(wrapper exited 1); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)
