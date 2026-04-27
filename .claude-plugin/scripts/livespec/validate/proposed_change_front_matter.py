"""Factory for the proposed-change front-matter validator.

`make_validator(*, fast_validator=...)` accepts a pre-compiled
fastjsonschema validator (with the schema dict's
`$id == "proposed_change_front_matter.schema.json"`) and returns
a closure that threads schema validation through dataclass
construction.

See bootstrap/decisions.md 2026-04-26T09:23:07Z for the
factory-shape rationale.
"""

from __future__ import annotations

from typing import Any

from returns.result import Result

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.proposed_change_front_matter import (
    ProposedChangeFrontMatter,
)
from livespec.types import Author, TopicSlug, TypedValidator

__all__: list[str] = [
    "make_validator",
]


def make_validator(
    *,
    fast_validator: TypedValidator[dict[str, Any]],
) -> TypedValidator[ProposedChangeFrontMatter]:
    """Compose `fast_validator` with `ProposedChangeFrontMatter`."""

    def validator(
        *,
        payload: dict[str, Any],
    ) -> Result[ProposedChangeFrontMatter, ValidationError]:
        return fast_validator(payload=payload).map(_to_dataclass)

    return validator


def _to_dataclass(data: dict[str, Any]) -> ProposedChangeFrontMatter:
    return ProposedChangeFrontMatter(
        topic=TopicSlug(data["topic"]),
        author=Author(data["author"]),
        created_at=data["created_at"],
    )
