"""Plugin-root, cache-path detection, and JSON-read helpers (stdlib-only).

The leaf of the pre-import `_currency` gate package: only stdlib imports,
no `_currency` siblings, so importing it never drags in the vendor path or
the `livespec` package.
"""

import json
import os
import re
from pathlib import Path
from typing import cast

__all__: list[str] = [
    "_MARKETPLACE_NAME",
    "_PLUGIN_NAME",
    "_SHA12_RE",
    "_is_codex_installed_plugin_cache_path",
    "_is_installed_plugin_cache_path",
    "_normalize_path",
    "_plugin_root",
    "_read_json_object",
]

_PLUGIN_NAME = "livespec"
_MARKETPLACE_NAME = "livespec"
_SHA12_RE = re.compile(r"^[0-9a-f]{12}$")
_CODEX_CACHE_PARENT_PARTS = (".codex", "plugins", "cache", _MARKETPLACE_NAME, _PLUGIN_NAME)


def _plugin_root() -> Path:
    env_value = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env_value:
        return Path(env_value)
    return Path(__file__).resolve().parents[2]


def _normalize_path(*, path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _read_json_object(*, path: Path) -> dict[str, object] | None:
    try:
        raw = path.read_text(encoding="utf-8")
        loaded = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(loaded, dict):
        return None
    return cast("dict[str, object]", loaded)


def _is_installed_plugin_cache_path(*, plugin_root: Path) -> bool:
    normalized_plugin_root = _normalize_path(path=plugin_root)
    parts = normalized_plugin_root.parts
    for index, part in enumerate(parts[:-1]):
        if part == "plugins" and parts[index + 1] == "cache":
            return True
    return False


def _is_codex_installed_plugin_cache_path(*, plugin_root: Path) -> bool:
    parts = _normalize_path(path=plugin_root).parts
    parent_part_count = len(_CODEX_CACHE_PARENT_PARTS)
    return (
        len(parts) > parent_part_count
        and parts[-(parent_part_count + 1) : -1] == _CODEX_CACHE_PARENT_PARTS
    )
