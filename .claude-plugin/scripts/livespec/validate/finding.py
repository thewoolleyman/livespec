"""Validator for the finding wire payload.

Per style doc §"Skill layout — `validate/`": factory-shape
validator that takes the parsed payload (a dict from JSON
parsing) and the parsed schema (a dict from
finding.schema.json), validates the payload against the
schema via fastjsonschema, and returns
`Result[Finding, ValidationError]`.

The vendored fastjsonschema raises `JsonSchemaValueException` on
violation; `@safe(exceptions=...)` lifts that onto the Result
track per the canonical pattern. Subsequent cycles introduce
the cached `compile_schema` facade in
`livespec/io/fastjsonschema_facade.py` once a second validator
shows up; for now the validator inlines the compile call
(matching seed_input / revise_input).
"""

from __future__ import annotations

from typing import Any

import fastjsonschema
from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["validate_finding"]


@safe(exceptions=(fastjsonschema.JsonSchemaValueException,))
def _raw_validate(*, payload: dict[str, Any], schema: dict[str, Any]) -> Finding:
    """Decorator-lifted validate-and-construct call.

    fastjsonschema.compile returns a validator function that
    raises JsonSchemaValueException on violation. On success we
    construct Finding from the validated payload's well-known
    keys, promoting `check_id` to `CheckId` and `spec_root` to
    `SpecRoot` per `check-newtype-domain-primitives`.
    """
    validator = fastjsonschema.compile(schema)
    validated = validator(payload)
    return Finding(
        check_id=CheckId(validated["check_id"]),
        status=validated["status"],
        message=validated["message"],
        path=validated["path"],
        line=validated["line"],
        spec_root=SpecRoot(validated["spec_root"]),
    )


def validate_finding(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> Result[Finding, ValidationError]:
    """Validate the finding payload against its schema.

    Returns Success(Finding) on a well-formed payload;
    Failure(ValidationError) with the schema-violation path
    embedded in the message on rejection.
    """
    return _raw_validate(payload=payload, schema=schema).alt(
        lambda exc: ValidationError(f"finding: {exc}"),
    )
