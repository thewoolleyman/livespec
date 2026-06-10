"""Validator for the template_config wire payload.

Per style doc §"Skill layout — `validate/`": factory-shape
validator that takes the parsed payload (a dict from JSON
parsing of template.json) and the parsed schema (a dict from
template_config.schema.json), validates the payload against
the schema via fastjsonschema, and returns
`Result[TemplateConfig, ValidationError]`.

fastjsonschema applies the schema's `default` keywords during
validation so the constructed TemplateConfig has fields
populated even when the input payload was minimal. The
schema's `if/then/else` enforces the v1/v2 invariants:
spec_files REQUIRED for v2, FORBIDDEN for v1.

Per `contracts.md` §"Template manifest wire contract", the
cross-property invariant — every diagram_rendered entry's
`derived_from` MUST resolve to a `kind: diagram_source` entry
in the same manifest — is NOT expressible in JSON Schema
(refs across instance fields). It is enforced here at the
validator layer as a post-schema check; violations surface as
the same `ValidationError` shape as schema-level rejections.
"""

from __future__ import annotations

from typing import Any

import fastjsonschema
from returns.result import Failure, Result, Success, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.template_config import (
    SpecFileDecl,
    SpecFileKind,
    TemplateConfig,
)
from livespec.types import SpecRoot

__all__: list[str] = ["validate_template_config"]


def _build_spec_files(
    *,
    raw: dict[str, Any] | None,
) -> dict[str, SpecFileDecl] | None:
    """Materialize SpecFileDecl entries from the validated dict.

    Returns None when raw is None (v1 templates have no
    manifest). Schema-level validation has already guaranteed
    each value carries a `kind` and (for diagram_rendered) a
    `derived_from`.
    """
    if raw is None:
        return None
    out: dict[str, SpecFileDecl] = {}
    for path, decl in raw.items():
        kind_value: SpecFileKind = decl["kind"]
        derived_from: str | None = decl.get("derived_from")
        out[path] = SpecFileDecl(kind=kind_value, derived_from=derived_from)
    return out


def _check_derived_from_resolves(
    *,
    spec_files: dict[str, SpecFileDecl] | None,
) -> Result[None, ValidationError]:
    """Post-schema cross-property check.

    Every diagram_rendered entry's `derived_from` MUST point at
    a path that exists in spec_files as a `kind: diagram_source`
    entry. JSON Schema cannot express this; we enforce here.
    """
    if spec_files is None:
        return Success(None)
    source_paths: set[str] = {
        path for path, decl in spec_files.items() if decl.kind == "diagram_source"
    }
    for path, decl in spec_files.items():
        if decl.kind != "diagram_rendered":
            continue
        target = decl.derived_from
        if target is None or target not in source_paths:
            return Failure(
                ValidationError(
                    f"template_config: spec_files['{path}'].derived_from "
                    f"= '{target}' does not resolve to a kind: diagram_source "
                    f"entry in spec_files",
                ),
            )
    return Success(None)


@safe(exceptions=(fastjsonschema.JsonSchemaValueException,))
def _raw_validate(*, payload: dict[str, Any], schema: dict[str, Any]) -> TemplateConfig:
    """Decorator-lifted validate-and-construct call.

    Promotes `spec_root` to `SpecRoot` per
    `check-newtype-domain-primitives`. Materializes the
    spec_files manifest into SpecFileDecl instances when
    present.
    """
    validator = fastjsonschema.compile(schema)
    validated = validator(payload)
    return TemplateConfig(
        template_format_version=validated["template_format_version"],
        spec_root=SpecRoot(validated["spec_root"]),
        spec_files=_build_spec_files(raw=validated.get("spec_files")),
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
    Failure(ValidationError) on rejection (schema-level
    structural violations OR the post-schema cross-property
    `derived_from` resolves check).

    The cross-property step composes via an explicit
    pattern-match rather than `.bind` — the returns library's
    KindN higher-kinded types erode flow-narrowing through
    pyright strict on bind chains, and the named-match form is
    the canonical fix.
    """
    schema_result: Result[TemplateConfig, ValidationError] = _raw_validate(
        payload=payload,
        schema=schema,
    ).alt(lambda exc: ValidationError(f"template_config: {exc}"))
    match schema_result:
        case Success(cfg):
            cross_result = _check_derived_from_resolves(spec_files=cfg.spec_files)
            match cross_result:
                case Failure(ValidationError() as err):
                    return Failure(err)
                case _:
                    return schema_result
        case _:
            return schema_result
