"""Validator for the revise-input wire payload.

Per style doc §"Skill layout — `validate/`": factory-shape
validator that takes both the parsed payload (a dict from JSON
parsing) and the parsed schema (a dict from
revise_input.schema.json), validates the payload against the
schema via fastjsonschema, and returns
`Result[RevisionInput, ValidationError]`.

The vendored fastjsonschema raises `JsonSchemaValueException` on
violation; `@safe(exceptions=...)` lifts that onto the Result
track per the canonical pattern.
"""

from __future__ import annotations

from typing import Any

import fastjsonschema
from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.revise_input import RevisionInput

__all__: list[str] = ["validate_revise_input"]


@safe(exceptions=(fastjsonschema.JsonSchemaValueException,))
def _raw_validate(*, payload: dict[str, Any], schema: dict[str, Any]) -> RevisionInput:
    """Decorator-lifted validate-and-construct call.

    fastjsonschema.compile returns a validator function that
    raises JsonSchemaValueException on violation. On success we
    construct RevisionInput from the validated payload's
    well-known keys.
    """
    validator = fastjsonschema.compile(schema)
    validated = validator(payload)
    return RevisionInput(
        author=validated.get("author"),
        decisions=validated["decisions"],
    )


def validate_revise_input(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> Result[RevisionInput, ValidationError]:
    """Validate the revise-input payload against its schema.

    Returns Success(RevisionInput) on a well-formed payload;
    Failure(ValidationError) with the schema-violation path
    embedded in the message on rejection.
    """
    return _raw_validate(payload=payload, schema=schema).alt(
        lambda exc: ValidationError(f"revise_input: {exc}"),
    )
