"""LivespecConfig dataclass paired 1:1 with livespec_config.schema.json.

Per style doc: fields match the schema one-to-one in name and Python
type. The dataclass is the type that flows through the railway after
schema validation:
    Result[LivespecConfig, ValidationError]
from validate.livespec_config.validate_livespec_config.

Per `check-newtype-domain-primitives`: `template` uses the
`TemplateName` NewType and `spec_root` uses the `SpecRoot`
NewType from `livespec.types`.

All fields are optional in the schema with documented defaults;
fastjsonschema applies the defaults at validation time so the
dataclass receives them populated. The dataclass-side defaults
mirror the schema's defaults so direct construction (without
going through the validator) still yields the same configured
state.

`spec_clis` carries the seven spec-side CLI names per
`contracts.md`: each is an argv-form array pre-populated with
core's reference default and individually overridable.
`orchestrator` is the optional orchestrator selection per
`contracts.md`: when configured it names the orchestrator plus
its three CLIs; `None` means no orchestrator is configured.
The `${CLAUDE_PLUGIN_ROOT}` placeholder in any argv entry is
expanded at dispatch time, not here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from livespec.types import SpecRoot, TemplateName

__all__: list[str] = [
    "LivespecConfig",
    "OrchestratorConfig",
    "SpecClis",
]


def _default_cli_argv(*, wrapper_filename: str) -> list[str]:
    """Core's reference-default argv for one spec-side CLI.

    Mirrors the per-key `default` arrays declared in
    livespec_config.schema.json byte-for-byte; the schema and
    this factory MUST stay co-authoritative per the
    schema-dataclass-pairing convention.
    """
    return ["python3", f"${{CLAUDE_PLUGIN_ROOT}}/scripts/bin/{wrapper_filename}"]


@dataclass(frozen=True, kw_only=True, slots=True)
class SpecClis:
    """The seven config-named spec-side CLIs.

    Mirrors livespec_config.schema.json's `spec_clis` object.
    Each field is an argv-form array (NOT a shell string),
    defaulting to core's reference wrapper per `contracts.md`.
    Overriding one field selects an alternate implementation of
    that one operation; siblings keep their defaults.
    """

    seed: list[str] = field(
        default_factory=lambda: _default_cli_argv(wrapper_filename="seed.py"),
    )
    propose_change: list[str] = field(
        default_factory=lambda: _default_cli_argv(wrapper_filename="propose_change.py"),
    )
    revise: list[str] = field(
        default_factory=lambda: _default_cli_argv(wrapper_filename="revise.py"),
    )
    critique: list[str] = field(
        default_factory=lambda: _default_cli_argv(wrapper_filename="critique.py"),
    )
    doctor: list[str] = field(
        default_factory=lambda: _default_cli_argv(wrapper_filename="doctor_static.py"),
    )
    prune_history: list[str] = field(
        default_factory=lambda: _default_cli_argv(wrapper_filename="prune_history.py"),
    )
    next: list[str] = field(
        default_factory=lambda: _default_cli_argv(wrapper_filename="next.py"),
    )


@dataclass(frozen=True, kw_only=True, slots=True)
class OrchestratorConfig:
    """The orchestrator selection + its three config-named CLIs.

    Mirrors livespec_config.schema.json's `orchestrator` object.
    All four fields are schema-required when the section is
    present; the section itself is optional
    (`LivespecConfig.orchestrator` is `None` when absent). Per
    `contracts.md` the CLIs are behaviorally undefined here — the
    contract is that they are named and callable.
    """

    name: str
    spec_reader: list[str]
    gap_capture: list[str]
    drift_capture: list[str]


@dataclass(frozen=True, kw_only=True, slots=True)
class LivespecConfig:
    """The `.livespec.jsonc` config wire dataclass.

    Mirrors livespec_config.schema.json: the flat spec-tier
    facts (`template`, `spec_root`, skip flags), the
    `spec_clis` object naming the seven spec-side CLIs, and the
    optional `orchestrator` selection. Unknown top-level
    sections in the payload are tolerated per the schema root's
    `additionalProperties: true` and are NOT carried on this
    dataclass — each plugin or sibling consumer validates its
    own section on read.
    """

    # NewType is structural — `TemplateName("livespec")` returns
    # the immutable str "livespec" at definition time and is
    # safely shareable across instances; ruff's RUF009 false-
    # positives the call as mutable-default risk.
    template: TemplateName = TemplateName("livespec")  # noqa: RUF009
    spec_root: SpecRoot = SpecRoot("SPECIFICATION")  # noqa: RUF009
    template_format_version: int = 1
    post_step_skip_doctor_llm_objective_checks: bool = False
    post_step_skip_doctor_llm_subjective_checks: bool = False
    post_step_skip_capture_impl_gaps: bool = False
    pre_step_skip_static_checks: bool = False
    pre_step_skip_stale_branch_check: bool = False
    spec_clis: SpecClis = field(default_factory=SpecClis)
    orchestrator: OrchestratorConfig | None = None
