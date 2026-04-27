"""Tests for livespec.schemas.dataclasses.doctor_findings."""

from __future__ import annotations

from pathlib import Path

from livespec.schemas.dataclasses.doctor_findings import DoctorFindings
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = []


def test_empty_findings_constructible() -> None:
    payload = DoctorFindings(findings=[])
    assert payload.findings == []


def test_findings_carries_entries() -> None:
    finding = Finding(
        check_id=CheckId("doctor-out-of-band-edits"),
        status="pass",
        message="ok",
        path=None,
        line=None,
        spec_root=SpecRoot(Path("/tmp/spec")),
    )
    payload = DoctorFindings(findings=[finding])
    assert payload.findings == [finding]
