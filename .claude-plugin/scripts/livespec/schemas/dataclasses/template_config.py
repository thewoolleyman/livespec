"""TemplateConfig dataclass paired 1:1 with template_config.schema.json.

Per style doc §"Skill layout — schemas/dataclasses/": fields
match the schema one-to-one in name and Python type. The
dataclass is the type that flows through the railway after
schema validation:
    Result[TemplateConfig, ValidationError]
from validate.template_config.validate_template_config.

Per v011 K5: a template's `template.json` declares its format
version, spec_root location, optional doctor extensibility
hooks (static check modules), and optional LLM-prompt paths
(objective + subjective checks). v1 livespec supports only
`template_format_version: 1`.

Per `check-newtype-domain-primitives`: `spec_root` uses the
`SpecRoot` NewType.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from livespec.types import SpecRoot

__all__: list[str] = ["TemplateConfig"]


@dataclass(frozen=True, kw_only=True, slots=True)
class TemplateConfig:
    """The template.json wire dataclass.

    Mirrors template_config.schema.json: required
    `template_format_version` (enum [1]); optional `spec_root`
    (default 'SPECIFICATION/'), `doctor_static_check_modules`
    (default empty), and two LLM-prompt path fields (default
    None).
    """

    template_format_version: int
    # NewType is structural — `SpecRoot("SPECIFICATION/")`
    # returns the immutable str at definition time and is
    # safely shareable across instances; ruff's RUF009 false-
    # positives the call as mutable-default risk.
    spec_root: SpecRoot = SpecRoot("SPECIFICATION/")  # noqa: RUF009
    doctor_static_check_modules: list[str] = field(default_factory=list)
    doctor_llm_objective_checks_prompt: str | None = None
    doctor_llm_subjective_checks_prompt: str | None = None
