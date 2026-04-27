"""Factory for the DoctorFindings validator.

`make_validator(*, fast_validator=...)` accepts a pre-compiled
fastjsonschema validator (the typed `Validator` from
`livespec.io.fastjsonschema_facade`, with the schema dict's
`$id == "doctor_findings.schema.json"`) and returns a closure
that threads the schema validation result through dataclass
construction.

See bootstrap/decisions.md 2026-04-26T09:23:07Z for the
factory-shape rationale.
"""

from __future__ import annotations

from typing import Any, cast

from returns.result import Result

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.doctor_findings import DoctorFindings
from livespec.schemas.dataclasses.finding import Finding, FindingStatus
from livespec.types import CheckId, TypedValidator

__all__: list[str] = [
    "make_validator",
]


def make_validator(
    *,
    fast_validator: TypedValidator[dict[str, Any]],
) -> TypedValidator[DoctorFindings]:
    """Compose `fast_validator` with `DoctorFindings` dataclass construction."""

    def validator(
        *,
        payload: dict[str, Any],
    ) -> Result[DoctorFindings, ValidationError]:
        return fast_validator(payload=payload).map(_to_dataclass)

    return validator


def _to_dataclass(data: dict[str, Any]) -> DoctorFindings:
    """Construct `DoctorFindings` from a schema-validated dict."""
    return DoctorFindings(
        findings=[_finding(entry=entry) for entry in data["findings"]],
    )


def _finding(*, entry: dict[str, Any]) -> Finding:
    return Finding(
        check_id=CheckId(entry["check_id"]),
        status=cast("FindingStatus", entry["status"]),
        message=entry["message"],
        path=entry["path"],
        line=entry["line"],
        spec_root=entry["spec_root"],
    )
