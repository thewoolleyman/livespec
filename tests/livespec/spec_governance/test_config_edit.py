"""Tests for spec-governance JSONC config edits."""

from __future__ import annotations

import json
from pathlib import Path

from livespec.spec_governance.config_edit import write_config_map_entry, write_config_value

__all__: list[str] = []


def test_config_edit_handles_malformed_existing_blocks(*, tmp_path: Path) -> None:
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text('{"spec_governance": [}', encoding="utf-8")

    assert isinstance(
        write_config_value(project_root=tmp_path, key="critique_mode", value="batch"), str
    )


def test_config_edit_handles_unterminated_and_comma_existing_blocks(*, tmp_path: Path) -> None:
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text(
        '{"spec_governance": {"x": {"unterminated": true}',
        encoding="utf-8",
    )
    assert isinstance(
        write_config_value(project_root=tmp_path, key="critique_mode", value="batch"), str
    )

    config_path.write_text('{"spec_governance": {"x": true,}}', encoding="utf-8")
    assert isinstance(
        write_config_value(project_root=tmp_path, key="critique_mode", value="batch"), Path
    )

    config_path.write_text(
        '{"spec_governance": {"critique_mode": "batch"}, "template": "x"}',
        encoding="utf-8",
    )
    assert isinstance(
        write_config_value(project_root=tmp_path, key="propose_change_mode", value="batch"),
        Path,
    )
    updated = config_path.read_text(encoding="utf-8")
    assert '"template": "x"' in updated
    assert json.loads(updated) == {
        "spec_governance": {
            "critique_mode": "batch",
            "propose_change_mode": "batch",
        },
        "template": "x",
    }


def test_config_edit_renders_nested_maps_without_extra_commas(*, tmp_path: Path) -> None:
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text('{"template": "x"}', encoding="utf-8")

    assert isinstance(
        write_config_map_entry(
            project_root=tmp_path,
            map_key="doctor_dispositions",
            entry_key="doctor-static-x",
            value="defer",
        ),
        Path,
    )

    updated = config_path.read_text(encoding="utf-8")
    assert ",," not in updated
    assert "{," not in updated
    assert json.loads(updated) == {
        "template": "x",
        "spec_governance": {
            "doctor_dispositions": {
                "doctor-static-x": "defer",
            },
        },
    }


def test_config_edit_insertion_variants(*, tmp_path: Path) -> None:
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text("{", encoding="utf-8")
    assert isinstance(
        write_config_value(project_root=tmp_path, key="critique_mode", value="batch"), Path
    )

    config_path.write_text("{   ", encoding="utf-8")
    assert isinstance(
        write_config_value(project_root=tmp_path, key="critique_mode", value="batch"), Path
    )

    config_path.write_text("{\n", encoding="utf-8")
    assert isinstance(
        write_config_value(project_root=tmp_path, key="critique_mode", value="batch"), Path
    )

    config_path.write_text("// leading comment\n{", encoding="utf-8")
    assert isinstance(
        write_config_value(project_root=tmp_path, key="critique_mode", value="batch"), Path
    )


def test_config_edit_matching_brace_handles_escaped_quotes(*, tmp_path: Path) -> None:
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text(
        '{"spec_governance": {"ratification_reviewer_model": "a\\\\\\"b"}}',
        encoding="utf-8",
    )

    assert isinstance(
        write_config_value(project_root=tmp_path, key="critique_mode", value="batch"), Path
    )
