"""Tests for livespec.doctor.static.no_stale_gap_tied.

Per `SPECIFICATION/contracts.md` §"`no-stale-gap-tied`": the check
fires `warn` (not `fail`) when an open gap-tied work-item's gap-id
is no longer present in a fresh impl-plugin gap-detection run. The
implementation shortcuts in v1 by replicating the gap-detection
logic from `livespec-impl-plaintext`'s `detect-impl-gaps` skill.
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


_CONFIG_UNSUPPORTED_PLUGIN = """{
  "template": "livespec",
  "spec_root": "SPECIFICATION",
  "implementation": { "plugin": "livespec-impl-other" }
}
"""


_CONFIG_NO_IMPL_SECTION = """{
  "template": "livespec",
  "spec_root": "SPECIFICATION"
}
"""


def _derive_gap_id(*, spec_file: str, heading_path: str, rule_text: str) -> str:
    payload = f"{spec_file}\x1f{heading_path}\x1f{rule_text}".encode()
    digest = hashlib.sha256(payload).digest()
    suffix = b32encode(digest).decode("ascii").rstrip("=").lower()[:8]
    return f"gap-{suffix}"


def _setup_project(
    *,
    tmp_path: Path,
    jsonl_lines: list[dict[str, object]] | None,
    spec_files: dict[str, str] | None = None,
    config_text: str = _CONFIG_TEXT,
) -> tuple[Path, Path]:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    if spec_files is not None:
        for name, content in spec_files.items():
            _ = (spec_root / name).write_text(content, encoding="utf-8")
    if jsonl_lines is not None:
        jsonl_text = "".join(
            json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n"
            for record in jsonl_lines
        )
        _ = (project_root / "work-items.jsonl").write_text(jsonl_text, encoding="utf-8")
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
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
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
        path=str(project_root / "work-items.jsonl"),
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
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
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
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path, jsonl_lines=records, spec_files={"spec.md": "# T\n"}
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
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


def test_passes_when_work_items_store_absent(*, tmp_path: Path) -> None:
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path, jsonl_lines=None, spec_files={"spec.md": "# T\n"}
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="pass",
        message=(
            f"no-stale-gap-tied: work-items store at {project_root / 'work-items.jsonl'} "
            "not present yet; no gap-tied items to check"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skipped_when_impl_plugin_unsupported(*, tmp_path: Path) -> None:
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        jsonl_lines=None,
        config_text=_CONFIG_UNSUPPORTED_PLUGIN,
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="skipped",
        message=(
            "no-stale-gap-tied: active impl-plugin is not in the v1 supported set "
            "(livespec-impl-plaintext); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skipped_when_implementation_section_missing(*, tmp_path: Path) -> None:
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        jsonl_lines=None,
        spec_files={"spec.md": "# T\n"},
        config_text=_CONFIG_NO_IMPL_SECTION,
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="skipped",
        message=(
            "no-stale-gap-tied: active impl-plugin is not in the v1 supported set "
            "(livespec-impl-plaintext); check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skipped_when_livespec_jsonc_missing(*, tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="skipped",
        message="no-stale-gap-tied: precondition not met (PreconditionError); check skipped",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skipped_when_livespec_jsonc_root_is_not_object(*, tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text("[1, 2, 3]", encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="skipped",
        message="no-stale-gap-tied: .livespec.jsonc root is not an object; check skipped",
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
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
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
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
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
        path=str(project_root / "work-items.jsonl"),
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_detection_skips_code_fences(*, tmp_path: Path) -> None:
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        jsonl_lines=None,
        spec_files={
            "spec.md": (
                "# T\n\n"
                "Live rule MUST exist.\n\n"
                "```python\n"
                "# this MUST be excluded\n"
                "```\n\n"
                "After fence: SHOULD pass.\n"
            )
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="pass",
        message=(
            f"no-stale-gap-tied: work-items store at {project_root / 'work-items.jsonl'} "
            "not present yet; no gap-tied items to check"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skipped_when_jsonc_parse_fails(*, tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text("this is not jsonc", encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="skipped",
        message="no-stale-gap-tied: precondition not met (ValidationError); check skipped",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_detection_traverses_headings_and_code_fences_when_evaluated(*, tmp_path: Path) -> None:
    """End-to-end test exercising _detect_gap_ids and _push_heading branches.

    Requires both a work-items store (with at least one open gap-tied item)
    AND a spec with multi-level headings + code fences to exercise the
    full detection path.
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
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
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
        path=str(project_root / "work-items.jsonl"),
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
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    assert isinstance(result, IOSuccess)


def test_uses_default_path_when_plugin_section_missing(*, tmp_path: Path) -> None:
    """Config has supported plugin but no plugin-specific section.

    Exercises the `isinstance(plugin_section, dict)` False branch.
    """
    config_text = """{
      "implementation": { "plugin": "livespec-impl-plaintext" }
    }
    """
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        jsonl_lines=None,
        spec_files={"spec.md": "# T\n"},
        config_text=config_text,
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="pass",
        message=(
            f"no-stale-gap-tied: work-items store at {project_root / 'work-items.jsonl'} "
            "not present yet; no gap-tied items to check"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_uses_default_path_when_work_items_path_not_string(*, tmp_path: Path) -> None:
    """Config has plugin section but work_items_path is wrong type.

    Exercises the `isinstance(candidate, str)` False branch.
    """
    config_text = """{
      "implementation": { "plugin": "livespec-impl-plaintext" },
      "livespec-impl-plaintext": {
        "work_items_path": 42
      }
    }
    """
    project_root, spec_root = _setup_project(
        tmp_path=tmp_path,
        jsonl_lines=None,
        spec_files={"spec.md": "# T\n"},
        config_text=config_text,
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = no_stale_gap_tied.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-no-stale-gap-tied",
        status="pass",
        message=(
            f"no-stale-gap-tied: work-items store at {project_root / 'work-items.jsonl'} "
            "not present yet; no gap-tied items to check"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_jsonl_skips_blank_lines_and_non_object_lines(*, tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _ = (project_root / ".livespec.jsonc").write_text(_CONFIG_TEXT, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = (spec_root / "spec.md").write_text("# T\n", encoding="utf-8")
    bad_object = json.dumps({"origin": "gap-tied", "status": "open", "gap_id": "gap-x"})
    good_record = json.dumps({"id": "li-real", "origin": "freeform", "status": "open"})
    raw_text = "".join(
        [
            "\n",
            "not-json-at-all\n",
            json.dumps([1, 2, 3]) + "\n",
            bad_object + "\n",
            good_record + "\n",
        ]
    )
    _ = (project_root / "work-items.jsonl").write_text(raw_text, encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
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
