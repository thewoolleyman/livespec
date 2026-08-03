"""Tests for spec-governance JSONC config edits."""

from __future__ import annotations

from pathlib import Path

from livespec.spec_governance.config_edit import write_config_value

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

    config_path.write_text(
        '{"spec_governance": {"critique_mode": "batch"}, "template": "x"}',
        encoding="utf-8",
    )
    assert isinstance(
        write_config_value(project_root=tmp_path, key="propose_change_mode", value="batch"),
        Path,
    )
    assert '"template": "x"' in config_path.read_text(encoding="utf-8")


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
