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
the schema and the dataclasses surfaces as ValidationError
(exit 4) rather than a silently-malformed stdout payload.
"""

from __future__ import annotations

from typing import Any

import fastjsonschema
from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.next_output import (
    NextCandidate,
    NextOutput,
    NextPagination,
)

__all__: list[str] = ["validate_next_output"]


def _candidate_from_validated(*, item: dict[str, Any]) -> NextCandidate:
    """Construct one NextCandidate from a schema-validated item dict.

    `target` is optional in the schema (`candidates.items` lists
    only `action`/`reason`/`urgency` as required); a missing key
    maps to `None` on the dataclass so the serializer can omit it
    symmetrically.
    """
    return NextCandidate(
        action=item["action"],
        reason=item["reason"],
        urgency=item["urgency"],
        target=item.get("target"),
    )


@safe(exceptions=(fastjsonschema.JsonSchemaValueException,))
def _raw_validate(*, payload: dict[str, Any], schema: dict[str, Any]) -> NextOutput:
    """Decorator-lifted validate-and-construct call.

    fastjsonschema.compile returns a validator function that
    raises JsonSchemaValueException on violation. Both top-level
    keys are required (`additionalProperties: false`); the
    compiled validator therefore returns a dict populated with
    exactly the `candidates` array and the `pagination` object,
    which the nested dataclass constructors consume.
    """
    validator = fastjsonschema.compile(schema)
    validated = validator(payload)
    pagination = validated["pagination"]
    return NextOutput(
        candidates=tuple(_candidate_from_validated(item=item) for item in validated["candidates"]),
        pagination=NextPagination(
            offset=pagination["offset"],
            limit=pagination["limit"],
            total=pagination["total"],
            has_more=pagination["has_more"],
        ),
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
