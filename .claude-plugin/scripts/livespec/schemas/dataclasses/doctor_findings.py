"""DoctorFindings dataclass paired 1:1 with doctor_findings.schema.json.

Per style doc §"Skill layout — schemas/dataclasses/": fields
match the schema one-to-one in name and Python type. The
dataclass is the type that flows through the railway after
schema validation:
    Result[DoctorFindings, ValidationError]
from validate.doctor_findings.validate_doctor_findings.

The wire shape wraps a list of finding entries (one per check
per spec tree per v014 N2 standalone). Mirroring
RevisionInput.decisions, the nested `findings` items stay as
dicts at validation time — consumers that need typed Finding
instances can validate each item separately via
validate.finding.validate_finding.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__: list[str] = ["DoctorFindings"]


@dataclass(frozen=True, kw_only=True, slots=True)
class DoctorFindings:
    """The doctor static-phase stdout wire dataclass.

    Mirrors doctor_findings.schema.json: top-level `findings`
    list. Each item is a finding-shape dict (paired 1:1 with
    finding.schema.json).
    """

    findings: list[dict[str, object]]
