"""Typed facade for the vendored fastjsonschema package."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeAlias

import fastjsonschema

__all__: list[str] = [
    "JsonSchemaValueException",
    "Schema",
    "Validator",
    "compile_schema",
]

Schema: TypeAlias = dict[str, Any]
Validator: TypeAlias = Callable[[dict[str, Any]], dict[str, Any]]
JsonSchemaValueException = fastjsonschema.JsonSchemaValueException

_COMPILED: dict[str, Validator] = {}


def compile_schema(*, schema_id: str, schema: Schema) -> Validator:
    """Compile `schema` and cache the resulting validator by schema id."""
    compiled = _COMPILED.get(schema_id)
    if compiled is None:
        compiled = fastjsonschema.compile(schema)
        _COMPILED[schema_id] = compiled
    return compiled
