"""Factory for the revision front-matter validator.

`make_validator(*, fast_validator=...)` accepts a pre-compiled
fastjsonschema validator (with the schema dict's
`$id == "revision_front_matter.schema.json"`) and returns a
closure that threads schema validation through dataclass
construction.

See bootstrap/decisions.md 2026-04-26T09:23:07Z for the
factory-shape rationale.
"""
from __future__ import annotations

from typing import Any, cast

from returns.result import Result

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.revision_front_matter import (
    Decision,
    RevisionFrontMatter,
)
from livespec.types import Author, TypedValidator

__all__: list[str] = [
    "make_validator",
]



def make_validator(
    *,
    fast_validator: TypedValidator[dict[str, Any]],
) -> TypedValidator[RevisionFrontMatter]:
    """Compose `fast_validator` with `RevisionFrontMatter`."""

    def validator(
        *,
        payload: dict[str, Any],
    ) -> Result[RevisionFrontMatter, ValidationError]:
        return fast_validator(payload=payload).map(_to_dataclass)

    return validator


def _to_dataclass(data: dict[str, Any]) -> RevisionFrontMatter:
    return RevisionFrontMatter(
        proposal=data["proposal"],
        decision=cast("Decision", data["decision"]),
        revised_at=data["revised_at"],
        author_human=data["author_human"],
        author_llm=Author(data["author_llm"]),
    )
