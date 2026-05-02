"""Validator for the livespec_config wire payload.

Per style doc §"Skill layout — `validate/`": factory-shape
validator that takes the parsed payload (a dict from JSON
parsing) and the parsed schema (a dict from
livespec_config.schema.json), validates the payload against
the schema via fastjsonschema, and returns
`Result[LivespecConfig, ValidationError]`.

The vendored fastjsonschema raises `JsonSchemaValueException` on
violation; `@safe(exceptions=...)` lifts that onto the Result
track per the canonical pattern. fastjsonschema applies the
schema's `default` keywords during validation so the
constructed LivespecConfig always has all fields populated.
"""

from __future__ import annotations

from typing import Any

import fastjsonschema
from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.livespec_config import LivespecConfig
from livespec.types import TemplateName

__all__: list[str] = ["validate_livespec_config"]


@safe(exceptions=(fastjsonschema.JsonSchemaValueException,))
def _raw_validate(*, payload: dict[str, Any], schema: dict[str, Any]) -> LivespecConfig:
    """Decorator-lifted validate-and-construct call.

    fastjsonschema.compile returns a validator function that
    raises JsonSchemaValueException on violation. The compiled
    validator applies the schema's `default` keywords, so the
    resulting `validated` dict is fully populated even when the
    input payload was empty or partial. We promote `template` to
    the `TemplateName` NewType per
    `check-newtype-domain-primitives`.
    """
    validator = fastjsonschema.compile(schema)
    validated = validator(payload)
    return LivespecConfig(
        template=TemplateName(validated["template"]),
        template_format_version=validated["template_format_version"],
        post_step_skip_doctor_llm_objective_checks=validated[
            "post_step_skip_doctor_llm_objective_checks"
        ],
        post_step_skip_doctor_llm_subjective_checks=validated[
            "post_step_skip_doctor_llm_subjective_checks"
        ],
        pre_step_skip_static_checks=validated["pre_step_skip_static_checks"],
    )


def validate_livespec_config(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> Result[LivespecConfig, ValidationError]:
    """Validate the livespec_config payload against its schema.

    Returns Success(LivespecConfig) on a well-formed payload;
    Failure(ValidationError) on rejection (e.g., unknown field
    via `additionalProperties: false`).
    """
    return _raw_validate(payload=payload, schema=schema).alt(
        lambda exc: ValidationError(f"livespec_config: {exc}"),
    )
