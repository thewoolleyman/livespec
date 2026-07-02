"""Validator for the proposed_change_front_matter wire payload.

Per style doc: factory-shape validator that takes the parsed payload
(a dict from YAML front-matter parsing) and the parsed schema (a dict
from proposed_change_front_matter.schema.json), validates the
payload against the schema via fastjsonschema, and returns
`Result[ProposedChangeFrontMatter, ValidationError]`.

The vendored fastjsonschema raises `JsonSchemaValueException`
on violation; `@safe(exceptions=...)` lifts that onto the
Result track per the canonical pattern.
"""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.proposed_change_front_matter import (
    ImplFollowup,
    ProposedChangeFrontMatter,
    SpecCommitments,
)
from livespec.types import Author, TopicSlug

_Validator = Callable[[dict[str, Any]], dict[str, Any]]
_FASTJSONSCHEMA_FACADE = import_module("livespec.io.fastjsonschema_facade")
_JsonSchemaValueException = cast(
    type[Exception],
    _FASTJSONSCHEMA_FACADE.JsonSchemaValueException,
)
_compile_schema = cast(
    Callable[..., _Validator],
    _FASTJSONSCHEMA_FACADE.compile_schema,
)

__all__: list[str] = ["validate_proposed_change_front_matter"]


def _build_spec_commitments(*, raw: dict[str, Any] | None) -> SpecCommitments | None:
    """Construct the optional SpecCommitments dataclass from a validated payload sub-tree.

    li-8mj2lz, PC #4 sub-proposal 1: the schema enforces shape
    (required `impl_followups[]` list, each entry's `id_hint`
    kebab-case + `description` non-empty, optional `supersedes[]`
    list of kebab-case strings) before this function runs.
    Returns None when the front-matter omits `spec_commitments`
    entirely (the zero-commitment path).
    """
    if raw is None:
        return None
    impl_followups = [
        ImplFollowup(id_hint=entry["id_hint"], description=entry["description"])
        for entry in raw["impl_followups"]
    ]
    supersedes = list(raw.get("supersedes", []))
    return SpecCommitments(impl_followups=impl_followups, supersedes=supersedes)


@safe(exceptions=(_JsonSchemaValueException,))
def _raw_validate(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> ProposedChangeFrontMatter:
    """Decorator-lifted validate-and-construct call.

    Promotes `topic` to `TopicSlug` and `author` to `Author` per
    `check-newtype-domain-primitives`. `created_at` stays plain
    `str` (ISO 8601 datetime). The optional `spec_commitments`
    block lands as the nested `SpecCommitments` dataclass when
    present (li-8mj2lz, PC #4 sub-proposal 1).
    """
    validator = _compile_schema(schema_id="proposed_change_front_matter.schema.json", schema=schema)
    validated = validator(payload)
    return ProposedChangeFrontMatter(
        topic=TopicSlug(validated["topic"]),
        author=Author(validated["author"]),
        created_at=validated["created_at"],
        parent_proposed_change=validated.get("parent_proposed_change"),
        spec_commitments=_build_spec_commitments(raw=validated.get("spec_commitments")),
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
