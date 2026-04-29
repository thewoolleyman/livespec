"""Tests for livespec.validate.seed_input."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import livespec.schemas
from hypothesis import HealthCheck, given, settings
from hypothesis_jsonschema import from_schema
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.seed_input import SeedInput
from livespec.validate.seed_input import make_validator
from returns.result import Failure, Success

if TYPE_CHECKING:
    from livespec.io.fastjsonschema_facade import Validator

__all__: list[str] = []


_SCHEMA_PATH = Path(livespec.schemas.__file__).parent / "seed_input.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


_VALID_PAYLOAD: dict[str, Any] = {
    "template": "livespec",
    "intent": "seed the project",
    "files": [
        {"path": "SPECIFICATION/spec.md", "content": "# Spec"},
    ],
    "sub_specs": [],
}


def test_minimal_payload(*, seed_input_validator: Validator) -> None:
    validator = make_validator(fast_validator=seed_input_validator)
    result = validator(payload=dict(_VALID_PAYLOAD))
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert isinstance(parsed, SeedInput)
    assert parsed.template == "livespec"
    assert parsed.intent == "seed the project"
    assert len(parsed.files) == 1
    assert parsed.files[0].path == "SPECIFICATION/spec.md"
    assert parsed.sub_specs == []


def test_payload_with_sub_specs(*, seed_input_validator: Validator) -> None:
    """Per v018 Q1 / v020 Q2, sub_specs[] carries per-template payloads."""
    validator = make_validator(fast_validator=seed_input_validator)
    payload: dict[str, Any] = {
        **_VALID_PAYLOAD,
        "sub_specs": [
            {
                "template_name": "livespec",
                "files": [
                    {
                        "path": "SPECIFICATION/templates/livespec/x.md",
                        "content": "X",
                    },
                ],
            },
        ],
    }
    result = validator(payload=payload)
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert len(parsed.sub_specs) == 1
    assert parsed.sub_specs[0].template_name == "livespec"
    assert len(parsed.sub_specs[0].files) == 1


def test_missing_required_field_returns_failure(
    *,
    seed_input_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=seed_input_validator)
    incomplete: dict[str, Any] = {"template": "livespec", "intent": "i", "files": []}
    result = validator(payload=incomplete)
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), ValidationError)


@given(payload=from_schema(_SCHEMA))
@settings(
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.too_slow,
    ],
    max_examples=10,
)
def test_pbt_schema_conforming_payloads_always_succeed(
    *,
    payload: dict[str, Any],
    seed_input_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=seed_input_validator)
    result = validator(payload=payload)
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert isinstance(parsed, SeedInput)
    assert len(parsed.files) == len(payload["files"])
    assert len(parsed.sub_specs) == len(payload["sub_specs"])
