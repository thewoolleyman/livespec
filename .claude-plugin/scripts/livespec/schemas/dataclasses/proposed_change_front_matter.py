"""ProposedChangeFrontMatter dataclass paired 1:1 with proposed_change_front_matter.schema.json.

Per style doc §"Skill layout — schemas/dataclasses/": fields
match the schema one-to-one in name and Python type. The
dataclass is the type that flows through the railway after
schema validation:
  Result[ProposedChangeFrontMatter, ValidationError]
from validate.proposed_change_front_matter.validate_proposed_change_front_matter.

Per `check-newtype-domain-primitives`: `topic` uses the
`TopicSlug` NewType (added at cycle 3d) and `author` uses the
`Author` NewType (added at ). `created_at` is plain
`str` (ISO 8601 datetime; no canonical NewType for timestamps
in this iteration).

`SpecCommitments` + `ImplFollowup` nested dataclasses mirror the
optional `spec_commitments` block per spec.md §"Proposed-change and
revision file formats" → "Spec→impl commitment declaration" (li-8mj2lz,
PC #4 sub-proposal 1). They are also re-imported by
`proposal_findings.py` so the same nested types flow through both the
wrapper's input payload validation and the file front-matter
validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from livespec.types import Author, TopicSlug

__all__: list[str] = ["ImplFollowup", "ProposedChangeFrontMatter", "SpecCommitments"]


@dataclass(frozen=True, kw_only=True, slots=True)
class ImplFollowup:
    """A single impl-side commitment entry declared in `spec_commitments.impl_followups[]`.

    Mirrors the `impl_followups[]` item shape in
    `proposed_change_front_matter.schema.json` (and the same shape in
    `proposal_findings.schema.json`): a non-empty kebab-case `id_hint`
    pairing the eventual work-item to this propose-change, and a
    non-empty free-text `description` of the impl change required
    after the propose-change is revised in.
    """

    id_hint: str
    description: str


@dataclass(frozen=True, kw_only=True, slots=True)
class SpecCommitments:
    """The optional `spec_commitments` block per spec.md §"Spec→impl commitment declaration".

    `impl_followups` is the required (when the block is present) list
    of `ImplFollowup` entries. `supersedes` is the optional list of
    earlier `id_hint` values this propose-change absorbs or revokes;
    the `unresolved-spec-commitment` doctor invariant honors this
    list when computing coverage.
    """

    impl_followups: list[ImplFollowup]
    supersedes: list[str] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True, slots=True)
class ProposedChangeFrontMatter:
    """The proposed-change YAML front-matter wire dataclass.

    Mirrors proposed_change_front_matter.schema.json: required
    `topic` (kebab-case slug), `author` identifier, and
    `created_at` UTC ISO-8601 datetime. Optional
    `parent_proposed_change` carries the canonical topic of a
    parent / coordinating-epic proposed change (per PC #2 of
    v081, coordinating-epic-stale-revise-enforcement). Optional
    `spec_commitments` block per spec.md §"Spec→impl commitment
    declaration" (li-8mj2lz, PC #4 sub-proposal 1).
    """

    topic: TopicSlug
    author: Author
    created_at: str
    parent_proposed_change: str | None = None
    spec_commitments: SpecCommitments | None = None
