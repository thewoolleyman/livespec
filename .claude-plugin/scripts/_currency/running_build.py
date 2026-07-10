"""Running plugin build detection (Claude installed-plugin registry + Codex config).

Resolves the build the CURRENT session is running from. A Codex install
reads the `last_revision` recorded in `~/.codex/config.toml` (the SHA Codex
last upgraded the marketplace clone to — what native auto-upgrade keys off);
a Claude install reads the `installed_plugins.json` registry, falling back
to a 12-hex cache-directory basename. Stdlib-only.
"""

from pathlib import Path
from typing import cast

from _currency.codex_remote import _codex_last_revision_build_id
from _currency.locate import (
    _SHA12_RE,
    _is_codex_installed_plugin_cache_path,
    _normalize_path,
    _read_json_object,
)

__all__: list[str] = [
    "_registry_plugin_build_id",
    "_running_build_id",
    "_running_build_id_from_registry",
]


def _running_build_id(*, plugin_root: Path) -> str | None:
    if _is_codex_installed_plugin_cache_path(plugin_root=plugin_root):
        return _codex_last_revision_build_id()
    registry_build_id = _running_build_id_from_registry(plugin_root=plugin_root)
    if registry_build_id is not None:
        return registry_build_id
    cache_dir_name = plugin_root.name.lower()
    if _SHA12_RE.fullmatch(cache_dir_name):
        return cache_dir_name
    return None


def _running_build_id_from_registry(*, plugin_root: Path) -> str | None:
    registry_path = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    registry = _read_json_object(path=registry_path)
    if registry is None:
        return None
    plugins = registry.get("plugins")
    if not isinstance(plugins, dict):
        return None
    plugin_records_by_name = cast("dict[object, object]", plugins)
    normalized_plugin_root = _normalize_path(path=plugin_root)
    for plugin_records in plugin_records_by_name.values():
        if not isinstance(plugin_records, list):
            continue
        for plugin in cast("list[object]", plugin_records):
            build_id = _registry_plugin_build_id(
                plugin=plugin,
                normalized_plugin_root=normalized_plugin_root,
            )
            if build_id is not None:
                return build_id
    return None


def _registry_plugin_build_id(*, plugin: object, normalized_plugin_root: Path) -> str | None:
    if not isinstance(plugin, dict):
        return None
    plugin_dict = cast("dict[object, object]", plugin)
    install_path = plugin_dict.get("installPath")
    git_commit_sha = plugin_dict.get("gitCommitSha")
    if not isinstance(install_path, str) or not isinstance(git_commit_sha, str):
        return None
    if _normalize_path(path=Path(install_path)) != normalized_plugin_root:
        return None
    return git_commit_sha[:12].lower()
