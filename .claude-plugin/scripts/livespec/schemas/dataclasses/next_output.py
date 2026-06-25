"""Next-output dataclasses paired 1:1 with next_output.schema.json.

Per style doc: fields match the schema one-to-one in name and Python
type. The dataclasses are the types that flow through the railway
from the ranker into the supervisor's JSON-emit stage:
    Result[NextOutput, ValidationError]
from validate.next_output.validate_next_output.

Per `SPECIFICATION/contracts.md`: the payload carries two
top-level keys — `candidates` (array of candidate objects) and
`pagination` (offset/limit echo + total + has_more). `action`
and `urgency` are typed as `str` (not `Literal[...]`) because
fastjsonschema enforces the enum membership at schema-validation
time; the schema is the wire contract and the dataclasses mirror
its plain shape. No NewType applies under
`check-newtype-domain-primitives`: no field's name matches the
registered canonical-target list.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__: list[str] = ["NextCandidate", "NextOutput", "NextPagination"]


@dataclass(frozen=True, kw_only=True, slots=True)
class NextCandidate:
    """One ripe-candidate entry in the `candidates` array.

    Mirrors the schema's `candidates.items`: required `action`,
    `reason`, `urgency`; optional `target` (None ⇔ the key is
    omitted from the serialized JSON object, e.g. for
    `prune-history` candidates that address a version range
    rather than one item).
    """

    action: str
    reason: str
    urgency: str
    target: str | None = None


@dataclass(frozen=True, kw_only=True, slots=True)
class NextPagination:
    """The `pagination` block of the `/livespec:next` payload.

    Mirrors the schema's `pagination` object: `offset` and
    `limit` echo the CLI flags; `total` counts ripe candidates
    BEFORE offset/limit are applied; `has_more` is `true` iff
    `offset + len(candidates) < total`.
    """

    offset: int
    limit: int
    total: int
    has_more: bool


@dataclass(frozen=True, kw_only=True, slots=True)
class NextOutput:
    """The `/livespec:next` stdout payload wire dataclass.

    Mirrors next_output.schema.json: required `candidates` (a
    tuple of NextCandidate, possibly empty — the empty tuple IS
    the no-work signal) and `pagination`. Constructed by the
    pagination stage; serialized to JSON on stdout by the
    supervisor.
    """

    candidates: tuple[NextCandidate, ...]
    pagination: NextPagination
