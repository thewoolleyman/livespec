"""Tests for livespec.validate.doctor_findings.

Per style doc §"Skill layout — `validate/`": validator at
`validate/doctor_findings.py` exports
`validate_doctor_findings(payload, schema)` returning
`Result[DoctorFindings, ValidationError]`. The doctor_findings
wire payload wraps a `findings` list (per
`schemas/doctor_findings.schema.json`); each entry mirrors the
finding schema (per v014 N2 standalone).
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.doctor_findings import DoctorFindings
from livespec.validate import doctor_findings
from returns.result import Failure, Success

__all__: list[str] = []

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude-plugin"
    / "scripts"
    / "livespec"
    / "schemas"
    / "doctor_findings.schema.json"
)

# Module-level schema cache (v040 D1): hypothesis-based @given
# tests run the body ~100 times per invocation; reloading the schema
# from disk on each example pushes individual examples over the
# default 200ms hypothesis deadline under `pytest -n auto` xdist
# worker contention. Loading once at module-import time eliminates
# per-example file I/O and the associated timing nondeterminism.
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_validate_doctor_findings_returns_success_for_empty_findings_list() -> None:
    """An empty `findings` list is a valid (if unusual) doctor output."""
    schema = _SCHEMA
    payload: dict[str, object] = {"findings": []}
    result = doctor_findings.validate_doctor_findings(payload=payload, schema=schema)
    assert result == Success(DoctorFindings(findings=[]))


def test_validate_doctor_findings_returns_success_for_one_finding() -> None:
    """A single-finding payload validates and round-trips field-for-field."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "findings": [
            {
                "check_id": "doctor-version-contiguity",
                "status": "pass",
                "message": "all versions contiguous",
                "path": None,
                "line": None,
                "spec_root": "SPECIFICATION",
            },
        ],
    }
    result = doctor_findings.validate_doctor_findings(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert isinstance(value, DoctorFindings)
            assert len(value.findings) == 1
            assert value.findings[0]["check_id"] == "doctor-version-contiguity"
        case _:
            msg = f"expected Success(DoctorFindings), got {result}"
            raise AssertionError(msg)


def test_validate_doctor_findings_returns_failure_on_missing_findings_field() -> None:
    """A payload without `findings` returns Failure(ValidationError)."""
    schema = _SCHEMA
    result = doctor_findings.validate_doctor_findings(payload={}, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "doctor_findings:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


@settings(deadline=None)
@given(message=st.text(min_size=1, max_size=200))
def test_validate_doctor_findings_round_trips_finding_message(*, message: str) -> None:
    """For arbitrary finding-message text, the success path preserves it verbatim."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "findings": [
            {
                "check_id": "doctor-version-contiguity",
                "status": "pass",
                "message": message,
                "path": None,
                "line": None,
                "spec_root": "SPECIFICATION",
            },
        ],
    }
    result = doctor_findings.validate_doctor_findings(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.findings[0]["message"] == message
        case _:
            msg = f"expected Success(DoctorFindings), got {result}"
            raise AssertionError(msg)
