"""Tests for livespec.validate.livespec_config.

Per style doc §"Skill layout — `validate/`": validator at
`validate/livespec_config.py` exports
`validate_livespec_config(payload, schema)` returning
`Result[LivespecConfig, ValidationError]`. The schema marks
all fields optional with documented defaults; an empty `{}`
payload validates and produces the all-defaults dataclass.
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
from returns.result import Failure, Success

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.livespec_config import LivespecConfig
from livespec.types import TemplateName
from livespec.validate import livespec_config

__all__: list[str] = []

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude-plugin"
    / "scripts"
    / "livespec"
    / "schemas"
    / "livespec_config.schema.json"
)


def test_validate_livespec_config_returns_success_with_defaults_for_empty_payload() -> None:
    """An empty `{}` payload validates to Success(LivespecConfig) with all schema defaults."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    result = livespec_config.validate_livespec_config(payload={}, schema=schema)
    expected = LivespecConfig(
        template=TemplateName("livespec"),
        template_format_version=1,
        post_step_skip_doctor_llm_objective_checks=False,
        post_step_skip_doctor_llm_subjective_checks=False,
        pre_step_skip_static_checks=False,
    )
    assert result == Success(expected)


def test_validate_livespec_config_returns_success_for_explicit_template() -> None:
    """An explicit `template` overrides the default."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {"template": "minimal"}
    result = livespec_config.validate_livespec_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.template == "minimal"
            assert value.template_format_version == 1  # still default
        case _:
            msg = f"expected Success(LivespecConfig), got {result}"
            raise AssertionError(msg)


def test_validate_livespec_config_returns_failure_on_unknown_field() -> None:
    """A payload with an unknown field returns Failure(ValidationError).

    Drives `additionalProperties: false`: fastjsonschema rejects
    any field not enumerated in the schema's `properties`.
    """
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {"unknown_field": "boom"}
    result = livespec_config.validate_livespec_config(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "livespec_config:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


@given(
    skip_objective=st.booleans(),
    skip_subjective=st.booleans(),
    skip_static=st.booleans(),
)
def test_validate_livespec_config_round_trips_skip_flags(
    *,
    skip_objective: bool,
    skip_subjective: bool,
    skip_static: bool,
) -> None:
    """For arbitrary skip-flag combinations, the success path preserves them verbatim."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "post_step_skip_doctor_llm_objective_checks": skip_objective,
        "post_step_skip_doctor_llm_subjective_checks": skip_subjective,
        "pre_step_skip_static_checks": skip_static,
    }
    result = livespec_config.validate_livespec_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.post_step_skip_doctor_llm_objective_checks is skip_objective
            assert value.post_step_skip_doctor_llm_subjective_checks is skip_subjective
            assert value.pre_step_skip_static_checks is skip_static
        case _:
            msg = f"expected Success(LivespecConfig), got {result}"
            raise AssertionError(msg)
