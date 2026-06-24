"""TemplateConfig dataclass paired 1:1 with template_config.schema.json.

Per style doc §"Skill layout — schemas/dataclasses/": fields
match the schema one-to-one in name and Python type. The
dataclass is the type that flows through the railway after
schema validation:
  Result[TemplateConfig, ValidationError]
from validate.template_config.validate_template_config.

Per a template's `template.json` declares its format
version, spec_root location, optional doctor extensibility
hooks (static check modules), and optional LLM-prompt paths
(objective + subjective checks).

Per the v2 manifest mechanism in SPECIFICATION/spec.md
§"Template manifest" and contracts.md §"Template manifest wire
contract": v2 templates additionally declare `spec_files` — a
mapping from spec-target-relative path strings to per-file
declarations. Each declaration carries a `kind` discriminator
whose sole value is `markdown`.

Per `check-newtype-domain-primitives`: `spec_root` uses the
`SpecRoot` NewType.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from livespec.types import SpecRoot

__all__: list[str] = ["SpecFileDecl", "SpecFileKind", "TemplateConfig"]


SpecFileKind = Literal["markdown"]


@dataclass(frozen=True, kw_only=True, slots=True)
class SpecFileDecl:
    """A single entry in the v2 spec_files manifest.

    Mirrors the per-file declaration shape in
    template_config.schema.json's `spec_files.additionalProperties`:
    a `kind` discriminator whose sole value is `markdown`.
    """

    kind: SpecFileKind


@dataclass(frozen=True, kw_only=True, slots=True)
class TemplateConfig:
    """The template.json wire dataclass.

    Mirrors template_config.schema.json. v1 templates leave
    `spec_files` as None; v2 templates populate it with the
    declared per-file manifest.
    """

    template_format_version: int
    # NewType is structural — `SpecRoot("SPECIFICATION/")`
    # returns the immutable str at definition time and is
    # safely shareable across instances; ruff's RUF009 false-
    # positives the call as mutable-default risk.
    spec_root: SpecRoot = SpecRoot("SPECIFICATION/")  # noqa: RUF009
    spec_files: dict[str, SpecFileDecl] | None = None
    doctor_static_check_modules: list[str] = field(default_factory=list)
    doctor_llm_objective_checks_prompt: str | None = None
    doctor_llm_subjective_checks_prompt: str | None = None
