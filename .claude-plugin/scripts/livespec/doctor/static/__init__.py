"""Static-doctor check registry.

Per v022 D7, Phase 3 narrows this registry to the eight checks
implemented at that phase; Phase 7 adds the remaining four. At Phase
2 the registry is empty: every per-check module under this package
exists as a stub but is not yet registered.

The registry is a list of (slug, run) tuples. JSON slug
↔ module filename ↔ check_id is documented per-row in the eventual
populated form (style doc §"File naming and invocation").
"""
from typing import Any

__all__: list[str] = ["CHECKS"]


CHECKS: list[tuple[str, Any]] = []
