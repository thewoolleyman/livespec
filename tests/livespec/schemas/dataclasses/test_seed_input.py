"""Tests for livespec.schemas.dataclasses.seed_input."""

from __future__ import annotations

import dataclasses

import pytest
from livespec.schemas.dataclasses.seed_input import SeedFile, SeedInput
from livespec.schemas.dataclasses.sub_spec_payload import (
    SubSpecFile,
    SubSpecPayload,
)
from livespec.types import TemplateName

__all__: list[str] = []


def test_seed_file_construct() -> None:
    f = SeedFile(path="SPECIFICATION/x.md", content="...")
    assert f.path == "SPECIFICATION/x.md"
    assert f.content == "..."


def test_seed_input_minimal() -> None:
    payload = SeedInput(
        template=TemplateName("livespec"),
        intent="seed the project",
        files=[],
        sub_specs=[],
    )
    assert payload.template == "livespec"
    assert payload.intent == "seed the project"
    assert payload.files == []
    assert payload.sub_specs == []


def test_seed_input_with_files() -> None:
    f = SeedFile(path="a.md", content="A")
    payload = SeedInput(
        template=TemplateName("livespec"),
        intent="...",
        files=[f],
        sub_specs=[],
    )
    assert payload.files == [f]


def test_seed_input_with_sub_specs() -> None:
    """Per v018 Q1 / v020 Q2 — `sub_specs[]` carries per-template payloads."""
    sub = SubSpecPayload(
        template_name="livespec",
        files=[SubSpecFile(path="t/x.md", content="X")],
    )
    payload = SeedInput(
        template=TemplateName("livespec"),
        intent="...",
        files=[],
        sub_specs=[sub],
    )
    assert payload.sub_specs == [sub]


def test_seed_file_is_frozen() -> None:
    f = SeedFile(path="x.md", content="x")
    with pytest.raises(dataclasses.FrozenInstanceError):
        f.path = "y.md"  # type: ignore[misc]


def test_seed_input_is_frozen() -> None:
    payload = SeedInput(
        template=TemplateName("livespec"),
        intent="i",
        files=[],
        sub_specs=[],
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        payload.intent = "changed"  # type: ignore[misc]
