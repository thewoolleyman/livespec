"""Validator for the proposal-findings wire payload.

Per style doc: factory-shape validator that takes both the parsed
payload (a dict from JSON parsing) and the parsed schema (a dict
from proposal_findings.schema.json), validates the payload against
the schema via fastjsonschema, and returns
`Result[ProposalFindings, ValidationError]`.

The vendored fastjsonschema raises `JsonSchemaValueException` on
violation; `@safe(exceptions=...)` lifts that onto the Result
track per the canonical pattern.

li-8mj2lz, PC #4 sub-proposal 1: the optional `spec_commitments`
top-level field's shape (kebab-case id_hint, non-empty description,
optional supersedes[]) is enforced by the JSON Schema itself; the
schema-violation path therefore lifts to exit 4 via the existing
`@safe(exceptions=...)` envelope without bespoke wrapper-side
checks. On success this validator constructs the nested
`SpecCommitments` + `ImplFollowup` dataclasses from the validated
payload.
"""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

from returns.result import Result, safe

from livespec.errors import ValidationError
from livespec.schemas.dataclasses.proposal_findings import ProposalFindings
from livespec.schemas.dataclasses.proposed_change_front_matter import (
    ImplFollowup,
    SpecCommitments,
)
from livespec.types import Author

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

__all__: list[str] = ["validate_proposal_findings"]


def _build_spec_commitments(*, raw: dict[str, Any] | None) -> SpecCommitments | None:
    """Construct the optional SpecCommitments dataclass from a validated payload sub-tree.

    The schema enforces shape (required `impl_followups[]` list,
    each entry's `id_hint` kebab-case + `description` non-empty,
    optional `supersedes[]` list of kebab-case strings) before
    this function runs — no defensive narrowing required here.
    Returns None when the wrapper input omits `spec_commitments`
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
def _raw_validate(*, payload: dict[str, Any], schema: dict[str, Any]) -> ProposalFindings:
    """Decorator-lifted validate-and-construct call.

    compile_schema returns a validator function that
    raises JsonSchemaValueException on violation. On success we
    construct ProposalFindings from the validated payload's
    well-known keys.
    """
    validator = _compile_schema(schema_id="proposal_findings.schema.json", schema=schema)
    validated = validator(payload)
    raw_author = validated.get("author")
    raw_spec_commitments = validated.get("spec_commitments")
    return ProposalFindings(
        findings=validated["findings"],
        author=Author(raw_author) if raw_author is not None else None,
        spec_commitments=_build_spec_commitments(raw=raw_spec_commitments),
    )


def validate_proposal_findings(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> Result[ProposalFindings, ValidationError]:
    """Validate the proposal-findings payload against its schema.

    Returns Success(ProposalFindings) on a well-formed payload;
    Failure(ValidationError) with the schema-violation path
    embedded in the message on rejection.
    """
    return _raw_validate(payload=payload, schema=schema).alt(
        lambda exc: ValidationError(f"proposal_findings: {exc}"),
    )
