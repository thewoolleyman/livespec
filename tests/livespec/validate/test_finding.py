"""Tests for livespec.validate.finding.

Per style doc §"Skill layout — `validate/`": validator at
`validate/finding.py` exports `validate_finding(payload, schema)`
returning `Result[Finding, ValidationError]`. Mirrors the
seed_input / revise_input validator shape (per v013 M6 +
the validator-as-factory-style decision).
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
from returns.result import Failure, Success

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot
from livespec.validate import finding

__all__: list[str] = []

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude-plugin"
    / "scripts"
    / "livespec"
    / "schemas"
    / "finding.schema.json"
)


def test_validate_finding_returns_success_with_dataclass_for_valid_payload() -> None:
    """A well-formed finding payload validates to Success(Finding)."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "check_id": "doctor-version-contiguity",
        "status": "pass",
        "message": "all version directories contiguous",
        "path": None,
        "line": None,
        "spec_root": "SPECIFICATION",
    }
    result = finding.validate_finding(payload=payload, schema=schema)
    expected = Finding(
        check_id=CheckId("doctor-version-contiguity"),
        status="pass",
        message="all version directories contiguous",
        path=None,
        line=None,
        spec_root=SpecRoot("SPECIFICATION"),
    )
    assert result == Success(expected)


def test_validate_finding_returns_failure_on_schema_violation() -> None:
    """A schema-violating payload returns Failure(ValidationError).

    Drives the missing-required-field branch: the payload is a
    valid object but lacks `status`, so fastjsonschema raises
    JsonSchemaValueException, which the @safe-decorated raw
    validator lifts to Failure and the public seam .alt-maps to
    a ValidationError.
    """
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "check_id": "doctor-version-contiguity",
        "message": "missing status field",
        "path": None,
        "line": None,
        "spec_root": "SPECIFICATION",
    }
    result = finding.validate_finding(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "finding:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


@given(message=st.text(min_size=1, max_size=200))
def test_validate_finding_round_trips_message_text(*, message: str) -> None:
    """For arbitrary `message` strings, the success path preserves the text verbatim."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "check_id": "doctor-version-contiguity",
        "status": "pass",
        "message": message,
        "path": None,
        "line": None,
        "spec_root": "SPECIFICATION",
    }
    result = finding.validate_finding(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.message == message
        case _:
            msg = f"expected Success(Finding), got {result}"
            raise AssertionError(msg)


def test_validate_finding_carries_path_and_line_when_present() -> None:
    """When `path` and `line` are populated, the dataclass carries them through."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "check_id": "doctor-frontmatter-spec-version",
        "status": "fail",
        "message": "version field missing",
        "path": "SPECIFICATION/spec.md",
        "line": 3,
        "spec_root": "SPECIFICATION",
    }
    result = finding.validate_finding(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert isinstance(value, Finding)
            assert value.path == "SPECIFICATION/spec.md"
            assert value.line == 3
        case _:
            msg = f"expected Success(Finding), got {result}"
            raise AssertionError(msg)
