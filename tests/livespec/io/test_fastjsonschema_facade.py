"""Tests for livespec.io.fastjsonschema_facade."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from livespec.io import fastjsonschema_facade

__all__: list[str] = []


def test_compile_schema_caches_compiled_validator_by_schema_id(
    *,
    monkeypatch: Any,
) -> None:
    """Repeated schema-id compilation returns the cached validator."""
    calls: list[dict[str, Any]] = []

    def fake_compile(definition: dict[str, Any]) -> fastjsonschema_facade.Validator:
        calls.append(definition)

        def fake_validator(payload: dict[str, Any]) -> dict[str, Any]:
            return payload

        return fake_validator

    monkeypatch.setattr(fastjsonschema_facade.fastjsonschema, "compile", fake_compile)

    schema_id = f"demo-{uuid4()}.schema.json"
    other_schema_id = f"other-{uuid4()}.schema.json"
    schema = {"$id": schema_id, "type": "object"}
    first = fastjsonschema_facade.compile_schema(
        schema_id=schema_id,
        schema=schema,
    )
    second = fastjsonschema_facade.compile_schema(
        schema_id=schema_id,
        schema={"$id": schema_id, "type": "object", "title": "Ignored"},
    )
    other = fastjsonschema_facade.compile_schema(
        schema_id=other_schema_id,
        schema={"$id": other_schema_id, "type": "object"},
    )

    assert first({"status": "ok"}) == {"status": "ok"}
    assert first is second
    assert first is not other
    assert calls == [
        schema,
        {"$id": other_schema_id, "type": "object"},
    ]
