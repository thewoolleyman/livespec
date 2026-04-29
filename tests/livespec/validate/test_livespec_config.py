"""Tests for livespec.validate.livespec_config."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import livespec.schemas
from hypothesis import HealthCheck, given, settings
from hypothesis_jsonschema import from_schema
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.livespec_config import LivespecConfig
from livespec.validate.livespec_config import make_validator
from returns.result import Failure, Success

if TYPE_CHECKING:
    from livespec.io.fastjsonschema_facade import Validator

__all__: list[str] = []


_FORMAT_VERSION_OVERRIDE = 2


_SCHEMA_PATH = Path(livespec.schemas.__file__).parent / "livespec_config.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_empty_payload_yields_documented_defaults(
    *,
    livespec_config_validator: Validator,
) -> None:
    """No fields set → as-if-missing-file state."""
    validator = make_validator(fast_validator=livespec_config_validator)
    result = validator(payload={})
    assert isinstance(result, Success)
    cfg = result.unwrap()
    assert isinstance(cfg, LivespecConfig)
    assert cfg.template == "livespec"
    assert cfg.template_format_version == 1
    assert cfg.post_step_skip_doctor_llm_objective_checks is False
    assert cfg.post_step_skip_doctor_llm_subjective_checks is False
    assert cfg.pre_step_skip_static_checks is False


def test_full_payload(*, livespec_config_validator: Validator) -> None:
    validator = make_validator(fast_validator=livespec_config_validator)
    payload: dict[str, Any] = {
        "template": "minimal",
        "template_format_version": _FORMAT_VERSION_OVERRIDE,
        "post_step_skip_doctor_llm_objective_checks": True,
        "post_step_skip_doctor_llm_subjective_checks": True,
        "pre_step_skip_static_checks": True,
    }
    result = validator(payload=payload)
    assert isinstance(result, Success)
    cfg = result.unwrap()
    assert cfg.template == "minimal"
    assert cfg.template_format_version == _FORMAT_VERSION_OVERRIDE
    assert cfg.post_step_skip_doctor_llm_objective_checks is True


def test_unknown_field_returns_failure(*, livespec_config_validator: Validator) -> None:
    """`additionalProperties: false` rejects any unrecognized field."""
    validator = make_validator(fast_validator=livespec_config_validator)
    result = validator(payload={"unrecognized": "value"})
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), ValidationError)


def test_template_format_version_negative_returns_failure(
    *,
    livespec_config_validator: Validator,
) -> None:
    """`minimum: 1` rejects 0 / negative integers."""
    validator = make_validator(fast_validator=livespec_config_validator)
    result = validator(payload={"template_format_version": 0})
    assert isinstance(result, Failure)


@given(payload=from_schema(_SCHEMA))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=25)
def test_pbt_schema_conforming_payloads_always_succeed(
    *,
    payload: dict[str, Any],
    livespec_config_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=livespec_config_validator)
    result = validator(payload=payload)
    assert isinstance(result, Success)
    assert isinstance(result.unwrap(), LivespecConfig)
