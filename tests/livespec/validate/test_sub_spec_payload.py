"""Tests for livespec.validate.sub_spec_payload."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import livespec.schemas
from hypothesis import HealthCheck, given, settings
from hypothesis_jsonschema import from_schema
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.sub_spec_payload import SubSpecPayload
from livespec.validate.sub_spec_payload import make_validator
from returns.result import Failure, Success

if TYPE_CHECKING:
    from livespec.io.fastjsonschema_facade import Validator

__all__: list[str] = []


_SCHEMA_PATH = Path(livespec.schemas.__file__).parent / "sub_spec_payload.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


_VALID_PAYLOAD: dict[str, Any] = {
    "template_name": "livespec",
    "files": [
        {"path": "SPECIFICATION/templates/livespec/spec.md", "content": "# X"},
    ],
}


def test_well_formed_payload_returns_success(
    *,
    sub_spec_payload_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=sub_spec_payload_validator)
    result = validator(payload=dict(_VALID_PAYLOAD))
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert isinstance(parsed, SubSpecPayload)
    assert parsed.template_name == "livespec"
    assert len(parsed.files) == 1
    assert parsed.files[0].path == "SPECIFICATION/templates/livespec/spec.md"


def test_empty_files_array(*, sub_spec_payload_validator: Validator) -> None:
    validator = make_validator(fast_validator=sub_spec_payload_validator)
    result = validator(payload={"template_name": "minimal", "files": []})
    assert isinstance(result, Success)
    assert result.unwrap().files == []


def test_missing_required_field_returns_failure(
    *,
    sub_spec_payload_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=sub_spec_payload_validator)
    result = validator(payload={"template_name": "livespec"})
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), ValidationError)


@given(payload=from_schema(_SCHEMA))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
def test_pbt_schema_conforming_payloads_always_succeed(
    *,
    payload: dict[str, Any],
    sub_spec_payload_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=sub_spec_payload_validator)
    result = validator(payload=payload)
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert isinstance(parsed, SubSpecPayload)
    assert parsed.template_name == payload["template_name"]
