"""Tests for livespec.validate.template_config."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import livespec.schemas
from hypothesis import HealthCheck, given, settings
from hypothesis_jsonschema import from_schema
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.template_config import TemplateConfig
from livespec.validate.template_config import make_validator
from returns.result import Failure, Success

if TYPE_CHECKING:
    from livespec.io.fastjsonschema_facade import Validator

__all__: list[str] = []


_SCHEMA_PATH = Path(livespec.schemas.__file__).parent / "template_config.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_minimal_payload_yields_documented_defaults(
    *,
    template_config_validator: Validator,
) -> None:
    """Only `template_format_version` is required; rest take schema defaults."""
    validator = make_validator(fast_validator=template_config_validator)
    result = validator(payload={"template_format_version": 1})
    assert isinstance(result, Success)
    cfg = result.unwrap()
    assert isinstance(cfg, TemplateConfig)
    assert cfg.template_format_version == 1
    assert str(cfg.spec_root) == "SPECIFICATION/"
    assert cfg.doctor_static_check_modules == []
    assert cfg.doctor_llm_objective_checks_prompt is None
    assert cfg.doctor_llm_subjective_checks_prompt is None


def test_full_payload(*, template_config_validator: Validator) -> None:
    validator = make_validator(fast_validator=template_config_validator)
    payload: dict[str, Any] = {
        "template_format_version": 1,
        "spec_root": ".",
        "doctor_static_check_modules": ["checks/extra.py"],
        "doctor_llm_objective_checks_prompt": "prompts/obj.md",
        "doctor_llm_subjective_checks_prompt": "prompts/subj.md",
    }
    result = validator(payload=payload)
    assert isinstance(result, Success)
    cfg = result.unwrap()
    assert cfg.doctor_static_check_modules == ["checks/extra.py"]
    assert cfg.doctor_llm_objective_checks_prompt == "prompts/obj.md"
    assert cfg.doctor_llm_subjective_checks_prompt == "prompts/subj.md"


def test_template_format_version_enum_rejects_unsupported_value(
    *,
    template_config_validator: Validator,
) -> None:
    """v1 livespec supports only template_format_version=1."""
    validator = make_validator(fast_validator=template_config_validator)
    result = validator(payload={"template_format_version": 2})
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), ValidationError)


def test_missing_required_template_format_version_returns_failure(
    *,
    template_config_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=template_config_validator)
    result = validator(payload={"spec_root": "."})
    assert isinstance(result, Failure)


@given(payload=from_schema(_SCHEMA))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
def test_pbt_schema_conforming_payloads_always_succeed(
    *,
    payload: dict[str, Any],
    template_config_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=template_config_validator)
    result = validator(payload=payload)
    assert isinstance(result, Success)
    cfg = result.unwrap()
    assert isinstance(cfg, TemplateConfig)
    assert cfg.template_format_version == payload["template_format_version"]
