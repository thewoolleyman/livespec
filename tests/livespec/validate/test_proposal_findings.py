"""Tests for livespec.validate.proposal_findings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import livespec.schemas
from hypothesis import HealthCheck, given, settings
from hypothesis_jsonschema import from_schema
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.proposal_findings import ProposalFindings
from livespec.validate.proposal_findings import make_validator
from returns.result import Failure, Success

if TYPE_CHECKING:
    from livespec.io.fastjsonschema_facade import Validator

__all__: list[str] = []


_SCHEMA_PATH = Path(livespec.schemas.__file__).parent / "proposal_findings.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


_VALID_PAYLOAD: dict[str, Any] = {
    "findings": [
        {
            "name": "topic-a",
            "target_spec_files": ["SPECIFICATION/x.md"],
            "summary": "summary",
            "motivation": "motivation",
            "proposed_changes": "...",
        },
    ],
}


def test_well_formed_payload_returns_success(
    *,
    proposal_findings_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=proposal_findings_validator)
    result = validator(payload=dict(_VALID_PAYLOAD))
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert isinstance(parsed, ProposalFindings)
    assert len(parsed.findings) == 1
    assert parsed.findings[0].name == "topic-a"
    assert parsed.findings[0].target_spec_files == ["SPECIFICATION/x.md"]


def test_empty_findings_array(*, proposal_findings_validator: Validator) -> None:
    validator = make_validator(fast_validator=proposal_findings_validator)
    result = validator(payload={"findings": []})
    assert isinstance(result, Success)
    assert result.unwrap().findings == []


def test_missing_required_field_returns_failure(
    *,
    proposal_findings_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=proposal_findings_validator)
    incomplete: dict[str, Any] = {
        "findings": [
            {"name": "x", "target_spec_files": [], "summary": "s", "motivation": "m"},
        ],
    }
    result = validator(payload=incomplete)
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
    proposal_findings_validator: Validator,
) -> None:
    validator = make_validator(fast_validator=proposal_findings_validator)
    result = validator(payload=payload)
    assert isinstance(result, Success)
    parsed = result.unwrap()
    assert isinstance(parsed, ProposalFindings)
    assert len(parsed.findings) == len(payload["findings"])
