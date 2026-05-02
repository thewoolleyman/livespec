"""LivespecConfig dataclass paired 1:1 with livespec_config.schema.json.

Per style doc §"Skill layout — schemas/dataclasses/": fields
match the schema one-to-one in name and Python type. The
dataclass is the type that flows through the railway after
schema validation:
    Result[LivespecConfig, ValidationError]
from validate.livespec_config.validate_livespec_config.

Per `check-newtype-domain-primitives`: `template` uses the
`TemplateName` NewType from `livespec.types`.

All fields are optional in the schema with documented defaults;
fastjsonschema applies the defaults at validation time so the
dataclass receives them populated. The dataclass-side defaults
mirror the schema's defaults so direct construction (without
going through the validator) still yields the same configured
state.
"""

from __future__ import annotations

from dataclasses import dataclass

from livespec.types import TemplateName

__all__: list[str] = ["LivespecConfig"]


@dataclass(frozen=True, kw_only=True, slots=True)
class LivespecConfig:
    """The `.livespec.jsonc` config wire dataclass.

    Mirrors livespec_config.schema.json: five optional fields
    matching the schema's defaults.
    """

    template: TemplateName = TemplateName("livespec")
    template_format_version: int = 1
    post_step_skip_doctor_llm_objective_checks: bool = False
    post_step_skip_doctor_llm_subjective_checks: bool = False
    pre_step_skip_static_checks: bool = False
