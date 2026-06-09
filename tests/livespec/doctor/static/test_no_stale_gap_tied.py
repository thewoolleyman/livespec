"""Tests for livespec.doctor.static.no_stale_gap_tied.

Per `SPECIFICATION/contracts.md` §"`no-stale-gap-tied`": the check
fires `warn` (not `fail`) when an open gap-tied work-item's gap-id
is no longer present in a fresh impl-plugin gap-detection run. The
implementation shortcuts in v1 by replicating the gap-detection
logic from `livespec-impl-plaintext`'s `detect-impl-gaps` skill.

Work-items are acquired via the active impl-plugin's `list-work-items`
wrapper (resolved into `ctx.work_items_provider`); the fixture wrapper
emits a fixed JSON array. When no provider is configured the check
surfaces a `skipped` Finding.
"""

from __future__ import annotations

import hashlib
import json
from base64 import b32encode
from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import no_stale_gap_tied
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


def _derive_gap_id(*, spec_file: str, heading_path: str, rule_text: str) -> str:
    payload = f"{spec_file}\x1f{heading_path}\x1f{rule_text}".encode()
    digest = hashlib.sha256(payload).digest()
    suffix = b32encode(digest).decode("ascii").rstrip("=").lower()[:8]
    return f"gap-{suffix}"


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
    spec_files: dict[str, str] | None = None,
    config_text: str = _CONFIG_TEXT,
) -> tuple[Path, Path]:
    """Create a project root with .livespec.jsonc, spec files, and a fixture provider."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    if spec_files is not None:
        for name, content in spec_files.items():
            _ = (spec_root / name).write_text(content, encoding="utf-8")
    _ = _write_provider(project_root=project_root, records=jsonl_lines)
    return project_root, spec_root


def _record(
    *,
    item_id: str,
    origin: str = "gap-tied",
    status: str = "open",
    gap_id: str | None = "gap-stale123",
) -> dict[str, object]:
    return {
        "id": item_id,
        "origin": origin,
        "status": status,
        "gap_id": gap_id,
    }


def test_warns_when_open_gap_tied_item_has_stale_gap_id(*, tmp_path: Path) -> None:
    records = [_record(item_id="li-stale", gap_id="gap-nolonger")]
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        jsonl_lines=records,
        spec_files={"spec.md": "# T\n\nSome unrelated rule MUST exist.\n"},
    )
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="warn",
        message=(
            "no-stale-gap-tied: 1 open gap-tied work-item(s) whose gap-id "
            "no longer surfaces in a fresh detection run: li-stale(gap-nolonger). "
            "Close each via a non-fix disposition (spec-revised, no-longer-applicable, "
            "resolved-out-of-band, or equivalent administrative reason)."
        ),
        path=_provider_path(project_root=project_root),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_open_gap_tied_item_has_current_gap_id(*, tmp_path: Path) -> None:
    fresh_gap_id = _derive_gap_id(
        spec_file="spec.md",
        heading_path="T",
        rule_text="Readers MUST cope.",
    )
    records = [_record(item_id="li-fresh", gap_id=fresh_gap_id)]
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        jsonl_lines=records,
        spec_files={"spec.md": "# T\n\nReaders MUST cope.\n"},
    )
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="pass",
        message=(
            "no-stale-gap-tied: all 1 open gap-tied work-item(s) "
            "have gap-ids present in the current spec"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_passes_when_no_open_gap_tied_items(*, tmp_path: Path) -> None:
    records = [_record(item_id="li-closed", status="closed", gap_id="gap-anything")]
    # No spec_files: with zero open gap-tied items the detection pass never runs,
    # so the `spec_files is None` branch of _setup_project is exercised here.
    project_root, spec_root = _setup_project(tmp_path=tmp_path, jsonl_lines=records)
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="pass",
        message="no-stale-gap-tied: no open gap-tied work-items (1 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_ignores_freeform_items_and_malformed_records(*, tmp_path: Path) -> None:
    records: list[dict[str, object]] = [
        _record(item_id="li-freeform", origin="freeform", gap_id=None),
        {"origin": "gap-tied", "status": "open", "gap_id": "gap-missing-id"},
        {"id": "li-bad", "origin": "gap-tied", "status": "open", "gap_id": 42},
    ]
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path, jsonl_lines=records, spec_files={"spec.md": "# T\n"}
    )
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="pass",
        message="no-stale-gap-tied: no open gap-tied work-items (2 work-items scanned)",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_detection_excludes_proposed_changes_and_history(*, tmp_path: Path) -> None:
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        jsonl_lines=[_record(item_id="li-x", gap_id="gap-from-history")],
        spec_files={"spec.md": "# T\n\nLive rule MUST exist.\n"},
    )
    history = spec_root / "history" / "v001"
    history.mkdir(parents=True)
    _ = (history / "spec.md").write_text("# T\n\nHistorical rule MUST exist.\n")
    proposed = spec_root / "proposed_changes"
    proposed.mkdir()
    _ = (proposed / "draft.md").write_text("# T\n\nDraft rule MUST exist.\n")
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="warn",
        message=(
            "no-stale-gap-tied: 1 open gap-tied work-item(s) whose gap-id "
            "no longer surfaces in a fresh detection run: li-x(gap-from-history). "
            "Close each via a non-fix disposition (spec-revised, no-longer-applicable, "
            "resolved-out-of-band, or equivalent administrative reason)."
        ),
        path=_provider_path(project_root=project_root),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_detection_traverses_headings_and_code_fences_when_evaluated(*, tmp_path: Path) -> None:
    """End-to-end test exercising _detect_gap_ids and _push_heading branches.

    Requires both an open gap-tied work-item AND a spec with multi-level
    headings + code fences to exercise the full detection path (including
    the code-fence-skip branch).
    """
    records = [_record(item_id="li-keep", gap_id="gap-irrelevant-stale")]
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        jsonl_lines=records,
        spec_files={
            "spec.md": (
                "# H1\n\n"
                "Top-level rule MUST exist.\n\n"
                "## H2 A\n\n"
                "Section rule MUST exist.\n\n"
                "### H3\n\n"
                "Sub rule MUST exist.\n\n"
                "## H2 B\n\n"
                "Another rule SHOULD exist.\n\n"
                "```python\n"
                "# fenced rule MUST be excluded\n"
                "```\n\n"
                "After fence: SHOULD survive.\n"
            )
        },
    )
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="warn",
        message=(
            "no-stale-gap-tied: 1 open gap-tied work-item(s) whose gap-id "
            "no longer surfaces in a fresh detection run: li-keep(gap-irrelevant-stale). "
            "Close each via a non-fix disposition (spec-revised, no-longer-applicable, "
            "resolved-out-of-band, or equivalent administrative reason)."
        ),
        path=_provider_path(project_root=project_root),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_detection_handles_level_jump_headings(*, tmp_path: Path) -> None:
    """Heading level skipping H2 — exercises _push_heading's padding branch."""
    records = [_record(item_id="li-stale", gap_id="gap-zzz")]
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        jsonl_lines=records,
        spec_files={
            "spec.md": (
                "# H1\n\n" "### H3 directly\n\n" "A rule MUST exist under jumped heading.\n"
            )
        },
    )
    ctx = _ctx(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    assert isinstance(result, IOSuccess)


def test_skips_when_provider_unset(*, tmp_path: Path) -> None:
    """No configured provider (work_items_provider is None) yields a skipped Finding."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root, work_items_provider=None)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="skipped",
        message=(
            "no-stale-gap-tied: no live work-item provider configured "
            "(set LIVESPEC_IMPL_LIST_WORK_ITEMS to the active impl-plugin's "
            "list-work-items wrapper to enforce); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skips_when_provider_unreachable(*, tmp_path: Path) -> None:
    """A provider that exits nonzero is a connection failure → skipped, not warn."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    wrapper = project_root / _WRAPPER_NAME
    _ = wrapper.write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root, work_items_provider=wrapper)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="skipped",
        message=(
            "no-stale-gap-tied: work-item store unreachable " "(wrapper exited 1); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)
