"""Validator for the proposal-findings wire payload.

Per style doc §"Skill layout — `validate/`": factory-shape
validator that takes both the parsed payload (a dict from JSON
parsing) and the parsed schema (a dict from
proposal_findings.schema.json), validates the payload against
the schema via fastjsonschema, and returns
`Result[ProposalFindings, ValidationError]`.

The vendored fastjsonschema raises `JsonSchemaValueException` on
violation; `@safe(exceptions=...)` lifts that onto the Result
track per the canonical pattern.
"""

from __future__ import annotations

from typing import Any

import fastjsonschema
from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.proposal_findings import ProposalFindings
from livespec.types import Author

__all__: list[str] = ["validate_proposal_findings"]


@safe(exceptions=(fastjsonschema.JsonSchemaValueException,))
def _raw_validate(*, payload: dict[str, Any], schema: dict[str, Any]) -> ProposalFindings:
    """Decorator-lifted validate-and-construct call.

    fastjsonschema.compile returns a validator function that
    raises JsonSchemaValueException on violation. On success we
    construct ProposalFindings from the validated payload's
    well-known keys.
    """
    validator = fastjsonschema.compile(schema)
    validated = validator(payload)
    raw_author = validated.get("author")
    return ProposalFindings(
        findings=validated["findings"],
        author=Author(raw_author) if raw_author is not None else None,
    )


def validate_proposal_findings(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> Result[ProposalFindings, ValidationError]:
    """Validate the proposal-findings payload against its schema.

    Returns Success(ProposalFindings) on a well-formed payload;
    Failure(ValidationError) with the schema-violation path
    embedded in the message on rejection.
    """
    return _raw_validate(payload=payload, schema=schema).alt(
        lambda exc: ValidationError(f"proposal_findings: {exc}"),
    )
