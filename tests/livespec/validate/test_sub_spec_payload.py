"""Tests for livespec.validate.sub_spec_payload.

Per style doc §"Skill layout — `validate/`": validator at
`validate/sub_spec_payload.py` exports
`validate_sub_spec_payload(payload, schema)` returning
`Result[SubSpecPayload, ValidationError]`.

Per v018 Q1 + v020 Q2: each sub-spec payload carries a
`template_name` marker (the sub-spec template's directory name)
and a `files` array (path/content pairs for atomic emission
alongside the main spec tree).
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
from returns.result import Failure, Success

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.sub_spec_payload import SubSpecPayload
from livespec.types import TemplateName
from livespec.validate import sub_spec_payload

__all__: list[str] = []

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude-plugin"
    / "scripts"
    / "livespec"
    / "schemas"
    / "sub_spec_payload.schema.json"
)


def test_validate_sub_spec_payload_returns_success_for_valid_payload() -> None:
    """A well-formed payload validates to Success(SubSpecPayload)."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "template_name": "livespec",
        "files": [
            {"path": "SPECIFICATION/templates/livespec/spec.md", "content": "# Spec\n"},
        ],
    }
    result = sub_spec_payload.validate_sub_spec_payload(payload=payload, schema=schema)
    expected = SubSpecPayload(
        template_name=TemplateName("livespec"),
        files=[
            {"path": "SPECIFICATION/templates/livespec/spec.md", "content": "# Spec\n"},
        ],
    )
    assert result == Success(expected)


def test_validate_sub_spec_payload_returns_failure_on_missing_required_field() -> None:
    """A payload missing `files` returns Failure(ValidationError)."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {"template_name": "livespec"}
    result = sub_spec_payload.validate_sub_spec_payload(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "sub_spec_payload:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_sub_spec_payload_carries_multiple_files() -> None:
    """A payload with multiple files preserves the list order and content."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "template_name": "minimal",
        "files": [
            {"path": "SPECIFICATION/templates/minimal/README.md", "content": "r\n"},
            {"path": "SPECIFICATION/templates/minimal/spec.md", "content": "s\n"},
        ],
    }
    result = sub_spec_payload.validate_sub_spec_payload(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert len(value.files) == 2
            assert value.files[0]["path"].endswith("README.md")
            assert value.files[1]["path"].endswith("spec.md")
        case _:
            msg = f"expected Success(SubSpecPayload), got {result}"
            raise AssertionError(msg)


@given(template_name=st.text(min_size=1, max_size=40))
def test_validate_sub_spec_payload_round_trips_template_name(*, template_name: str) -> None:
    """For arbitrary template_name text, the success path preserves it verbatim."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "template_name": template_name,
        "files": [{"path": "p", "content": "c"}],
    }
    result = sub_spec_payload.validate_sub_spec_payload(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.template_name == template_name
        case _:
            msg = f"expected Success(SubSpecPayload), got {result}"
            raise AssertionError(msg)
