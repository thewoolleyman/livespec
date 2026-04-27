"""Typed wrapper over vendored fastjsonschema, plus compile-cache.

`io/` hosts typed facades over vendored libraries whose surface
types are not strict-pyright-clean. The vendored `fastjsonschema`
returns `Callable[[Any], Any]` from `compile()`; this facade narrows
the surface to a typed `Validator` that returns
`Result[dict, ValidationError]` and centralizes the
`JsonSchemaException` → `ValidationError` mapping at a single
io/ location.

Compile results are cached on `$id` per style doc lines 1010-1022:
> The facade holds a module-level `_COMPILED: dict[str, Callable]
> = {}` keyed on `$id` to dedupe compiles across calls.
> `functools.lru_cache` can't be used directly (dicts are
> unhashable), and a module-level cache would trip
> `check-global-writes` in pure code — so the cache lives in the
> impure facade layer and is explicitly exempted.

The `_COMPILED` cache and its mutation in `compile_schema` are
exempt from `check-global-writes` per the explicit list in style
doc §"Structured logging → Bootstrap" lines 1497-1506.

`compile_schema` itself is logically pure (no I/O). It lives in
`io/` because that is the canonical location for typed
vendored-lib glue per style doc line 672-685, and because the
cache mutation is the one impure operation it performs. The
validator it returns is fully pure: it returns `Result` (not
`IOResult`); it constructs `ValidationError` instances and ships
them via `Failure(...)` without raising (LivespecError raise
sites stay confined to the rest of `io/**`).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, TypeAlias

import fastjsonschema
from returns.result import Failure, Result, Success

from livespec.errors import ValidationError
from livespec.types import SchemaId, TypedValidator

__all__: list[str] = [
    "Validator",
    "compile_schema",
]


Validator: TypeAlias = TypedValidator[dict[str, Any]]
"""A compiled JSON Schema validator (keyword-only call surface).

Calling `validator(payload=<dict>)` returns:

- `Success(data)` when the object conforms to the schema (the
  validator returns the same dict the caller passed in; the
  fastjsonschema-generated validator's coercions, if any, are
  preserved).
- `Failure(ValidationError(<message>))` when the object does not
  conform. The message names the schema's `$id` so the validate/
  caller can attribute the failure without the data flow needing
  to thread the schema identity separately.

The validator does NOT raise for schema-non-conformance; it ships
the failure through `Failure`. This keeps validation pure (no
exception flow) and keeps `LivespecError` raise-sites confined to
the rest of `io/**`.

Type alias for `TypedValidator[dict[str, Any]]` from
`livespec.types` — Protocol-based keyword-only callable, required
because `Callable[[X], Y]` cannot express keyword-only call
shapes under pyright strict mode."""


_COMPILED: dict[str, Validator] = {}
"""Module-level compile cache keyed on schema `$id`.

Mutation in `compile_schema` is explicitly exempt from
`check-global-writes` per the exemption list at style doc lines
1497-1506."""


def compile_schema(
    *,
    schema_id: SchemaId,
    schema: Mapping[str, Any],
) -> Validator:
    """Compile `schema` to a typed validator (cached on `schema_id`).

    The caller passes `schema_id` explicitly rather than extracting
    `schema["$id"]` so the cache lookup is one dict membership check.
    Callers that have already loaded the schema dict from disk via
    `livespec/io/fs.py::read_text` + `livespec/parse/jsonc.py`
    typically know the `$id` from the same load.

    Returns the cached validator on cache hit; compiles, caches,
    and returns a new validator on cache miss.
    """
    cached = _COMPILED.get(schema_id)
    if cached is not None:
        return cached

    raw: Callable[[Any], Any] = fastjsonschema.compile(dict(schema))

    def validator(
        *,
        payload: dict[str, Any],
    ) -> Result[dict[str, Any], ValidationError]:
        try:
            raw(payload)
        except fastjsonschema.JsonSchemaException as e:
            return Failure(
                ValidationError(
                    f"schema {schema_id} validation failed: {e.message}",
                ),
            )
        return Success(payload)

    _COMPILED[schema_id] = validator
    return validator
