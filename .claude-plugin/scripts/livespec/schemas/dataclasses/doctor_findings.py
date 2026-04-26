"""Dataclass paired with `doctor_findings.schema.json`.

Wraps the list of Finding entries that doctor's static phase
emits to stdout. Distinct from `ProposalFindings` (which is the
propose-change / critique LLM-output schema).

Three-way pairing: this dataclass, `doctor_findings.schema.json`,
and `validate/doctor_findings.py` are co-authoritative.
"""
from dataclasses import dataclass

from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = [
    "DoctorFindings",
]


@dataclass(frozen=True, kw_only=True, slots=True)
class DoctorFindings:
    findings: list[Finding]
