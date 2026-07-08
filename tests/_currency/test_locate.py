"""Focused coverage for _currency.locate path/cache/JSON helpers."""

# ruff: noqa: SLF001

from __future__ import annotations

import json
from pathlib import Path

import pytest
from _currency import locate

__all__: list[str] = []


def test_plugin_root_prefers_env_override(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`CLAUDE_PLUGIN_ROOT` wins over the bundle-relative fallback."""
    override = tmp_path / "override"
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(override))
    assert locate._plugin_root() == override


def test_plugin_root_falls_back_to_bundle_root(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """With no env override, the plugin root is the `.claude-plugin` bundle dir."""
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    expected = Path(locate.__file__).resolve().parents[2]
    assert locate._plugin_root() == expected


def test_read_json_object_rejects_missing_malformed_and_non_object(*, tmp_path: Path) -> None:
    """Only a real JSON object is returned; missing/malformed/non-object yield None."""
    assert locate._read_json_object(path=tmp_path / "absent.json") is None
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{not json", encoding="utf-8")
    assert locate._read_json_object(path=malformed) is None
    list_shaped = tmp_path / "list.json"
    list_shaped.write_text("[]", encoding="utf-8")
    assert locate._read_json_object(path=list_shaped) is None
    obj = tmp_path / "obj.json"
    obj.write_text(json.dumps({"k": "v"}), encoding="utf-8")
    assert locate._read_json_object(path=obj) == {"k": "v"}


def test_installed_plugin_cache_path_detection_covers_claude_and_codex(*, tmp_path: Path) -> None:
    """Only installed plugin-cache roots are inside the currency gate."""
    assert locate._is_installed_plugin_cache_path(
        plugin_root=tmp_path / "home" / ".claude" / "plugins" / "cache" / "livespec" / "0.6.1"
    )
    assert locate._is_installed_plugin_cache_path(
        plugin_root=tmp_path / "home" / ".codex" / "plugins" / "cache" / "livespec" / "0.6.1"
    )
    assert not locate._is_installed_plugin_cache_path(
        plugin_root=tmp_path / "repo" / ".claude-plugin"
    )


def test_is_codex_installed_plugin_cache_path_matches_only_codex_layout(*, tmp_path: Path) -> None:
    """The nested `.codex/plugins/cache/livespec/livespec/...` layout is Codex-specific."""
    assert locate._is_codex_installed_plugin_cache_path(
        plugin_root=tmp_path / ".codex" / "plugins" / "cache" / "livespec" / "livespec" / "0.6.1"
    )
    assert not locate._is_codex_installed_plugin_cache_path(
        plugin_root=tmp_path / ".claude" / "plugins" / "cache" / "livespec" / "0.6.1"
    )
