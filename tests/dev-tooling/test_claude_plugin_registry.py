"""Tests for `dev-tooling/claude_plugin_registry.py` synthetic-registry cleanup."""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

__all__: list[str] = []

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "dev-tooling" / "claude_plugin_registry.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("claude_plugin_registry", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _registry_path(*, home: Path) -> Path:
    return home / ".claude" / "plugins" / "installed_plugins.json"


def _write_registry(*, home: Path, registry: Mapping[str, Any]) -> Path:
    path = _registry_path(home=home)
    path.parent.mkdir(parents=True)
    _ = path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    return path


def test_prunes_dead_project_scope_entries_and_writes_backup(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    home = tmp_path / "home"
    live_project = tmp_path / "live-project"
    live_project.mkdir()
    missing_project = tmp_path / "missing-project"
    registry_path = _write_registry(
        home=home,
        registry={
            "version": 2,
            "plugins": {
                "livespec@livespec": [
                    {"scope": "project", "projectPath": str(missing_project), "enabled": True},
                    {"scope": "project", "projectPath": str(live_project), "enabled": True},
                    {"scope": "project", "enabled": True},
                    {"scope": "project", "projectPath": "", "enabled": True},
                    {"scope": "user", "enabled": True},
                ]
            },
        },
    )
    monkeypatch.setenv("HOME", str(home))

    removed = module.prune_dead_project_plugin_entries(dry_run=False)

    assert removed == [f"livespec@livespec:{missing_project}"]
    assert json.loads(registry_path.read_text(encoding="utf-8")) == {
        "version": 2,
        "plugins": {
            "livespec@livespec": [
                {"scope": "project", "projectPath": str(live_project), "enabled": True},
                {"scope": "project", "enabled": True},
                {"scope": "project", "projectPath": "", "enabled": True},
                {"scope": "user", "enabled": True},
            ]
        },
    }
    backups = sorted(registry_path.parent.glob("installed_plugins.json.*.bak"))
    assert len(backups) == 1
    backed_up = json.loads(backups[0].read_text(encoding="utf-8"))
    assert backed_up["plugins"]["livespec@livespec"][0]["projectPath"] == str(missing_project)


def test_dry_run_reports_dead_entries_without_mutating_registry(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    home = tmp_path / "home"
    missing_project = tmp_path / "missing-project"
    registry = {
        "version": 2,
        "plugins": {
            "b@market": [
                {"scope": "project", "projectPath": str(missing_project)},
            ],
            "a@market": [
                {"scope": "project", "projectPath": str(missing_project)},
            ],
        },
    }
    registry_path = _write_registry(home=home, registry=registry)
    before = registry_path.read_text(encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))

    removed = module.prune_dead_project_plugin_entries(dry_run=True)

    assert removed == [f"a@market:{missing_project}", f"b@market:{missing_project}"]
    assert registry_path.read_text(encoding="utf-8") == before
    assert sorted(registry_path.parent.glob("installed_plugins.json.*.bak")) == []


def test_noops_when_registry_missing_or_no_entries_are_dead(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))

    assert module.prune_dead_project_plugin_entries(dry_run=False) == []

    live_project = tmp_path / "live-project"
    live_project.mkdir()
    registry_path = _write_registry(
        home=home,
        registry={
            "version": 2,
            "plugins": {
                "livespec@livespec": [
                    {"scope": "project", "projectPath": str(live_project)},
                ]
            },
        },
    )
    before = registry_path.read_text(encoding="utf-8")

    assert module.prune_dead_project_plugin_entries(dry_run=False) == []
    assert registry_path.read_text(encoding="utf-8") == before
    assert sorted(registry_path.parent.glob("installed_plugins.json.*.bak")) == []


@pytest.mark.parametrize(
    "raw_registry",
    [
        "not json",
        json.dumps([]),
        json.dumps({"version": 1, "plugins": {}}),
        json.dumps({"version": 2, "plugins": []}),
        json.dumps({"version": 2, "plugins": {"ok": {}}}),
        json.dumps({"version": 2, "plugins": {"ok": ["not an entry"]}}),
    ],
)
def test_unrecognized_registry_shapes_warn_and_noop(
    *, raw_registry: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    home = tmp_path / "home"
    registry_path = _registry_path(home=home)
    registry_path.parent.mkdir(parents=True)
    _ = registry_path.write_text(raw_registry, encoding="utf-8")
    before = registry_path.read_text(encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))

    assert module.prune_dead_project_plugin_entries(dry_run=False) == []
    assert registry_path.read_text(encoding="utf-8") == before
    assert sorted(registry_path.parent.glob("installed_plugins.json.*.bak")) == []
