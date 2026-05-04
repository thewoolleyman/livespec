"""Tests for livespec.validate.proposal_findings.

Per style doc §"Skill layout — `validate/`": validator at
`validate/proposal_findings.py` exports
`validate_proposal_findings(payload, schema)` returning
`Result[ProposalFindings, ValidationError]`. Mirrors the
finding / seed_input validator shape (per v013 M6 +
the validator-as-factory-style decision).
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.proposal_findings import ProposalFindings
from livespec.validate import proposal_findings
from returns.result import Failure, Success

__all__: list[str] = []

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude-plugin"
    / "scripts"
    / "livespec"
    / "schemas"
    / "proposal_findings.schema.json"
)
# Module-level schema cache. The hypothesis-based round-trip test
# generates ~100 examples per invocation; reloading the schema
# from disk on each example pushed individual examples over the
# default 200ms hypothesis deadline under `pytest -n auto` xdist
# worker-process load (one observed flake under v039 D2's
# canonical aggregate run; passed on retry). Loading once at
# module-import time eliminates per-example file I/O and the
# associated timing nondeterminism. The user-codified hard
# constraint (2026-05-05) requires conclusive resolution of any
# observed flake; no `@settings(deadline=None)` workaround is
# used because that would mask the underlying cost rather than
# eliminate it.
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def _make_finding(*, name: str = "Example proposal") -> dict[str, object]:
    return {
        "name": name,
        "target_spec_files": ["SPECIFICATION/spec.md"],
        "summary": "Add foo.",
        "motivation": "Foo is needed.",
        "proposed_changes": "Append a sentence to spec.md.",
    }


def test_validate_proposal_findings_returns_success_for_valid_payload() -> None:
    """A well-formed proposal-findings payload validates to Success(ProposalFindings)."""
    schema = _SCHEMA
    payload: dict[str, object] = {"findings": [_make_finding()]}
    result = proposal_findings.validate_proposal_findings(payload=payload, schema=schema)
    expected = ProposalFindings(findings=payload["findings"])
    assert result == Success(expected)


def test_validate_proposal_findings_returns_failure_on_schema_violation() -> None:
    """A schema-violating payload returns Failure(ValidationError)."""
    schema = _SCHEMA
    payload: dict[str, object] = {"findings": "not-an-array"}
    result = proposal_findings.validate_proposal_findings(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "proposal_findings:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_proposal_findings_rejects_missing_findings_key() -> None:
    """A payload missing the required `findings` key returns Failure."""
    schema = _SCHEMA
    payload: dict[str, object] = {}
    result = proposal_findings.validate_proposal_findings(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError()):
            pass
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


@given(name=st.text(min_size=1, max_size=200))
def test_validate_proposal_findings_round_trips_name_text(*, name: str) -> None:
    """For arbitrary non-empty `name` strings, the success path preserves the text verbatim."""
    schema = _SCHEMA
    payload: dict[str, object] = {"findings": [_make_finding(name=name)]}
    result = proposal_findings.validate_proposal_findings(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.findings[0]["name"] == name
        case _:
            msg = f"expected Success(ProposalFindings), got {result}"
            raise AssertionError(msg)
