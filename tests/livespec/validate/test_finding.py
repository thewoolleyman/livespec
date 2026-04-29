"""Tests for livespec.validate.finding."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import livespec.schemas
from hypothesis import HealthCheck, given, settings
from hypothesis_jsonschema import from_schema
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.finding import Finding
from livespec.validate.finding import make_validator
from returns.result import Failure, Success

if TYPE_CHECKING:
    from livespec.io.fastjsonschema_facade import Validator

__all__: list[str] = []


_SCHEMA_PATH = Path(livespec.schemas.__file__).parent / "finding.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


_LINE_NO = 42


_VALID_PAYLOAD: dict[str, Any] = {
    "check_id": "doctor-out-of-band-edits",
    "status": "pass",
    "message": "ok",
    "path": None,
    "line": None,
    "spec_root": "SPECIFICATION/",
}


def test_well_formed_payload_returns_success(*, finding_validator: Validator) -> None:
    validator = make_validator(fast_validator=finding_validator)
    result = validator(payload=dict(_VALID_PAYLOAD))
    assert isinstance(result, Success)
    finding = result.unwrap()
    assert isinstance(finding, Finding)
    assert finding.check_id == "doctor-out-of-band-edits"
    assert finding.status == "pass"


def test_payload_with_path_and_line(*, finding_validator: Validator) -> None:
    validator = make_validator(fast_validator=finding_validator)
    payload: dict[str, Any] = {
        **_VALID_PAYLOAD,
        "status": "fail",
        "path": "SPECIFICATION/history/v003",
        "line": _LINE_NO,
    }
    result = validator(payload=payload)
    assert isinstance(result, Success)
    finding = result.unwrap()
    assert finding.path == "SPECIFICATION/history/v003"
    assert finding.line == _LINE_NO


def test_malformed_payload_returns_failure(*, finding_validator: Validator) -> None:
    validator = make_validator(fast_validator=finding_validator)
    result = validator(payload={"missing": "fields"})
    assert isinstance(result, Failure)
    err = result.failure()
    assert isinstance(err, ValidationError)
    assert "finding.schema.json" in str(err)


def test_malformed_status_enum_returns_failure(*, finding_validator: Validator) -> None:
    validator = make_validator(fast_validator=finding_validator)
    payload: dict[str, Any] = {**_VALID_PAYLOAD, "status": "unrecognized-status"}
    result = validator(payload=payload)
    assert isinstance(result, Failure)


@given(payload=from_schema(_SCHEMA))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=25)
def test_pbt_schema_conforming_payloads_always_succeed(
    *,
    payload: dict[str, Any],
    finding_validator: Validator,
) -> None:
    """Any payload satisfying finding.schema.json maps to a `Finding` Success."""
    validator = make_validator(fast_validator=finding_validator)
    result = validator(payload=payload)
    assert isinstance(result, Success)
    finding = result.unwrap()
    assert isinstance(finding, Finding)
    assert finding.check_id == payload["check_id"]
    assert finding.status == payload["status"]
