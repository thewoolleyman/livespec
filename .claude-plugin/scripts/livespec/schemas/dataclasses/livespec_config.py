"""Dataclass paired with `livespec_config.schema.json`.

Represents the parsed `.livespec.jsonc` configuration. Every field
has a default that mirrors the JSON Schema default — `LivespecConfig()`
with no kwargs constructs the as-if-missing-file state per
PROPOSAL.md §"Configuration: `.livespec.jsonc` → Absence behavior".

Three-way pairing: this dataclass, `schemas/livespec_config.schema.json`,
and `validate/livespec_config.py` are co-authoritative. Drift is
detected by `check-schema-dataclass-pairing` (v013 M6).
"""

from dataclasses import dataclass

from livespec.types import TemplateName

__all__: list[str] = [
    "LivespecConfig",
]


_DEFAULT_TEMPLATE: TemplateName = TemplateName("livespec")
"""Module-level default for the `template` field. Pre-computing
the `NewType` cast outside the dataclass body avoids RUF009
("function call in dataclass default") — `NewType("X", str)` is a
runtime no-op, but ruff cannot prove that without a per-rule
exception, so the indirection through a module-level constant
keeps the dataclass body clean."""


@dataclass(frozen=True, kw_only=True, slots=True)
class LivespecConfig:
    template: TemplateName = _DEFAULT_TEMPLATE
    template_format_version: int = 1
    post_step_skip_doctor_llm_objective_checks: bool = False
    post_step_skip_doctor_llm_subjective_checks: bool = False
    pre_step_skip_static_checks: bool = False
