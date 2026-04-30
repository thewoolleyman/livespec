"""Validator for the seed-input wire payload.

Per style doc §"Skill layout — `validate/`": factory-shape
validator that takes both the parsed payload (a dict from JSON
parsing) and the parsed schema (a dict from
seed_input.schema.json), validates the payload against the
schema via fastjsonschema, and returns
`Result[SeedInput, ValidationError]`.

The vendored fastjsonschema raises `JsonSchemaValueException` on
violation; `@safe(exceptions=...)` lifts that onto the Result
track per the canonical pattern. Subsequent cycles introduce
the cached `compile_schema` facade in
`livespec/io/fastjsonschema_facade.py` once a second validator
shows up; for now the validator inlines the compile call.
"""

from __future__ import annotations

from typing import Any

import fastjsonschema
from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.seed_input import SeedInput

__all__: list[str] = ["validate_seed_input"]


@safe(exceptions=(fastjsonschema.JsonSchemaValueException,))
def _raw_validate(*, payload: dict[str, Any], schema: dict[str, Any]) -> SeedInput:
    """Decorator-lifted validate-and-construct call.

    fastjsonschema.compile returns a validator function that
    raises JsonSchemaValueException on violation. On success we
    construct SeedInput from the validated payload's well-known
    keys.
    """
    validator = fastjsonschema.compile(schema)
    validated = validator(payload)
    return SeedInput(
        template=validated["template"],
        intent=validated["intent"],
        files=validated["files"],
        sub_specs=validated["sub_specs"],
    )


def validate_seed_input(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> Result[SeedInput, ValidationError]:
    """Validate the seed-input payload against its schema.

    Returns Success(SeedInput) on a well-formed payload;
    Failure(ValidationError) with the schema-violation path
    embedded in the message on rejection.
    """
    return _raw_validate(payload=payload, schema=schema).alt(
        lambda exc: ValidationError(f"seed_input: {exc}"),
    )
