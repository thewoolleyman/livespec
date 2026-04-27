"""Factory for the Finding validator (v014 N2).

`make_validator(*, fast_validator=...)` accepts a pre-compiled
fastjsonschema validator (the typed `Validator` from
`livespec.io.fastjsonschema_facade`, with the schema dict's
`$id == "finding.schema.json"`) and returns a closure that
threads the schema validation result through dataclass
construction.

See bootstrap/decisions.md 2026-04-26T09:23:07Z for the
factory-shape rationale.
"""

from __future__ import annotations

from typing import Any, cast

from returns.result import Result

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.finding import Finding, FindingStatus
from livespec.types import CheckId, TypedValidator

__all__: list[str] = [
    "make_validator",
]


def make_validator(
    *,
    fast_validator: TypedValidator[dict[str, Any]],
) -> TypedValidator[Finding]:
    """Compose `fast_validator` with `Finding` dataclass construction."""

    def validator(
        *,
        payload: dict[str, Any],
    ) -> Result[Finding, ValidationError]:
        return fast_validator(payload=payload).map(_to_dataclass)

    return validator


def _to_dataclass(data: dict[str, Any]) -> Finding:
    """Construct `Finding` from a schema-validated dict.

    The schema's `enum: ["pass", "fail", "skipped"]` constrains the
    `status` field to one of three string literals; `cast(FindingStatus, ...)`
    narrows the `str` to the `Literal` type for pyright.
    """
    return Finding(
        check_id=CheckId(data["check_id"]),
        status=cast("FindingStatus", data["status"]),
        message=data["message"],
        path=data["path"],
        line=data["line"],
        spec_root=data["spec_root"],
    )
