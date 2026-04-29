"""Tests for livespec.schemas.dataclasses.sub_spec_payload."""

from __future__ import annotations

import dataclasses

import pytest
from livespec.schemas.dataclasses.sub_spec_payload import (
    SubSpecFile,
    SubSpecPayload,
)

__all__: list[str] = []


def test_sub_spec_file_construct() -> None:
    f = SubSpecFile(path="SPECIFICATION/templates/livespec/x.md", content="...")
    assert f.path == "SPECIFICATION/templates/livespec/x.md"
    assert f.content == "..."


def test_sub_spec_payload_empty_files() -> None:
    payload = SubSpecPayload(template_name="livespec", files=[])
    assert payload.template_name == "livespec"
    assert payload.files == []


def test_sub_spec_payload_with_files() -> None:
    a = SubSpecFile(path="a.md", content="A")
    b = SubSpecFile(path="b.md", content="B")
    payload = SubSpecPayload(template_name="minimal", files=[a, b])
    assert payload.template_name == "minimal"
    assert payload.files == [a, b]


def test_sub_spec_file_is_frozen() -> None:
    f = SubSpecFile(path="x.md", content="x")
    with pytest.raises(dataclasses.FrozenInstanceError):
        f.path = "y.md"  # type: ignore[misc]


def test_sub_spec_payload_is_frozen() -> None:
    payload = SubSpecPayload(template_name="livespec", files=[])
    with pytest.raises(dataclasses.FrozenInstanceError):
        payload.template_name = "minimal"  # type: ignore[misc]
