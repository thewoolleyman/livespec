"""Tests for livespec.validate.doctor_findings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import livespec.schemas
from hypothesis import HealthCheck, given, settings
from hypothesis_jsonschema import from_schema
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.doctor_findings import DoctorFindings
from livespec.validate.doctor_findings import make_validator
from returns.result import Failure, Success

if TYPE_CHECKING:
    from livespec.io.fastjsonschema_facade import Validator

__all__: list[str] = []


_SCHEMA_PATH = Path(livespec.schemas.__file__).parent / "doctor_findings.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


_VALID_PAYLOAD: dict[str, Any] = {
    "findings": [
        {
            "check_id": "doctor-out-of-band-edits",
            "status": "pass",
            "message": "ok",
            "path": None,
            "line": None,
            "spec_root": "SPECIFICATION/",
        },
    ],
}


def test_well_formed_payload_returns_success(*, doctor_findings_validator: Validator) -> None:
    validator = make_validator(fast_validator=doctor_findings_validator)
    result = validator(payload=dict(_VALID_PAYLOAD))
    assert isinstance(result, Success)
    payload = result.unwrap()
    assert isinstance(payload, DoctorFindings)
    assert len(payload.findings) == 1
    assert payload.findings[0].check_id == "doctor-out-of-band-edits"


def test_empty_findings_array(*, doctor_findings_validator: Validator) -> None:
    validator = make_validator(fast_validator=doctor_findings_validator)
    result = validator(payload={"findings": []})
    assert isinstance(result, Success)
    assert result.unwrap().findings == []


def test_malformed_payload_returns_failure(*, doctor_findings_validator: Validator) -> None:
    validator = make_validator(fast_validator=doctor_findings_validator)
    result = validator(payload={"unrelated": True})
    assert isinstance(result, Failure)
    assert isinstance(result.failure(), ValidationError)


@given(payload=from_schema(_SCHEMA))
@settings(
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.too_slow,
    ],
    max_examples=15,
)
def test_pbt_schema_conforming_payloads_always_succeed(
    *,
    payload: dict[str, Any],
    doctor_findings_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=doctor_findings_validator)
    result = validator(payload=payload)
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert isinstance(parsed, DoctorFindings)
    assert len(parsed.findings) == len(payload["findings"])
