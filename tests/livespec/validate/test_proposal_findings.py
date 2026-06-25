"""Tests for livespec.validate.proposal_findings.

Per style doc: validator at
`validate/proposal_findings.py` exports
`validate_proposal_findings(payload, schema)` returning
`Result[ProposalFindings, ValidationError]`. Mirrors the
finding / seed_input validator-as-factory-style shape.

li-8mj2lz, PC #4 sub-proposal 1: the optional `spec_commitments`
block's shape (kebab-case id_hint, non-empty description,
optional supersedes[]) is enforced by the JSON Schema and lifts
to ValidationError (exit 4) at this validator's boundary.
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.proposal_findings import ProposalFindings
from livespec.schemas.dataclasses.proposed_change_front_matter import (
    ImplFollowup,
    SpecCommitments,
)
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
# Module-level schema cache. The hypothesis-based round-trip
# test generates ~100 examples per invocation; reloading the
# schema from disk on each example would burn unnecessary I/O.
# Loading once at module-import time eliminates per-example
# file work. Companion to the `@settings(deadline=None)`
# decorator on the @given test below — the decorator is the
# load-bearing flake fix (round-trip text preservation has no
# timing semantics, so the 200ms hypothesis deadline cannot
# fail informatively under xdist worker-process contention).
# The cache is a secondary work-elimination optimization.
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


@settings(deadline=None)
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


# li-8mj2lz, PC #4 sub-proposal 1: spec_commitments validation.
# The schema is the validation seam — these tests pin the schema's
# enforcement of the spec.md
# contract so any future schema edit that loosens the shape (e.g.,
# drops the kebab pattern, drops minLength) is caught here.


def test_validate_proposal_findings_accepts_spec_commitments_with_only_impl_followups() -> None:
    """A well-formed spec_commitments block without supersedes constructs the dataclass."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "findings": [_make_finding()],
        "spec_commitments": {
            "impl_followups": [
                {"id_hint": "wire-skill", "description": "Wire the new skill."},
                {"id_hint": "doctor-check", "description": "Add the doctor invariant."},
            ],
        },
    }
    result = proposal_findings.validate_proposal_findings(payload=payload, schema=schema)
    expected = ProposalFindings(
        findings=payload["findings"],  # pyright: ignore[reportArgumentType]
        spec_commitments=SpecCommitments(
            impl_followups=[
                ImplFollowup(id_hint="wire-skill", description="Wire the new skill."),
                ImplFollowup(
                    id_hint="doctor-check",
                    description="Add the doctor invariant.",
                ),
            ],
            supersedes=[],
        ),
    )
    assert result == Success(expected)


def test_validate_proposal_findings_accepts_spec_commitments_with_supersedes() -> None:
    """A well-formed spec_commitments block with supersedes preserves the list verbatim."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "findings": [_make_finding()],
        "spec_commitments": {
            "impl_followups": [
                {"id_hint": "replace-old", "description": "Replace the prior impl."},
            ],
            "supersedes": ["prior-hint-one", "prior-hint-two"],
        },
    }
    result = proposal_findings.validate_proposal_findings(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.spec_commitments is not None
            assert value.spec_commitments.supersedes == ["prior-hint-one", "prior-hint-two"]
            assert len(value.spec_commitments.impl_followups) == 1
            assert value.spec_commitments.impl_followups[0].id_hint == "replace-old"
        case _:
            msg = f"expected Success(ProposalFindings), got {result}"
            raise AssertionError(msg)


def test_validate_proposal_findings_treats_absent_spec_commitments_as_none() -> None:
    """Omitting spec_commitments entirely produces ProposalFindings with spec_commitments=None."""
    schema = _SCHEMA
    payload: dict[str, object] = {"findings": [_make_finding()]}
    result = proposal_findings.validate_proposal_findings(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.spec_commitments is None
        case _:
            msg = f"expected Success(ProposalFindings), got {result}"
            raise AssertionError(msg)


def test_validate_proposal_findings_rejects_spec_commitments_missing_impl_followups() -> None:
    """A spec_commitments block without the required impl_followups[] field returns Failure."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "findings": [_make_finding()],
        "spec_commitments": {"supersedes": ["earlier-hint"]},
    }
    result = proposal_findings.validate_proposal_findings(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "proposal_findings:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_proposal_findings_rejects_impl_followup_missing_id_hint() -> None:
    """An impl_followups[] entry without id_hint returns Failure."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "findings": [_make_finding()],
        "spec_commitments": {
            "impl_followups": [{"description": "Missing the slug."}],
        },
    }
    result = proposal_findings.validate_proposal_findings(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "proposal_findings:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_proposal_findings_rejects_impl_followup_with_empty_description() -> None:
    """An impl_followups[] entry whose description is an empty string returns Failure."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "findings": [_make_finding()],
        "spec_commitments": {
            "impl_followups": [{"id_hint": "wire-it", "description": ""}],
        },
    }
    result = proposal_findings.validate_proposal_findings(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "proposal_findings:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_proposal_findings_rejects_impl_followup_with_non_kebab_id_hint() -> None:
    """An impl_followups[] entry whose id_hint violates the kebab-case pattern returns Failure."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "findings": [_make_finding()],
        "spec_commitments": {
            "impl_followups": [
                {"id_hint": "Not Kebab Case", "description": "ok"},
            ],
        },
    }
    result = proposal_findings.validate_proposal_findings(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "proposal_findings:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_proposal_findings_rejects_non_list_impl_followups() -> None:
    """impl_followups must be an array; a non-list value returns Failure."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "findings": [_make_finding()],
        "spec_commitments": {"impl_followups": "not-a-list"},
    }
    result = proposal_findings.validate_proposal_findings(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "proposal_findings:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_proposal_findings_rejects_non_kebab_supersedes_entry() -> None:
    """A supersedes[] entry violating the kebab pattern returns Failure."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "findings": [_make_finding()],
        "spec_commitments": {
            "impl_followups": [{"id_hint": "ok-hint", "description": "ok"}],
            "supersedes": ["Bad Slug"],
        },
    }
    result = proposal_findings.validate_proposal_findings(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "proposal_findings:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_proposal_findings_rejects_unknown_spec_commitments_field() -> None:
    """An additional unknown field inside spec_commitments returns Failure (additionalProperties: false)."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "findings": [_make_finding()],
        "spec_commitments": {
            "impl_followups": [{"id_hint": "ok-hint", "description": "ok"}],
            "unknown_field": "should-not-be-allowed",
        },
    }
    result = proposal_findings.validate_proposal_findings(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError()):
            pass
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)
