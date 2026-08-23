"""Tests for spec-governance JSONC config edits."""

from __future__ import annotations

import json
from pathlib import Path

from livespec.errors import ValidationError
from livespec.spec_governance.config_edit import write_config_map_entry, write_config_value
from returns.io import IOFailure, IOSuccess
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def test_config_edit_handles_malformed_existing_blocks(*, tmp_path: Path) -> None:
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text('{"spec_governance": [}', encoding="utf-8")

    outcome = write_config_value(project_root=tmp_path, key="critique_mode", value="batch")
    assert isinstance(outcome, IOFailure)
    assert isinstance(unsafe_perform_io(outcome.failure()), ValidationError)


def test_config_edit_handles_unterminated_and_comma_existing_blocks(*, tmp_path: Path) -> None:
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text(
        '{"spec_governance": {"x": {"unterminated": true}',
        encoding="utf-8",
    )
    assert isinstance(
        write_config_value(project_root=tmp_path, key="critique_mode", value="batch"),
        IOFailure,
    )

    config_path.write_text('{"spec_governance": {"x": true,}}', encoding="utf-8")
    assert isinstance(
        write_config_value(project_root=tmp_path, key="critique_mode", value="batch"),
        IOFailure,
    )
    assert config_path.read_text(encoding="utf-8") == '{"spec_governance": {"x": true,}}'

    config_path.write_text(
        '{"spec_governance": {"critique_mode": "batch"}, "template": "x"}',
        encoding="utf-8",
    )
    assert isinstance(
        write_config_value(project_root=tmp_path, key="propose_change_mode", value="batch"),
        IOSuccess,
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


def test_config_edit_preserves_sibling_keys_in_a_commented_block(*, tmp_path: Path) -> None:
    """A `//` comment in the block MUST NOT cost the block its other keys.

    `SPECIFICATION/contracts.md` requires the control CLI to "atomically
    replace only the selected config or front-matter value while preserving
    unrelated JSONC keys/comments". A comment is the whole reason the file is
    `.jsonc`, and the write half used to parse the block with raw `json.loads`
    — so a commented block raised `JSONDecodeError`, was swallowed to `{}`, and
    every sibling key was overwritten by the one key being written, while the
    call returned the SUCCESS spelling.
    """
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text(
        "{\n"
        '  "spec_governance": {\n'
        "    // maintainer direction: batch mode is deliberate\n"
        '    "propose_change_mode": "batch",\n'
        '    "ratification_review": "auto-spawn"\n'
        "  }\n"
        "}\n",
        encoding="utf-8",
    )

    outcome = write_config_value(
        project_root=tmp_path, key="in_flight_alignment", value="default-align"
    )

    # The PRESERVATION assertion comes first deliberately: it is the one that
    # carries the proof. Asserting the return type first would let this test go
    # red for the type change alone and never exercise the data loss.
    assert json.loads(config_path.read_text(encoding="utf-8")) == {
        "spec_governance": {
            "propose_change_mode": "batch",
            "ratification_review": "auto-spawn",
            "in_flight_alignment": "default-align",
        },
    }
    assert isinstance(outcome, IOSuccess)


def test_config_map_entry_refuses_an_unreadable_block_too(*, tmp_path: Path) -> None:
    """The MAP writer refuses on the same terms as the scalar writer.

    Both halves read through `_extract_block`, so a block that will not parse must
    refuse in both. Pinning only the scalar writer would leave the map writer free
    to keep overwriting a config it could not read.
    """
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text(
        '{"spec_governance": {"doctor_dispositions": {"a": "b",}}}',
        encoding="utf-8",
    )

    outcome = write_config_map_entry(
        project_root=tmp_path,
        map_key="doctor_dispositions",
        entry_key="doctor-anchor-reference-resolution",
        value="accept",
    )

    assert isinstance(outcome, IOFailure)
    assert isinstance(unsafe_perform_io(outcome.failure()), ValidationError)
    assert config_path.read_text(encoding="utf-8") == (
        '{"spec_governance": {"doctor_dispositions": {"a": "b",}}}'
    )


def test_config_edit_refuses_a_block_that_is_not_an_object(*, tmp_path: Path) -> None:
    """A parseable block of the WRONG SHAPE is a failure, not an empty default."""
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text('{"spec_governance": ["not", "an", "object"]}', encoding="utf-8")

    outcome = write_config_value(project_root=tmp_path, key="critique_mode", value="batch")

    assert isinstance(outcome, IOFailure)
    assert isinstance(unsafe_perform_io(outcome.failure()), ValidationError)


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
        IOSuccess,
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
        write_config_value(project_root=tmp_path, key="critique_mode", value="batch"),
        IOSuccess,
    )

    config_path.write_text("{   ", encoding="utf-8")
    assert isinstance(
        write_config_value(project_root=tmp_path, key="critique_mode", value="batch"),
        IOSuccess,
    )

    config_path.write_text("{\n", encoding="utf-8")
    assert isinstance(
        write_config_value(project_root=tmp_path, key="critique_mode", value="batch"),
        IOSuccess,
    )

    config_path.write_text("// leading comment\n{", encoding="utf-8")
    assert isinstance(
        write_config_value(project_root=tmp_path, key="critique_mode", value="batch"),
        IOSuccess,
    )


def test_config_edit_matching_brace_handles_escaped_quotes(*, tmp_path: Path) -> None:
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text(
        '{"spec_governance": {"ratification_reviewer_model": "a\\\\\\"b"}}',
        encoding="utf-8",
    )

    assert isinstance(
        write_config_value(project_root=tmp_path, key="critique_mode", value="batch"),
        IOSuccess,
    )


def test_config_edit_surgically_clears_only_scalar_member(*, tmp_path: Path) -> None:
    config_path = tmp_path / ".livespec.jsonc"
    config_path.write_text(
        '{\n  "spec_governance": {\n    "revise_decision_mode": "delegated"\n  }\n}\n',
        encoding="utf-8",
    )

    result = write_config_value(
        project_root=tmp_path,
        key="revise_decision_mode",
        value=None,
    )

    assert isinstance(result, IOSuccess)
    assert isinstance(unsafe_perform_io(result.unwrap()), Path)
    assert json.loads(config_path.read_text(encoding="utf-8")) == {"spec_governance": {}}
