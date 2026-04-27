"""Factory for the SubSpecPayload validator (v018 Q1 / v020 Q2).

`make_validator(*, fast_validator=...)` accepts a pre-compiled
fastjsonschema validator (the typed `Validator` from
`livespec.io.fastjsonschema_facade`, with the schema dict's
`$id == "sub_spec_payload.schema.json"`) and returns a closure
that threads the schema validation result through dataclass
construction.

See bootstrap/decisions.md 2026-04-26T09:23:07Z for the
factory-shape rationale.
"""

from __future__ import annotations

from typing import Any

from returns.result import Result

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.sub_spec_payload import (
    SubSpecFile,
    SubSpecPayload,
)
from livespec.types import TypedValidator

__all__: list[str] = [
    "make_validator",
]


def make_validator(
    *,
    fast_validator: TypedValidator[dict[str, Any]],
) -> TypedValidator[SubSpecPayload]:
    """Compose `fast_validator` with `SubSpecPayload` dataclass construction."""

    def validator(
        *,
        payload: dict[str, Any],
    ) -> Result[SubSpecPayload, ValidationError]:
        return fast_validator(payload=payload).map(_to_dataclass)

    return validator


def _to_dataclass(data: dict[str, Any]) -> SubSpecPayload:
    """Construct `SubSpecPayload` from a schema-validated dict.

    `template_name` and `files` are both required by the schema
    (`required: [template_name, files]`), so direct dict access
    is safe. Each `files[]` entry is constructed into `SubSpecFile`
    via list comprehension over the validated dicts.
    """
    return SubSpecPayload(
        template_name=data["template_name"],
        files=[
            SubSpecFile(path=entry["path"], content=entry["content"]) for entry in data["files"]
        ],
    )
