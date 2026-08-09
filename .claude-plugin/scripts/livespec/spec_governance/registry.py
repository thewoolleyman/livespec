"""Compatibility projection for the runtime-owned spec-governance manifest.

The relocated surface is `livespec_runtime.spec_governance`; this module keeps
the old core import path that formerly housed
`livespec_runtime.spec_governance.registry` behavior.
"""

from __future__ import annotations

from typing import TypeAlias

from livespec_runtime.spec_governance import ConfigValueType, ManifestRow, manifest_rows

__all__: list[str] = [
    "CONFIG_KEYS",
    "ConfigKey",
    "ConfigValueType",
    "ManifestRow",
    "manifest_rows",
]

ConfigKey: TypeAlias = ManifestRow
CONFIG_KEYS: tuple[ConfigKey, ...] = tuple(manifest_rows())
