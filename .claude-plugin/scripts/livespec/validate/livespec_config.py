"""Validator for the livespec_config wire payload.

Per style doc: factory-shape validator that takes the parsed payload
(a dict from JSON parsing) and the parsed schema (a dict from
livespec_config.schema.json), validates the payload against
the schema via fastjsonschema, and returns
`Result[LivespecConfig, ValidationError]`.

The vendored fastjsonschema raises `JsonSchemaValueException` on
violation; `@safe(exceptions=...)` lifts that onto the Result
track per the canonical pattern. fastjsonschema applies the
schema's `default` keywords during validation so the
constructed LivespecConfig always has all fields populated.

`spec_clis` is materialized key-by-key with the dataclass-side
core defaults filling any name the payload omits (per
`contracts.md`: pre-populated with core's reference defaults,
individually overridable).
`orchestrator` materializes to `OrchestratorConfig` when the
section is present (schema-required four keys) and to `None`
when absent. `credential_wrapper` materializes to the payload's
argv-form prefix when present and to `[]` when absent (no
credential wrapper applied). Unknown top-level sections validate
per the schema root's `additionalProperties: true` and are
dropped here — each plugin or sibling consumer validates its own
section on read.
"""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.livespec_config import (
    LivespecConfig,
    OrchestratorConfig,
    SpecClis,
)
from livespec.types import SpecRoot, TemplateName

_Validator = Callable[[dict[str, Any]], dict[str, Any]]
_FASTJSONSCHEMA_FACADE = import_module("livespec.io.fastjsonschema_facade")
_JsonSchemaValueException = cast(
    type[Exception],
    _FASTJSONSCHEMA_FACADE.JsonSchemaValueException,
)
_compile_schema = cast(
    Callable[..., _Validator],
    _FASTJSONSCHEMA_FACADE.compile_schema,
)

__all__: list[str] = ["validate_livespec_config"]


def _build_spec_clis(*, raw: dict[str, Any] | None) -> SpecClis:
    """Materialize the SpecClis dataclass from the validated dict.

    Returns the all-core-defaults SpecClis when the section is
    absent; otherwise overlays the payload's per-operation argv
    overrides onto the core defaults so each CLI is individually
    overridable per `contracts.md`.
    Schema-level validation has already constrained each value
    to a non-empty list of strings.
    """
    defaults = SpecClis()
    if raw is None:
        return defaults
    return SpecClis(
        seed=raw.get("seed", defaults.seed),
        propose_change=raw.get("propose_change", defaults.propose_change),
        revise=raw.get("revise", defaults.revise),
        critique=raw.get("critique", defaults.critique),
        doctor=raw.get("doctor", defaults.doctor),
        prune_history=raw.get("prune_history", defaults.prune_history),
        next=raw.get("next", defaults.next),
    )


def _build_orchestrator(*, raw: dict[str, Any] | None) -> OrchestratorConfig | None:
    """Materialize the optional OrchestratorConfig from the validated dict.

    Returns None when the section is absent (no orchestrator
    configured). When present, schema-level validation has
    already required all four keys, so direct indexing is safe.
    """
    if raw is None:
        return None
    return OrchestratorConfig(
        name=raw["name"],
        spec_reader=raw["spec_reader"],
        gap_capture=raw["gap_capture"],
        drift_capture=raw["drift_capture"],
    )


@safe(exceptions=(_JsonSchemaValueException,))
def _raw_validate(*, payload: dict[str, Any], schema: dict[str, Any]) -> LivespecConfig:
    """Decorator-lifted validate-and-construct call.

    compile_schema returns a validator function that
    raises JsonSchemaValueException on violation. The compiled
    validator applies the schema's `default` keywords, so the
    resulting `validated` dict is fully populated even when the
    input payload was empty or partial. We promote `template` to
    the `TemplateName` NewType and `spec_root` to the `SpecRoot`
    NewType per `check-newtype-domain-primitives`.
    """
    validator = _compile_schema(schema_id="livespec_config.schema.json", schema=schema)
    validated = validator(payload)
    return LivespecConfig(
        template=TemplateName(validated["template"]),
        spec_root=SpecRoot(validated["spec_root"]),
        template_format_version=validated["template_format_version"],
        post_step_skip_doctor_llm_objective_checks=validated[
            "post_step_skip_doctor_llm_objective_checks"
        ],
        post_step_skip_doctor_llm_subjective_checks=validated[
            "post_step_skip_doctor_llm_subjective_checks"
        ],
        post_step_skip_capture_impl_gaps=validated["post_step_skip_capture_impl_gaps"],
        pre_step_skip_static_checks=validated["pre_step_skip_static_checks"],
        pre_step_skip_stale_branch_check=validated["pre_step_skip_stale_branch_check"],
        spec_clis=_build_spec_clis(raw=validated.get("spec_clis")),
        orchestrator=_build_orchestrator(raw=validated.get("orchestrator")),
        credential_wrapper=validated.get("credential_wrapper", []),
    )


def validate_livespec_config(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> Result[LivespecConfig, ValidationError]:
    """Validate the livespec_config payload against its schema.

    Returns Success(LivespecConfig) on a well-formed payload;
    Failure(ValidationError) on rejection (e.g., a malformed
    `spec_clis` entry or a partial `orchestrator` section).
    Unknown top-level sections validate per the schema root's
    `additionalProperties: true`.
    """
    return _raw_validate(payload=payload, schema=schema).alt(
        lambda exc: ValidationError(f"livespec_config: {exc}"),
    )
