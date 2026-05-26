"""ProposalFindings dataclass paired 1:1 with proposal_findings.schema.json.

Per style doc §"Skill layout — schemas/dataclasses/": fields
match the schema one-to-one in name and Python type. The
dataclass is the type that flows through the railway after
schema validation:
    Result[ProposalFindings, ValidationError]
from validate.proposal_findings.validate_proposal_findings.

The `spec_commitments` optional block uses the same `SpecCommitments`
nested dataclass authored under
`proposed_change_front_matter.py` (li-8mj2lz, PC #4 sub-proposal 1) —
the field is identically shaped on the wrapper's input payload and on
the resulting file's front-matter, so the dataclass is shared between
the two paired files rather than duplicated.
"""

from __future__ import annotations

from dataclasses import dataclass

from livespec.schemas.dataclasses.proposed_change_front_matter import SpecCommitments
from livespec.types import Author

__all__: list[str] = ["ProposalFindings"]


@dataclass(frozen=True, kw_only=True, slots=True)
class ProposalFindings:
    """The proposal-findings wire dataclass.

    Mirrors proposal_findings.schema.json: top-level `findings`
    list of objects (each with `name`, `target_spec_files`,
    `summary`, `motivation`, `proposed_changes` per the schema)
    plus an optional file-level `author` LLM self-declaration
    (canonical NewType per `check-newtype-domain-primitives`)
    consumed by the unified author-precedence chain, plus an
    optional `spec_commitments` block (li-8mj2lz, PC #4
    sub-proposal 1) carrying the spec→impl commitment declaration
    threaded through to the resulting file's YAML front-matter.
    """

    findings: list[dict[str, object]]
    author: Author | None = None
    spec_commitments: SpecCommitments | None = None
