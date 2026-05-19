"""Validator for the next_output wire payload.

Per style doc §"Skill layout — `validate/`": factory-shape
validator that takes the prepared payload (a dict) and the
parsed schema (a dict from next_output.schema.json), validates
the payload against the schema via fastjsonschema, and returns
`Result[NextOutput, ValidationError]`.

The vendored fastjsonschema raises `JsonSchemaValueException`
on violation; `@safe(exceptions=...)` lifts that onto the
Result track per the canonical pattern shared with the other
validators in this directory. The supervisor uses this
validator to round-trip the ranker's emitted dataclass against
the schema before writing JSON to stdout, so a drift between
the schema and the dataclass surfaces as ValidationError
(exit 4) rather than a silently-malformed stdout payload.
"""

from __future__ import annotations

from typing import Any

import fastjsonschema
from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.next_output import NextOutput

__all__: list[str] = ["validate_next_output"]


@safe(exceptions=(fastjsonschema.JsonSchemaValueException,))
def _raw_validate(*, payload: dict[str, Any], schema: dict[str, Any]) -> NextOutput:
    """Decorator-lifted validate-and-construct call.

    fastjsonschema.compile returns a validator function that
    raises JsonSchemaValueException on violation. Each of the
    three schema fields is required (`additionalProperties:
    false`); the compiled validator therefore returns a dict
    populated with exactly those keys, which the dataclass
    constructor consumes positionally.
    """
    validator = fastjsonschema.compile(schema)
    validated = validator(payload)
    return NextOutput(
        action=validated["action"],
        reason=validated["reason"],
        urgency=validated["urgency"],
    )


def validate_next_output(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> Result[NextOutput, ValidationError]:
    """Validate the next_output payload against its schema.

    Returns `Success(NextOutput)` on a schema-conformant
    payload; `Failure(ValidationError)` on rejection (unknown
    field, missing required, enum violation, etc.).
    """
    return _raw_validate(payload=payload, schema=schema).alt(
        lambda exc: ValidationError(f"next_output: {exc}"),
    )
