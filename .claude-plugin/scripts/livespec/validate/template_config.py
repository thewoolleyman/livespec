"""Factory for the parsed `template.json` validator.

`make_validator(*, fast_validator=...)` accepts a pre-compiled
fastjsonschema validator (the typed `Validator` from
`livespec.io.fastjsonschema_facade`, with the schema dict's
`$id == "template_config.schema.json"`) and returns a closure
that threads the schema validation result through dataclass
construction.

See bootstrap/decisions.md 2026-04-26T09:23:07Z for the
factory-shape rationale (validate/ stays pure under the
import-linter parse-and-validate-are-pure contract; the compiled
validator is provided by the caller upstream in commands/ or
doctor/).
"""
from __future__ import annotations

from typing import Any

from returns.result import Result

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.template_config import TemplateConfig
from livespec.types import TypedValidator

__all__: list[str] = [
    "make_validator",
]



def make_validator(
    *,
    fast_validator: TypedValidator[dict[str, Any]],
) -> TypedValidator[TemplateConfig]:
    """Compose `fast_validator` with `TemplateConfig` dataclass construction.

    The returned closure:

    - Calls `fast_validator(payload=payload)` to schema-validate the dict.
    - On `Success(data)`, constructs `TemplateConfig(**data_with_defaults)`
      and returns `Success(config)`.
    - On `Failure(ValidationError(...))`, propagates the failure
      unchanged.
    """

    def validator(
        *,
        payload: dict[str, Any],
    ) -> Result[TemplateConfig, ValidationError]:
        return fast_validator(payload=payload).map(_to_dataclass)

    return validator


def _to_dataclass(data: dict[str, Any]) -> TemplateConfig:
    """Construct `TemplateConfig` from a schema-validated dict.

    `template_format_version` is required by the schema; the other
    fields use their schema-documented defaults when absent. The
    list field is copied via `list(...)` so the constructed
    dataclass owns its own list (defensive against caller mutation).
    """
    return TemplateConfig(
        template_format_version=data["template_format_version"],
        spec_root=data.get("spec_root", "SPECIFICATION/"),
        doctor_static_check_modules=list(
            data.get("doctor_static_check_modules", []),
        ),
        doctor_llm_objective_checks_prompt=data.get(
            "doctor_llm_objective_checks_prompt",
        ),
        doctor_llm_subjective_checks_prompt=data.get(
            "doctor_llm_subjective_checks_prompt",
        ),
    )
