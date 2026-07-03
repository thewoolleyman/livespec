"""Claude Code installed-plugin registry cleanup helpers for repo janitors."""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

_VENDOR_DIR = Path(__file__).resolve().parent.parent / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  -- vendor-path-aware import after sys.path insert.

__all__: list[str] = ["prune_dead_project_plugin_entries"]

_INSTALLED_PLUGINS_REGISTRY_VERSION = 2


def _installed_plugins_registry_path() -> Path:
    """Return the Claude Code installed-plugins registry path for the current HOME."""
    return Path.home() / ".claude" / "plugins" / "installed_plugins.json"


def _is_project_entry_with_dead_path(*, entry: dict[str, Any]) -> bool:
    """Return True for project-scoped plugin entries whose project path is gone."""
    project_path = entry.get("projectPath")
    return (
        entry.get("scope") == "project"
        and isinstance(project_path, str)
        and project_path != ""
        and not Path(project_path).exists()
    )


def _registry_timestamp() -> str:
    """Return a filesystem-safe UTC timestamp for backup filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _load_plugin_registry(
    *, registry_path: Path, log: structlog.stdlib.BoundLogger
) -> dict[str, Any] | None:
    """Load Claude Code's installed-plugins registry, or warn and no-op."""
    if not registry_path.exists():
        return None
    try:
        raw = cast(object, json.loads(registry_path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as error:
        log.warning(
            "installed_plugins.json is not valid JSON; skipping dead project plugin sweep",
            path=str(registry_path),
            error=str(error),
        )
        return None
    if not isinstance(raw, dict):
        log.warning(
            "installed_plugins.json has unrecognized shape; skipping dead project plugin sweep",
            path=str(registry_path),
        )
        return None
    return cast(dict[str, Any], raw)


def _validate_plugin_registry(
    *, registry: dict[str, Any], registry_path: Path, log: structlog.stdlib.BoundLogger
) -> dict[str, list[dict[str, Any]]] | None:
    """Return the typed v2 `plugins` map, or warn and no-op."""
    raw_plugins = registry.get("plugins")
    if registry.get("version") != _INSTALLED_PLUGINS_REGISTRY_VERSION or not isinstance(
        raw_plugins, dict
    ):
        log.warning(
            "installed_plugins.json is not v2 shape; skipping dead project plugin sweep",
            path=str(registry_path),
        )
        return None
    plugins = cast(dict[object, object], raw_plugins)
    entries_message = (
        "installed_plugins.json has unrecognized plugin entries; skipping dead project plugin sweep"
    )
    entry_message = (
        "installed_plugins.json has unrecognized plugin entry; skipping dead project plugin sweep"
    )
    typed_plugins: dict[str, list[dict[str, Any]]] = {}
    for plugin_id, entries in plugins.items():
        if not isinstance(plugin_id, str) or not isinstance(entries, list):
            log.warning(entries_message, path=str(registry_path))
            return None
        typed_entries: list[dict[str, Any]] = []
        for entry in cast(list[object], entries):
            if not isinstance(entry, dict):
                log.warning(
                    entry_message,
                    path=str(registry_path),
                    plugin_id=plugin_id,
                )
                return None
            typed_entries.append(cast(dict[str, Any], entry))
        typed_plugins[plugin_id] = typed_entries
    return typed_plugins


def prune_dead_project_plugin_entries(*, dry_run: bool) -> list[str]:
    """Prune Claude Code project-scope plugin entries whose project paths are gone.

    Returns the sorted removed-entry descriptions (`<plugin id>:<path>`).
    Under `dry_run`, reports the would-remove entries without mutating
    the registry or writing a backup. Unrecognized registry formats are
    warning-only no-ops so the caller remains conservative.
    """
    log = structlog.get_logger("claude_plugin_registry")
    registry_path = _installed_plugins_registry_path()
    registry = _load_plugin_registry(registry_path=registry_path, log=log)
    if registry is None:
        return []
    plugins = _validate_plugin_registry(registry=registry, registry_path=registry_path, log=log)
    if plugins is None:
        return []

    removed: list[str] = []
    pruned_plugins: dict[str, list[dict[str, Any]]] = {}
    for plugin_id, entries in plugins.items():
        kept_entries: list[dict[str, Any]] = []
        for entry in entries:
            if _is_project_entry_with_dead_path(entry=entry):
                project_path = str(entry["projectPath"])
                removed.append(f"{plugin_id}:{project_path}")
                continue
            kept_entries.append(entry)
        pruned_plugins[plugin_id] = kept_entries

    if len(removed) == 0:
        return []
    for removed_entry in sorted(removed):
        if dry_run:
            log.info("would prune dead project plugin entry (dry-run)", entry=removed_entry)
        else:
            log.info("pruned dead project plugin entry", entry=removed_entry)
    if dry_run:
        return sorted(removed)

    backup_path = registry_path.with_name(f"{registry_path.name}.{_registry_timestamp()}.bak")
    _ = shutil.copy2(registry_path, backup_path)
    registry["plugins"] = pruned_plugins
    _ = registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    log.info(
        "backed up installed_plugins.json before pruning dead project entries",
        path=str(registry_path),
        backup_path=str(backup_path),
        removed_count=len(removed),
    )
    return sorted(removed)
