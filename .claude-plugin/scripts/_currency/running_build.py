"""Running plugin build detection (installed-plugin registry + Codex plugin list).

Resolves the build the CURRENT session is running from three ordered
sources: the Claude `installed_plugins.json` registry, the Codex
`codex plugin list --json` output, and a 12-hex cache-directory basename
fallback. Stdlib-only.
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import cast

from _currency.expected_build import _git_rev_parse_head
from _currency.locate import (
    _MARKETPLACE_NAME,
    _PLUGIN_NAME,
    _SHA12_RE,
    _is_codex_installed_plugin_cache_path,
    _normalize_path,
    _read_json_object,
)

__all__ = [
    "_codex_local_source_build_id",
    "_codex_plugin_build_id",
    "_codex_plugin_list_json",
    "_codex_plugin_record_matches",
    "_plugin_records_from_mapping",
    "_registry_plugin_build_id",
    "_running_build_id",
    "_running_build_id_from_codex_plugin_list",
    "_running_build_id_from_registry",
]


def _running_build_id(*, plugin_root: Path) -> str | None:
    registry_build_id = _running_build_id_from_registry(plugin_root=plugin_root)
    if registry_build_id is not None:
        return registry_build_id
    codex_plugin_list_build_id = _running_build_id_from_codex_plugin_list(plugin_root=plugin_root)
    if codex_plugin_list_build_id is not None:
        return codex_plugin_list_build_id
    cache_dir_name = plugin_root.name.lower()
    if _SHA12_RE.fullmatch(cache_dir_name):
        return cache_dir_name
    return None


def _running_build_id_from_codex_plugin_list(*, plugin_root: Path) -> str | None:
    if not _is_codex_installed_plugin_cache_path(plugin_root=plugin_root):
        return None
    plugin_list = _codex_plugin_list_json()
    if plugin_list is None:
        return None
    normalized_plugin_root = _normalize_path(path=plugin_root)
    plugins = plugin_list.get("installed") or plugin_list.get("plugins")
    if isinstance(plugins, list):
        plugin_records = cast("list[object]", plugins)
    elif isinstance(plugins, dict):
        plugin_records = _plugin_records_from_mapping(mapping=cast("dict[object, object]", plugins))
    else:
        plugin_records: list[object] = []
    for plugin in plugin_records:
        build_id = _codex_plugin_build_id(
            plugin=plugin, normalized_plugin_root=normalized_plugin_root
        )
        if build_id is not None:
            return build_id
    return None


def _plugin_records_from_mapping(*, mapping: dict[object, object]) -> list[object]:
    records: list[object] = []
    for key, value in mapping.items():
        values = cast("list[object]", value) if isinstance(value, list) else [value]
        for item in values:
            if isinstance(item, dict) and isinstance(key, str):
                item_dict = dict(cast("dict[object, object]", item))
                item_dict["id"] = item_dict.get("id", key)
                records.append(item_dict)
            else:
                records.append(cast("object", item))
    return records


def _codex_plugin_build_id(*, plugin: object, normalized_plugin_root: Path) -> str | None:
    if not isinstance(plugin, dict):
        return None
    plugin_dict = cast("dict[object, object]", plugin)
    if not _codex_plugin_record_matches(
        plugin=plugin_dict, normalized_plugin_root=normalized_plugin_root
    ):
        return None
    for field_name in ("gitCommitSha", "commitSha", "sourceCommitSha", "commit", "buildId"):
        build_id = plugin_dict.get(field_name)
        if isinstance(build_id, str):
            return build_id[:12].lower()
    return _codex_local_source_build_id(plugin=plugin_dict)


def _codex_local_source_build_id(*, plugin: dict[object, object]) -> str | None:
    source = plugin.get("source")
    if not isinstance(source, dict):
        return None
    source_dict = cast("dict[object, object]", source)
    if source_dict.get("source") != "local":
        return None
    source_path = source_dict.get("path")
    if not isinstance(source_path, str):
        return None
    return _git_rev_parse_head(repository=Path(source_path).expanduser())


def _codex_plugin_record_matches(
    *, plugin: dict[object, object], normalized_plugin_root: Path
) -> bool:
    install_path = plugin.get("installPath")
    if (
        isinstance(install_path, str)
        and _normalize_path(path=Path(install_path)) == normalized_plugin_root
    ):
        return True
    plugin_name = plugin.get("name")
    marketplace_name = plugin.get("marketplaceName", plugin.get("marketplace"))
    if plugin_name == _PLUGIN_NAME and marketplace_name == _MARKETPLACE_NAME:
        return True
    plugin_id = plugin.get("pluginId", plugin.get("id"))
    return plugin_id == f"{_PLUGIN_NAME}@{_MARKETPLACE_NAME}"


def _codex_plugin_list_json() -> dict[str, object] | None:
    codex = shutil.which("codex")
    if codex is None:
        return None
    try:
        completed = subprocess.run(  # noqa: S603
            [codex, "plugin", "list", "--json"],
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    try:
        loaded = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(loaded, dict):
        return None
    return cast("dict[str, object]", loaded)


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
