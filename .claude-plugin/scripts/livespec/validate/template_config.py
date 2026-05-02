"""Validator for the template_config wire payload.

Per style doc §"Skill layout — `validate/`": factory-shape
validator that takes the parsed payload (a dict from JSON
parsing of template.json) and the parsed schema (a dict from
template_config.schema.json), validates the payload against
the schema via fastjsonschema, and returns
`Result[TemplateConfig, ValidationError]`.

fastjsonschema applies the schema's `default` keywords during
validation so the constructed TemplateConfig has all five
fields populated even when the input payload was minimal.
"""

from __future__ import annotations

from typing import Any

import fastjsonschema
from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.template_config import TemplateConfig
from livespec.types import SpecRoot

__all__: list[str] = ["validate_template_config"]


@safe(exceptions=(fastjsonschema.JsonSchemaValueException,))
def _raw_validate(*, payload: dict[str, Any], schema: dict[str, Any]) -> TemplateConfig:
    """Decorator-lifted validate-and-construct call.

    Promotes `spec_root` to `SpecRoot` per
    `check-newtype-domain-primitives`.
    """
    validator = fastjsonschema.compile(schema)
    validated = validator(payload)
    return TemplateConfig(
        template_format_version=validated["template_format_version"],
        spec_root=SpecRoot(validated["spec_root"]),
        doctor_static_check_modules=validated["doctor_static_check_modules"],
        doctor_llm_objective_checks_prompt=validated["doctor_llm_objective_checks_prompt"],
        doctor_llm_subjective_checks_prompt=validated["doctor_llm_subjective_checks_prompt"],
    )


def validate_template_config(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> Result[TemplateConfig, ValidationError]:
    """Validate the template_config payload against its schema.

    Returns Success(TemplateConfig) on a well-formed payload;
    Failure(ValidationError) on rejection (e.g., unsupported
    template_format_version, unknown field).
    """
    return _raw_validate(payload=payload, schema=schema).alt(
        lambda exc: ValidationError(f"template_config: {exc}"),
    )
