"""Validator for the doctor_findings wire payload.

Per style doc §"Skill layout — `validate/`": factory-shape
validator that takes the parsed payload (a dict from JSON
parsing) and the parsed schema (a dict from
doctor_findings.schema.json), validates the payload against
the schema via fastjsonschema, and returns
`Result[DoctorFindings, ValidationError]`.

The vendored fastjsonschema raises `JsonSchemaValueException` on
violation; `@safe(exceptions=...)` lifts that onto the Result
track per the canonical pattern.
"""

from __future__ import annotations

from typing import Any

import fastjsonschema
from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.doctor_findings import DoctorFindings

__all__: list[str] = ["validate_doctor_findings"]


@safe(exceptions=(fastjsonschema.JsonSchemaValueException,))
def _raw_validate(*, payload: dict[str, Any], schema: dict[str, Any]) -> DoctorFindings:
    """Decorator-lifted validate-and-construct call.

    fastjsonschema.compile returns a validator function that
    raises JsonSchemaValueException on violation. On success we
    construct DoctorFindings from the validated payload, keeping
    the nested findings as dicts (consumers cast them via
    validate.finding.validate_finding when typed Finding
    instances are needed).
    """
    validator = fastjsonschema.compile(schema)
    validated = validator(payload)
    return DoctorFindings(findings=validated["findings"])


def validate_doctor_findings(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> Result[DoctorFindings, ValidationError]:
    """Validate the doctor_findings payload against its schema.

    Returns Success(DoctorFindings) on a well-formed payload;
    Failure(ValidationError) with the schema-violation path
    embedded in the message on rejection.
    """
    return _raw_validate(payload=payload, schema=schema).alt(
        lambda exc: ValidationError(f"doctor_findings: {exc}"),
    )
