"""Pre-livespec-import bootstrap: sys.path setup + Python version check.

Imported by every bin/*.py wrapper before any livespec import. Lives under
bin/ so raise SystemExit is permitted by check-supervisor-discipline.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast

_PLUGIN_NAME = "livespec"
_MARKETPLACE_NAME = "livespec"
_CURRENCY_GATE_FAIL = "fail"
_EXIT_CODE_VERSION_MISMATCH = 127
_EXIT_CODE_STALE_PLUGIN = 78
_CHECKOUT_MODE_MESSAGE = "INFO: running from a repo checkout; plugin-currency gate not applicable\n"
_SHA12_RE = re.compile(r"^[0-9a-f]{12}$")
_CODEX_CACHE_PARENT_PARTS = (".codex", "plugins", "cache", _MARKETPLACE_NAME, _PLUGIN_NAME)


def bootstrap() -> None:
    if sys.version_info < (3, 10):
        _ = sys.stderr.write("livespec requires Python 3.10+; install via your package manager.\n")
        raise SystemExit(_EXIT_CODE_VERSION_MISMATCH)
    _verify_currency()
    bundle_scripts = Path(__file__).resolve().parent.parent
    bundle_vendor = bundle_scripts / "_vendor"
    for path in (bundle_scripts, bundle_vendor):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def _verify_currency() -> None:
    plugin_root = _plugin_root()
    if not _is_installed_plugin_cache_path(plugin_root=plugin_root):
        _ = sys.stderr.write(_CHECKOUT_MODE_MESSAGE)
        return
    running_build_id = _running_build_id(plugin_root=plugin_root)
    expected_build_id = _expected_build_id(plugin_root=plugin_root)
    message = _currency_message(
        running_build_id=running_build_id,
        expected_build_id=expected_build_id,
    )
    if message is None:
        return
    _ = sys.stderr.write(message)
    stale = running_build_id is not None and expected_build_id is not None
    if stale or os.environ.get("LIVESPEC_CURRENCY_GATE") == _CURRENCY_GATE_FAIL:
        raise SystemExit(_EXIT_CODE_STALE_PLUGIN)


def _plugin_root() -> Path:
    env_value = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env_value:
        return Path(env_value)
    return Path(__file__).resolve().parents[2]


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
    plugins = plugin_list.get("plugins")
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
    marketplace_name = plugin.get("marketplace")
    if plugin_name == _PLUGIN_NAME and marketplace_name == _MARKETPLACE_NAME:
        return True
    plugin_id = plugin.get("id")
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


def _is_installed_plugin_cache_path(*, plugin_root: Path) -> bool:
    normalized_plugin_root = _normalize_path(path=plugin_root)
    parts = normalized_plugin_root.parts
    for index, part in enumerate(parts[:-1]):
        if part == "plugins" and parts[index + 1] == "cache":
            return True
    return False


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


def _expected_build_id(*, plugin_root: Path) -> str | None:
    if _is_codex_installed_plugin_cache_path(plugin_root=plugin_root):
        marketplace = Path.home() / ".codex" / ".tmp" / "marketplaces" / _MARKETPLACE_NAME
    else:
        marketplace = Path.home() / ".claude" / "plugins" / "marketplaces" / _MARKETPLACE_NAME
    return _git_rev_parse_head(repository=marketplace)


def _is_codex_installed_plugin_cache_path(*, plugin_root: Path) -> bool:
    parts = _normalize_path(path=plugin_root).parts
    parent_part_count = len(_CODEX_CACHE_PARENT_PARTS)
    return (
        len(parts) > parent_part_count
        and parts[-(parent_part_count + 1) : -1] == _CODEX_CACHE_PARENT_PARTS
    )


def _git_rev_parse_head(*, repository: Path) -> str | None:
    if not repository.exists():
        return None
    try:
        completed = subprocess.run(  # noqa: S603
            ["/usr/bin/git", "-C", str(repository), "rev-parse", "--short=12", "HEAD"],
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    build_id = completed.stdout.strip().lower()
    if not _SHA12_RE.fullmatch(build_id):
        return None
    return build_id


def _currency_message(*, running_build_id: str | None, expected_build_id: str | None) -> str | None:
    if running_build_id is None or expected_build_id is None:
        return (
            "livespec plugin currency could not be verified; running build or pinned "
            "marketplace build is unknown. Set LIVESPEC_CURRENCY_GATE=fail to make "
            "this warning fatal in CI or dispatch.\n"
        )
    if running_build_id == expected_build_id:
        return None
    return (
        f"livespec plugin '{_PLUGIN_NAME}' is stale: running build {running_build_id} "
        f"does not match pinned release build {expected_build_id}. Reload plugins or "
        "run `mise exec -- just ensure-plugins` and restart Claude Code; for Codex, "
        "run `codex plugin marketplace upgrade` and restart the session.\n"
    )


def _read_json_object(*, path: Path) -> dict[str, object] | None:
    try:
        raw = path.read_text(encoding="utf-8")
        loaded = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(loaded, dict):
        return None
    return cast("dict[str, object]", loaded)


def _normalize_path(*, path: Path) -> Path:
    return path.expanduser().resolve(strict=False)
