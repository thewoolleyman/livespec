"""Factory for the seed_input validator.

`make_validator(*, fast_validator=...)` accepts a pre-compiled
fastjsonschema validator (the typed `Validator` from
`livespec.io.fastjsonschema_facade`, with the schema dict's
`$id == "seed_input.schema.json"`) and returns a closure that
threads the schema validation result through dataclass
construction. Per v018 Q1 + v020 Q2, the dataclass carries
`sub_specs: list[SubSpecPayload]`.

See bootstrap/decisions.md 2026-04-26T09:23:07Z for the
factory-shape rationale.
"""

from __future__ import annotations

from typing import Any

from returns.result import Result

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.seed_input import SeedFile, SeedInput
from livespec.schemas.dataclasses.sub_spec_payload import (
    SubSpecFile,
    SubSpecPayload,
)
from livespec.types import TemplateName, TypedValidator

__all__: list[str] = [
    "make_validator",
]


def make_validator(
    *,
    fast_validator: TypedValidator[dict[str, Any]],
) -> TypedValidator[SeedInput]:
    """Compose `fast_validator` with `SeedInput` dataclass construction."""

    def validator(
        *,
        payload: dict[str, Any],
    ) -> Result[SeedInput, ValidationError]:
        return fast_validator(payload=payload).map(_to_dataclass)

    return validator


def _to_dataclass(data: dict[str, Any]) -> SeedInput:
    """Construct `SeedInput` from a schema-validated dict.

    The schema's `required: [template, files, intent, sub_specs]`
    plus `additionalProperties: false` means every key is present
    and well-typed; direct dict access is safe. Sub-spec entries
    are constructed inline via nested list comprehensions because
    the seed_input schema embeds the SubSpecPayload structure
    inline (rather than $ref-ing sub_spec_payload.schema.json) —
    callers that want to validate a standalone SubSpecPayload use
    `validate.sub_spec_payload.make_validator` directly.
    """
    return SeedInput(
        template=TemplateName(data["template"]),
        intent=data["intent"],
        files=[SeedFile(path=entry["path"], content=entry["content"]) for entry in data["files"]],
        sub_specs=[
            SubSpecPayload(
                template_name=sub["template_name"],
                files=[
                    SubSpecFile(path=entry["path"], content=entry["content"])
                    for entry in sub["files"]
                ],
            )
            for sub in data["sub_specs"]
        ],
    )
