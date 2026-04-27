"""Tests for livespec.schemas.dataclasses.finding."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from livespec.schemas.dataclasses.finding import Finding, FindingStatus
from livespec.types import CheckId, SpecRoot

__all__: list[str] = []


_LINE_NO = 42


def _make_finding(*, status: FindingStatus = "pass") -> Finding:
    return Finding(
        check_id=CheckId("doctor-template-exists"),
        status=status,
        message="ok",
        path=None,
        line=None,
        spec_root=SpecRoot(Path("/tmp/spec")),
    )


def test_construct_pass() -> None:
    f = _make_finding(status="pass")
    assert f.status == "pass"


def test_construct_fail_with_path_and_line() -> None:
    f = Finding(
        check_id=CheckId("doctor-version-contiguity"),
        status="fail",
        message="gap at v003",
        path="SPECIFICATION/history/v003",
        line=_LINE_NO,
        spec_root=SpecRoot(Path("/tmp/spec")),
    )
    assert f.path == "SPECIFICATION/history/v003"
    assert f.line == _LINE_NO


def test_construct_skipped() -> None:
    f = _make_finding(status="skipped")
    assert f.status == "skipped"


def test_finding_is_frozen() -> None:
    f = _make_finding()
    with pytest.raises(dataclasses.FrozenInstanceError):
        f.status = "fail"  # type: ignore[misc]
