"""Validator for the proposed_change_front_matter wire payload.

Per style doc §"Skill layout — `validate/`": factory-shape
validator that takes the parsed payload (a dict from YAML
front-matter parsing) and the parsed schema (a dict from
proposed_change_front_matter.schema.json), validates the
payload against the schema via fastjsonschema, and returns
`Result[ProposedChangeFrontMatter, ValidationError]`.

The vendored fastjsonschema raises `JsonSchemaValueException`
on violation; `@safe(exceptions=...)` lifts that onto the
Result track per the canonical pattern.
"""

from __future__ import annotations

from typing import Any

import fastjsonschema
from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.proposed_change_front_matter import (
    ProposedChangeFrontMatter,
)
from livespec.types import Author, TopicSlug

__all__: list[str] = ["validate_proposed_change_front_matter"]


@safe(exceptions=(fastjsonschema.JsonSchemaValueException,))
def _raw_validate(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> ProposedChangeFrontMatter:
    """Decorator-lifted validate-and-construct call.

    Promotes `topic` to `TopicSlug` and `author` to `Author` per
    `check-newtype-domain-primitives`. `created_at` stays plain
    `str` (ISO 8601 datetime).
    """
    validator = fastjsonschema.compile(schema)
    validated = validator(payload)
    return ProposedChangeFrontMatter(
        topic=TopicSlug(validated["topic"]),
        author=Author(validated["author"]),
        created_at=validated["created_at"],
    )


def validate_proposed_change_front_matter(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> Result[ProposedChangeFrontMatter, ValidationError]:
    """Validate the proposed_change_front_matter payload against its schema.

    Returns Success(ProposedChangeFrontMatter) on a well-formed
    payload; Failure(ValidationError) on rejection (e.g.,
    invalid kebab-case topic, missing required field).
    """
    return _raw_validate(payload=payload, schema=schema).alt(
        lambda exc: ValidationError(f"proposed_change_front_matter: {exc}"),
    )
