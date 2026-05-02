"""Validator for the sub_spec_payload wire payload.

Per style doc §"Skill layout — `validate/`": factory-shape
validator that takes the parsed payload (a dict from JSON
parsing) and the parsed schema (a dict from
sub_spec_payload.schema.json), validates the payload against
the schema via fastjsonschema, and returns
`Result[SubSpecPayload, ValidationError]`.
"""

from __future__ import annotations

from typing import Any

import fastjsonschema
from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.sub_spec_payload import SubSpecPayload
from livespec.types import TemplateName

__all__: list[str] = ["validate_sub_spec_payload"]


@safe(exceptions=(fastjsonschema.JsonSchemaValueException,))
def _raw_validate(*, payload: dict[str, Any], schema: dict[str, Any]) -> SubSpecPayload:
    """Decorator-lifted validate-and-construct call.

    Promotes `template_name` to `TemplateName` (semantic typing
    even though check-newtype-domain-primitives' exact-name
    lookup doesn't require it — see dataclass docstring).
    """
    validator = fastjsonschema.compile(schema)
    validated = validator(payload)
    return SubSpecPayload(
        template_name=TemplateName(validated["template_name"]),
        files=validated["files"],
    )


def validate_sub_spec_payload(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> Result[SubSpecPayload, ValidationError]:
    """Validate the sub_spec_payload payload against its schema.

    Returns Success(SubSpecPayload) on a well-formed payload;
    Failure(ValidationError) on rejection.
    """
    return _raw_validate(payload=payload, schema=schema).alt(
        lambda exc: ValidationError(f"sub_spec_payload: {exc}"),
    )
