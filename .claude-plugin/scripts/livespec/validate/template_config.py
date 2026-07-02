"""Validator for the template_config wire payload.

Per style doc: factory-shape validator that takes the parsed payload
(a dict from JSON parsing of template.json) and the parsed schema
(a dict from template_config.schema.json), validates the payload
against the schema via fastjsonschema, and returns
`Result[TemplateConfig, ValidationError]`.

fastjsonschema applies the schema's `default` keywords during
validation so the constructed TemplateConfig has fields
populated even when the input payload was minimal. The
schema's `if/then/else` enforces the v1/v2 invariants:
spec_files REQUIRED for v2, FORBIDDEN for v1. Each manifest
entry's sole legal `kind` is `markdown`; the schema enum
rejects any other value.
"""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.template_config import (
    SpecFileDecl,
    SpecFileKind,
    TemplateConfig,
)
from livespec.types import SpecRoot

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

__all__: list[str] = ["validate_template_config"]


def _build_spec_files(
    *,
    raw: dict[str, Any] | None,
) -> dict[str, SpecFileDecl] | None:
    """Materialize SpecFileDecl entries from the validated dict.

    Returns None when raw is None (v1 templates have no
    manifest). Schema-level validation has already guaranteed
    each value carries a `markdown` `kind`.
    """
    if raw is None:
        return None
    out: dict[str, SpecFileDecl] = {}
    for path, decl in raw.items():
        kind_value: SpecFileKind = decl["kind"]
        out[path] = SpecFileDecl(kind=kind_value)
    return out


@safe(exceptions=(_JsonSchemaValueException,))
def _raw_validate(*, payload: dict[str, Any], schema: dict[str, Any]) -> TemplateConfig:
    """Decorator-lifted validate-and-construct call.

    Promotes `spec_root` to `SpecRoot` per
    `check-newtype-domain-primitives`. Materializes the
    spec_files manifest into SpecFileDecl instances when
    present.
    """
    validator = _compile_schema(schema_id="template_config.schema.json", schema=schema)
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
    Failure(ValidationError) on any schema-level structural
    violation (including a manifest entry whose `kind` is not
    `markdown`).
    """
    return _raw_validate(payload=payload, schema=schema).alt(
        lambda exc: ValidationError(f"template_config: {exc}"),
    )
