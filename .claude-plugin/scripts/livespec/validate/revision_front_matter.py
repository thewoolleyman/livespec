"""Validator for the revision_front_matter wire payload.

Per style doc §"Skill layout — `validate/`": factory-shape
validator that takes the parsed payload (a dict from YAML
front-matter parsing) and the parsed schema (a dict from
revision_front_matter.schema.json), validates the payload
against the schema via fastjsonschema, and returns
`Result[RevisionFrontMatter, ValidationError]`.
"""

from __future__ import annotations

from typing import Any

import fastjsonschema
from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.revision_front_matter import RevisionFrontMatter
from livespec.types import Author

__all__: list[str] = ["validate_revision_front_matter"]


@safe(exceptions=(fastjsonschema.JsonSchemaValueException,))
def _raw_validate(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> RevisionFrontMatter:
    """Decorator-lifted validate-and-construct call.

    Promotes both `author_human` and `author_llm` to `Author`
    per `check-newtype-domain-primitives`.
    """
    validator = fastjsonschema.compile(schema)
    validated = validator(payload)
    return RevisionFrontMatter(
        proposal=validated["proposal"],
        decision=validated["decision"],
        revised_at=validated["revised_at"],
        author_human=Author(validated["author_human"]),
        author_llm=Author(validated["author_llm"]),
    )


def validate_revision_front_matter(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> Result[RevisionFrontMatter, ValidationError]:
    """Validate the revision_front_matter payload against its schema.

    Returns Success(RevisionFrontMatter) on a well-formed
    payload; Failure(ValidationError) on rejection.
    """
    return _raw_validate(payload=payload, schema=schema).alt(
        lambda exc: ValidationError(f"revision_front_matter: {exc}"),
    )
