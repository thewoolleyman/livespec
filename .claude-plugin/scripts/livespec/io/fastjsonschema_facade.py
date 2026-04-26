"""Typed wrapper over vendored fastjsonschema, plus compile-cache.

Phase 2 placeholder. Real `compile_schema` + `validate` operations
land alongside the first validator that needs them. The
module-level `_COMPILED: dict[str, Callable]` cache (and its
mutation in `compile_schema`) is exempt from `check-global-writes`
per the style doc §"Bootstrap"; `Any` from fastjsonschema is
confined to this facade.
"""

__all__: list[str] = []
