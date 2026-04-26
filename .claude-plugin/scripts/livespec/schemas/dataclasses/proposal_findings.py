"""Dataclass paired with `proposal_findings.schema.json`.

LLM-output schema for propose-change and critique. Each entry is
a candidate proposal that the wrapper materializes into a
`## Proposal: <name>` section in the resulting proposed-change file.

Distinct from `DoctorFindings` (doctor static-phase output). Per
PROPOSAL.md §"doctor → Static-phase orchestrator" line 2624.

Three-way pairing with `proposal_findings.schema.json` and
`validate/proposal_findings.py`.
"""
from dataclasses import dataclass

__all__: list[str] = [
    "ProposalFinding",
    "ProposalFindings",
]


@dataclass(frozen=True, kw_only=True, slots=True)
class ProposalFinding:
    name: str
    target_spec_files: list[str]
    summary: str
    motivation: str
    proposed_changes: str


@dataclass(frozen=True, kw_only=True, slots=True)
class ProposalFindings:
    findings: list[ProposalFinding]
