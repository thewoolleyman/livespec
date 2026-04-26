"""Dataclass paired with `finding.schema.json` (v014 N2).

Represents a single doctor-static check Finding. Each check
produces one Finding per spec tree; the orchestrator collects them
into a `DoctorFindings` payload (see `doctor_findings.py`).

`Finding` is moved-from-doctor (per v010 J11) to the validators
layer because its schema is wire-protocol payload — the doctor's
stdout JSON conforms to `finding.schema.json` via
`doctor_findings.schema.json`'s `findings: [Finding, ...]`
wrapping.

Constructor helpers `pass_finding`, `fail_finding`, and
`skipped_finding` are deferred to a later sub-step (or the calling
check modules can construct `Finding` directly with the
appropriate `status` literal — Phase 3 minimum-viable).

Three-way pairing: this dataclass, `finding.schema.json`, and
`validate/finding.py` are co-authoritative.
"""
from dataclasses import dataclass
from typing import Literal

from livespec.types import CheckId

__all__: list[str] = [
    "Finding",
    "FindingStatus",
]


FindingStatus = Literal["pass", "fail", "skipped"]
"""The three v1 finding statuses. Mirrors the schema's
`status` enum."""


@dataclass(frozen=True, kw_only=True, slots=True)
class Finding:
    check_id: CheckId
    status: FindingStatus
    message: str
    path: str | None
    line: int | None
    spec_root: str
