"""Factory for the parsed `.livespec.jsonc` validator.

`make_validator(*, fast_validator=...)` accepts a pre-compiled
fastjsonschema validator (the typed `Validator` from
`livespec.io.fastjsonschema_facade`, with the schema dict's
`$id == "livespec_config.schema.json"`) and returns a closure that
threads the schema validation result through dataclass
construction.

Pure-validate discipline (per
`python-skill-script-style-requirements.md` §"Purity and I/O
isolation"): this module imports zero `livespec.io.*`,
`subprocess`, `pathlib`, `returns.io`, or networking modules. The
compiled validator is provided by the caller, who lives upstream
in `commands/<cmd>.py` or `doctor/run_static.py` and orchestrates
the io/-bound schema-load + jsonc-parse + compile_schema chain.
This separation is the import-linter `parse-and-validate-are-pure`
contract; the validate/ closure captures the compiled validator
without touching io/ directly. (See bootstrap/decisions.md
2026-04-26T09:23:07Z for the factory-shape rationale.)
"""
from __future__ import annotations

from typing import Any

from returns.result import Result

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.livespec_config import LivespecConfig
from livespec.types import TemplateName, TypedValidator

__all__: list[str] = [
    "make_validator",
]

"""Local type alias matching `livespec.io.fastjsonschema_facade.Validator`.
Re-declared here (not imported from io/) to keep `validate/` strictly
pure under the import-linter `parse-and-validate-are-pure` contract."""


def make_validator(
    *,
    fast_validator: TypedValidator[dict[str, Any]],
) -> TypedValidator[LivespecConfig]:
    """Compose `fast_validator` with `LivespecConfig` dataclass construction.

    The returned closure:

    - Calls `fast_validator(payload=payload)` to schema-validate the dict.
    - On `Success(data)`, constructs `LivespecConfig(**data_with_defaults)`
      and returns `Success(config)`.
    - On `Failure(ValidationError(...))`, propagates the failure
      unchanged.

    `_to_dataclass` applies the schema's documented defaults for
    fields the payload omits (per PROPOSAL.md §"Configuration:
    `.livespec.jsonc` → Absence behavior" — missing keys take the
    documented defaults).
    """

    def validator(
        *,
        payload: dict[str, Any],
    ) -> Result[LivespecConfig, ValidationError]:
        return fast_validator(payload=payload).map(_to_dataclass)

    return validator


def _to_dataclass(data: dict[str, Any]) -> LivespecConfig:
    """Construct `LivespecConfig` from a schema-validated dict.

    Each `data.get(<key>, <default>)` mirrors the schema's field
    default. The schema validator above guarantees no extra keys
    (`additionalProperties: false`) and per-field type compliance,
    so every present key is safe to pass through.
    """
    return LivespecConfig(
        template=TemplateName(data.get("template", "livespec")),
        template_format_version=data.get("template_format_version", 1),
        post_step_skip_doctor_llm_objective_checks=data.get(
            "post_step_skip_doctor_llm_objective_checks",
            False,
        ),
        post_step_skip_doctor_llm_subjective_checks=data.get(
            "post_step_skip_doctor_llm_subjective_checks",
            False,
        ),
        pre_step_skip_static_checks=data.get("pre_step_skip_static_checks", False),
    )
