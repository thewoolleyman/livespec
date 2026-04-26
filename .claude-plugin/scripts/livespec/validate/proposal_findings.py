"""Factory for the proposal_findings validator.

`make_validator(*, fast_validator=...)` accepts a pre-compiled
fastjsonschema validator (with the schema dict's
`$id == "proposal_findings.schema.json"`) and returns a closure
that threads schema validation through dataclass construction.

See bootstrap/decisions.md 2026-04-26T09:23:07Z for the
factory-shape rationale.
"""
from __future__ import annotations

from typing import Any

from returns.result import Result

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.proposal_findings import (
    ProposalFinding,
    ProposalFindings,
)
from livespec.types import TypedValidator

__all__: list[str] = [
    "make_validator",
]



def make_validator(
    *,
    fast_validator: TypedValidator[dict[str, Any]],
) -> TypedValidator[ProposalFindings]:
    """Compose `fast_validator` with `ProposalFindings`."""

    def validator(
        *,
        payload: dict[str, Any],
    ) -> Result[ProposalFindings, ValidationError]:
        return fast_validator(payload=payload).map(_to_dataclass)

    return validator


def _to_dataclass(data: dict[str, Any]) -> ProposalFindings:
    return ProposalFindings(
        findings=[_finding(entry=entry) for entry in data["findings"]],
    )


def _finding(*, entry: dict[str, Any]) -> ProposalFinding:
    return ProposalFinding(
        name=entry["name"],
        target_spec_files=list(entry["target_spec_files"]),
        summary=entry["summary"],
        motivation=entry["motivation"],
        proposed_changes=entry["proposed_changes"],
    )
