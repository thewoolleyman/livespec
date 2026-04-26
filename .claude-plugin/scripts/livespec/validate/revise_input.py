"""Factory for the revise_input validator.

`make_validator(*, fast_validator=...)` accepts a pre-compiled
fastjsonschema validator (with the schema dict's
`$id == "revise_input.schema.json"`) and returns a closure that
threads schema validation through dataclass construction.

See bootstrap/decisions.md 2026-04-26T09:23:07Z for the
factory-shape rationale.
"""
from __future__ import annotations

from typing import Any, cast

from returns.result import Result

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.revise_input import (
    Decision,
    ProposalDecision,
    ResultingFile,
    ReviseInput,
)
from livespec.types import Author, TopicSlug, TypedValidator

__all__: list[str] = [
    "make_validator",
]



def make_validator(
    *,
    fast_validator: TypedValidator[dict[str, Any]],
) -> TypedValidator[ReviseInput]:
    """Compose `fast_validator` with `ReviseInput`."""

    def validator(
        *,
        payload: dict[str, Any],
    ) -> Result[ReviseInput, ValidationError]:
        return fast_validator(payload=payload).map(_to_dataclass)

    return validator


def _to_dataclass(data: dict[str, Any]) -> ReviseInput:
    raw_author = data.get("author")
    return ReviseInput(
        author=Author(raw_author) if raw_author else None,
        decisions=[_decision(entry=entry) for entry in data["decisions"]],
    )


def _decision(*, entry: dict[str, Any]) -> ProposalDecision:
    return ProposalDecision(
        proposal_topic=TopicSlug(entry["proposal_topic"]),
        decision=cast("Decision", entry["decision"]),
        rationale=entry["rationale"],
        modifications=entry.get("modifications"),
        resulting_files=[
            ResultingFile(path=f["path"], content=f["content"])
            for f in entry.get("resulting_files", [])
        ],
    )
