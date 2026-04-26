"""Dataclass paired with `template_config.schema.json` (v011 K5).

Represents the parsed `template.json` from an active template
(built-in or user-provided). The skill reads this to learn the
template's format version, spec_root location, optional doctor
extensibility hooks, and optional LLM-prompt paths.

Three-way pairing: this dataclass,
`schemas/template_config.schema.json`, and
`validate/template_config.py` are co-authoritative. Drift is
detected by `check-schema-dataclass-pairing` (v013 M6).
"""
from dataclasses import dataclass, field

__all__: list[str] = [
    "TemplateConfig",
]


_DEFAULT_SPEC_ROOT = "SPECIFICATION/"
"""Default directory under the repo root for spec files. Used by
templates that follow the conventional layout; templates that
place spec files directly at the repo root override with './'."""


def _empty_check_modules() -> list[str]:
    """Default factory for `doctor_static_check_modules`. Returns a
    fresh empty list per instance to avoid the shared-mutable-default
    pitfall."""
    return []


@dataclass(frozen=True, kw_only=True, slots=True)
class TemplateConfig:
    template_format_version: int
    spec_root: str = _DEFAULT_SPEC_ROOT
    doctor_static_check_modules: list[str] = field(default_factory=_empty_check_modules)
    doctor_llm_objective_checks_prompt: str | None = None
    doctor_llm_subjective_checks_prompt: str | None = None
