"""ProposalFindings dataclass paired 1:1 with proposal_findings.schema.json.

Per style doc §"Skill layout — schemas/dataclasses/": fields
match the schema one-to-one in name and Python type. The
dataclass is the type that flows through the railway after
schema validation:
    Result[ProposalFindings, ValidationError]
from validate.proposal_findings.validate_proposal_findings.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__: list[str] = ["ProposalFindings"]


@dataclass(frozen=True, kw_only=True, slots=True)
class ProposalFindings:
    """The proposal-findings wire dataclass.

    Mirrors proposal_findings.schema.json: top-level `findings`
    list of objects (each with `name`, `target_spec_files`,
    `summary`, `motivation`, `proposed_changes` per the schema).
    """

    findings: list[dict[str, object]]
