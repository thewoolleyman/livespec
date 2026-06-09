"""Tests for livespec.doctor.static.no_orphan_dependency.

Per `SPECIFICATION/contracts.md` §"`no-orphan-dependency`": every
work-item's typed `depends_on` entries MUST resolve cleanly. For
`kind == "local"` the check fails when the referenced `work_item_id`
is absent from the store; non-local kinds (sibling_work_item,
pull_request, branch) defer to
`livespec_runtime.cross_repo.resolve_ref` and fire `fail` ONLY when
the runtime returns `unknown` AND the entry's `repo` is configured
in `cross_repo_targets`.

Legacy bare-string entries are tolerated for closed records (treated
as implicit local lookups); open records with bare-string entries
fire `fail` because v072 requires the typed form.

Provider calls (`gh_provider.query_pull_request_state`,
`gh_provider.branch_exists_on_remote`,
`gh_provider.branch_merged_into_default`) are monkeypatched at the
module attribute level so the tests don't shell out to `gh`.
`time.sleep` is monkeypatched in retry-exhaustion tests so they
don't burn real wall-clock backoff.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import no_orphan_dependency
from livespec.schemas.dataclasses.finding import Finding
from livespec_runtime.cross_repo.providers import github as gh_provider
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


def _raise_runtime_error(*_args: Any, **_kwargs: Any) -> Any:
    raise RuntimeError("simulated gh failure")


_WRAPPER_NAME = "fake_wrapper.py"


def _write_provider(*, project_root: Path, records: list[dict[str, object]]) -> Path:
    """Write a fake list-work-items wrapper emitting `records` as a JSON array.

    The check acquires work-items by running this wrapper as a
    subprocess and parsing its top-level JSON array (per
    `_work_items_provider.py`). The wrapper reads a sibling
    `provider_data.json` and prints it verbatim so the array content
    is fixture-driven.
    """
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
    depends_on: list[object] | None = None,
) -> dict[str, object]:
    """Minimal work-item record."""
    return {
        "id": item_id,
        "type": "task",
        "status": status,
        "depends_on": list(depends_on) if depends_on is not None else [],
    }


def _local(work_item_id: str) -> dict[str, str]:
    """Build a typed LocalDependency dict."""
    return {"kind": "local", "work_item_id": work_item_id}


def test_fails_when_typed_local_references_missing_id(*, tmp_path: Path) -> None:
    """A typed local depends_on entry that doesn't resolve fires `fail`."""
    records = [
        _record(item_id="a", status="open", depends_on=[_local("missing-1")]),
        _record(item_id="b", status="open", depends_on=[_local("a"), _local("missing-2")]),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="fail",
        message=(
            "no-orphan-dependency: 2 unresolved depends_on reference(s): "
            "a→missing-1 (kind=local), b→missing-2 (kind=local). "
            "Either add the missing work-item(s) or remove the stale depends_on entry."
        ),
        path=_provider_path(project_root=project_root),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_all_typed_local_resolve(*, tmp_path: Path) -> None:
    """When every typed local resolves, the check passes — closed deps are fine."""
    records = [
        _record(item_id="a", status="closed"),
        _record(item_id="b", status="open", depends_on=[_local("a")]),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (2 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_all_depends_on_empty(*, tmp_path: Path) -> None:
    """When no work-item has depends_on, the check passes vacuously."""
    records = [
        _record(item_id="a", status="open"),
        _record(item_id="b", status="open"),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (2 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_open_record_with_bare_string_fires_fail(*, tmp_path: Path) -> None:
    """An open record with a legacy bare-string entry fires `fail` (data-migration pending)."""
    records = [
        _record(item_id="a", status="open", depends_on=["b"]),
        _record(item_id="b", status="closed"),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="fail",
        message=(
            "no-orphan-dependency: 1 unresolved depends_on reference(s): "
            "a→b (kind=bare-string (data-migration pending)). "
            "Either add the missing work-item(s) or remove the stale depends_on entry."
        ),
        path=_provider_path(project_root=project_root),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_closed_record_with_bare_string_resolving_passes(*, tmp_path: Path) -> None:
    """Closed records with bare-string entries are tolerated when the target exists."""
    records = [
        _record(item_id="a", status="closed", depends_on=["b"]),
        _record(item_id="b", status="closed"),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (2 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_closed_record_with_bare_string_missing_target_still_fails(*, tmp_path: Path) -> None:
    """Closed records with bare-string entries pointing to missing ids still fire fail."""
    records = [
        _record(item_id="a", status="closed", depends_on=["missing"]),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="fail",
        message=(
            "no-orphan-dependency: 1 unresolved depends_on reference(s): "
            "a→missing (kind=local-legacy). "
            "Either add the missing work-item(s) or remove the stale depends_on entry."
        ),
        path=_provider_path(project_root=project_root),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def _setup_project_with_manifest(
    *,
    tmp_path: Path,
    jsonl_lines: list[dict[str, object]],
) -> tuple[Path, Path]:
    """Same as _setup_project but writes a config with a `cross_repo_targets` block."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT_WITH_MANIFEST, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = _write_provider(project_root=project_root, records=jsonl_lines)
    return project_root, spec_root


def test_pull_request_open_dependency_passes(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An open PR dependency resolves to OPEN — not an orphan (work in flight)."""
    monkeypatch.setattr(gh_provider, "query_pull_request_state", lambda **_kwargs: "OPEN")
    records = [
        _record(
            item_id="a",
            status="open",
            depends_on=[{"kind": "pull_request", "repo": "runtime", "number": 5}],
        ),
    ]
    project_root, spec_root = _setup_project_with_manifest(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_pull_request_merged_dependency_passes(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A merged PR dependency resolves to CLOSED — not an orphan (historically valid)."""
    monkeypatch.setattr(gh_provider, "query_pull_request_state", lambda **_kwargs: "MERGED")
    records = [
        _record(
            item_id="a",
            status="open",
            depends_on=[{"kind": "pull_request", "repo": "runtime", "number": 5}],
        ),
    ]
    project_root, spec_root = _setup_project_with_manifest(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_unknown_with_configured_target_fires_fail(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """UNKNOWN + repo configured in manifest fires `fail`."""
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(gh_provider, "query_pull_request_state", _raise_runtime_error)
    records = [
        _record(
            item_id="a",
            status="open",
            depends_on=[{"kind": "pull_request", "repo": "runtime", "number": 5}],
        ),
    ]
    project_root, spec_root = _setup_project_with_manifest(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="fail",
        message=(
            "no-orphan-dependency: 1 unresolved depends_on reference(s): "
            "a→runtime#PR5 (kind=pull_request (unresolved by runtime)). "
            "Either add the missing work-item(s) or remove the stale depends_on entry."
        ),
        path=_provider_path(project_root=project_root),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_unknown_with_unconfigured_target_passes(*, tmp_path: Path) -> None:
    """UNKNOWN + repo absent from manifest is NOT an orphan here (wellformedness's domain)."""
    records = [
        _record(
            item_id="a",
            status="open",
            depends_on=[{"kind": "sibling_work_item", "repo": "missing", "work_item_id": "li-x"}],
        ),
    ]
    # Use the default config WITHOUT cross_repo_targets — missing repo can't be configured.
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_branch_present_and_not_merged_passes(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A branch present on remote and not merged resolves to OPEN — not an orphan."""
    monkeypatch.setattr(gh_provider, "branch_exists_on_remote", lambda **_kwargs: True)
    monkeypatch.setattr(gh_provider, "branch_merged_into_default", lambda **_kwargs: False)
    records = [
        _record(
            item_id="a",
            status="open",
            depends_on=[{"kind": "branch", "repo": "runtime", "name": "feat/x"}],
        ),
    ]
    project_root, spec_root = _setup_project_with_manifest(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_sibling_without_lookup_unknown_fires_fail_when_configured(*, tmp_path: Path) -> None:
    """sibling_work_item with no runtime lookup → UNKNOWN; configured target → fail."""
    records = [
        _record(
            item_id="a",
            status="open",
            depends_on=[{"kind": "sibling_work_item", "repo": "runtime", "work_item_id": "li-x"}],
        ),
    ]
    project_root, spec_root = _setup_project_with_manifest(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="fail",
        message=(
            "no-orphan-dependency: 1 unresolved depends_on reference(s): "
            "a→runtime#li-x (kind=sibling_work_item (unresolved by runtime)). "
            "Either add the missing work-item(s) or remove the stale depends_on entry."
        ),
        path=_provider_path(project_root=project_root),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_branch_unknown_with_configured_target_fires_fail(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A branch entry that exhausts retries with a configured target fires `fail`."""
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(gh_provider, "branch_exists_on_remote", _raise_runtime_error)
    records = [
        _record(
            item_id="a",
            status="open",
            depends_on=[{"kind": "branch", "repo": "runtime", "name": "feat/y"}],
        ),
    ]
    project_root, spec_root = _setup_project_with_manifest(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="fail",
        message=(
            "no-orphan-dependency: 1 unresolved depends_on reference(s): "
            "a→runtime@feat/y (kind=branch (unresolved by runtime)). "
            "Either add the missing work-item(s) or remove the stale depends_on entry."
        ),
        path=_provider_path(project_root=project_root),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_malformed_cross_repo_manifest_treated_as_empty(*, tmp_path: Path) -> None:
    """A malformed cross_repo_targets block falls back to an empty manifest (wellformedness's domain)."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_text = (
        "{\n"
        '  "template": "livespec",\n'
        '  "implementation": { "plugin": "livespec-impl-plaintext" },\n'
        '  "livespec-impl-plaintext": { "work_items_path": "work-items.jsonl" },\n'
        '  "cross_repo_targets": { "runtime": { "missing": "github_url" } }\n'
        "}\n"
    )
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = _write_provider(
        project_root=project_root,
        records=[
            {
                "id": "a",
                "type": "task",
                "status": "open",
                "depends_on": [
                    {"kind": "sibling_work_item", "repo": "runtime", "work_item_id": "li-x"}
                ],
            }
        ],
    )
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    # Empty manifest → repo not in manifest → not an orphan here.
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_closed_record_with_non_local_kind_tolerated(*, tmp_path: Path) -> None:
    """Closed records with non-local kinds are tolerated (no resolver call)."""
    records = [
        _record(
            item_id="a",
            status="closed",
            depends_on=[{"kind": "pull_request", "repo": "runtime", "number": 5}],
        ),
    ]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_open_record_with_schema_error_entry_fires_fail(*, tmp_path: Path) -> None:
    """Open records with depends_on entries missing `kind` fire fail."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = _write_provider(
        project_root=project_root,
        records=[
            {"id": "a", "type": "task", "status": "open", "depends_on": [{"work_item_id": "x"}]}
        ],
    )
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="fail",
        message=(
            "no-orphan-dependency: 1 unresolved depends_on reference(s): "
            "a→{'work_item_id': 'x'} (kind=schema-error). "
            "Either add the missing work-item(s) or remove the stale depends_on entry."
        ),
        path=_provider_path(project_root=project_root),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_closed_record_with_schema_error_entry_tolerated(*, tmp_path: Path) -> None:
    """Closed records with malformed dict entries are silently tolerated."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    raw = '{"id":"a","type":"task","status":"closed","depends_on":[{"bad":"shape"}]}\n'
    _ = _write_provider(
        project_root=project_root,
        records=[json.loads(line) for line in raw.splitlines() if line.strip()],
    )
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_open_record_with_non_dict_non_string_entry_fires_fail(*, tmp_path: Path) -> None:
    """Open records with depends_on entries that are integers fire fail."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    raw = '{"id":"a","type":"task","status":"open","depends_on":[42]}\n'
    _ = _write_provider(
        project_root=project_root,
        records=[json.loads(line) for line in raw.splitlines() if line.strip()],
    )
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="fail",
        message=(
            "no-orphan-dependency: 1 unresolved depends_on reference(s): "
            "a→42 (kind=malformed (non-dict)). "
            "Either add the missing work-item(s) or remove the stale depends_on entry."
        ),
        path=_provider_path(project_root=project_root),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_closed_record_with_non_dict_non_string_entry_tolerated(*, tmp_path: Path) -> None:
    """Closed records with non-dict-non-string entries are tolerated."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    raw = '{"id":"a","type":"task","status":"closed","depends_on":[42]}\n'
    _ = _write_provider(
        project_root=project_root,
        records=[json.loads(line) for line in raw.splitlines() if line.strip()],
    )
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_ignores_record_when_depends_on_is_not_a_list(*, tmp_path: Path) -> None:
    """When `depends_on` is malformed (not a list), the check ignores the record."""
    records = [{"id": "a", "type": "task", "status": "open", "depends_on": "not-a-list"}]
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_provider_emits_empty_array(*, tmp_path: Path) -> None:
    """An empty work-items store is a clean pass (no dependencies to check)."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=[])
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (0 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_when_provider_unset(*, tmp_path: Path) -> None:
    """No configured provider (work_items_provider is None) yields a skipped Finding."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root, work_items_provider=None)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="skipped",
        message=(
            "no-orphan-dependency: no live work-item provider configured "
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
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    wrapper = project_root / _WRAPPER_NAME
    _ = wrapper.write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root, work_items_provider=wrapper)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="skipped",
        message=(
            "no-orphan-dependency: work-item store unreachable " "(wrapper exited 1); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_manifest_empty_when_livespec_jsonc_missing(*, tmp_path: Path) -> None:
    """A missing .livespec.jsonc yields an empty manifest (best-effort) — check still runs."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    # No .livespec.jsonc on disk → load_manifest_io lashes to an empty manifest.
    _ = _write_provider(
        project_root=project_root,
        records=[_record(item_id="a", status="closed", depends_on=[])],
    )
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_manifest_empty_when_livespec_jsonc_malformed(*, tmp_path: Path) -> None:
    """Malformed .livespec.jsonc JSON yields an empty manifest (parse-failure branch)."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text('{"unterminated', encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = _write_provider(
        project_root=project_root,
        records=[_record(item_id="a", status="closed", depends_on=[])],
    )
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_manifest_empty_when_livespec_jsonc_root_not_object(*, tmp_path: Path) -> None:
    """A non-object .livespec.jsonc root yields an empty manifest (non-dict branch)."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text("[1, 2, 3]\n", encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = _write_provider(
        project_root=project_root,
        records=[_record(item_id="a", status="closed", depends_on=[])],
    )
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_orphan_dependency.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-orphan-dependency",
        status="pass",
        message="no-orphan-dependency: every depends_on reference resolves (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)
