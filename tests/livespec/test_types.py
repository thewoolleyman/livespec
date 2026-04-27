"""Tests for livespec.types.

Covers the NewType aliases (zero-runtime-cost type aliases),
the `@rop_pipeline` marker decorator (runtime no-op, AST-enforced
shape), and the `TypedValidator` Protocol's keyword-only call shape.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from returns.result import Failure, Result, Success

from livespec.errors import ValidationError
from livespec.types import (
    Author,
    CheckId,
    RunId,
    SchemaId,
    SpecRoot,
    TemplateName,
    TopicSlug,
    TypedValidator,
    VersionTag,
    rop_pipeline,
)

__all__: list[str] = []


def test_newtype_aliases_are_runtime_identity() -> None:
    """NewType is a pure runtime no-op; the alias-call returns the value unchanged."""
    assert CheckId("doctor-out-of-band-edits") == "doctor-out-of-band-edits"
    assert RunId("a-uuid") == "a-uuid"
    assert TopicSlug("my-topic") == "my-topic"
    assert SchemaId("seed_input.schema.json") == "seed_input.schema.json"
    assert TemplateName("livespec") == "livespec"
    assert Author("you@example.com") == "you@example.com"
    assert VersionTag("v001") == "v001"


def test_specroot_wraps_path() -> None:
    """SpecRoot wraps `Path` rather than `str`; runtime equality uses pathlib semantics."""
    p = Path("/tmp/spec")
    wrapped = SpecRoot(p)
    assert wrapped == p
    assert isinstance(wrapped, Path)


def test_rop_pipeline_returns_class_unchanged() -> None:
    """@rop_pipeline is a marker — runtime no-op."""

    @rop_pipeline
    class Demo:
        def run(self, *, value: int) -> int:
            return value + 1

    instance = Demo()
    assert instance.run(value=2) == 3
    assert Demo.__name__ == "Demo"


def test_rop_pipeline_does_not_change_identity() -> None:
    class Original:
        pass

    decorated = rop_pipeline(Original)
    assert decorated is Original


def test_typed_validator_protocol_accepts_kw_only_callable() -> None:
    """A function matching `TypedValidator[T]`'s call shape is structurally compatible."""

    def validator(*, payload: dict[str, Any]) -> Result[str, ValidationError]:
        if "name" in payload:
            return Success(str(payload["name"]))
        return Failure(ValidationError("name missing"))

    accepted: TypedValidator[str] = validator
    success = accepted(payload={"name": "example"})
    failure = accepted(payload={})
    assert success == Success("example")
    assert isinstance(failure, Failure)
