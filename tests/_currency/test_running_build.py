"""Focused coverage for _currency.running_build detection helpers."""

# ruff: noqa: SLF001

from __future__ import annotations

import json
from pathlib import Path

import pytest
from _currency import running_build

__all__: list[str] = []


def _codex_plugin_root(*, home: Path) -> Path:
    return home / ".codex" / "plugins" / "cache" / "livespec" / "livespec" / "0.6.1"


def test_running_build_id_routes_codex_to_last_revision(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A Codex cache path resolves the running build from config `last_revision`.

    The Claude registry MUST NOT be consulted for a Codex install: Codex has no
    `installed_plugins.json`, and the clone-HEAD derivation it used to fall back
    to was tautologically equal to the expected build.
    """
    home = tmp_path / "home"
    codex_root = _codex_plugin_root(home=home)
    codex_root.mkdir(parents=True)
    monkeypatch.setattr(running_build, "_codex_last_revision_build_id", lambda: "abcabcabcabc")
    # A sentinel on the registry source: if the Codex branch failed to return
    # early, this value would surface as the result and fail the assertion.
    monkeypatch.setattr(
        running_build, "_running_build_id_from_registry", lambda **_kwargs: "registry-consulted"
    )
    assert running_build._running_build_id(plugin_root=codex_root) == "abcabcabcabc"


def test_running_build_id_prefers_registry_then_sha_dir_for_claude(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A non-Codex path tries the registry, then a 12-hex cache-dir basename."""
    sha_root = tmp_path / "cache" / "livespec" / "abcdef123456"
    monkeypatch.setattr(running_build, "_running_build_id_from_registry", lambda **_kwargs: None)
    assert running_build._running_build_id(plugin_root=sha_root) == "abcdef123456"

    plain_root = tmp_path / "cache" / "livespec" / "0.6.1"
    assert running_build._running_build_id(plugin_root=plain_root) is None

    monkeypatch.setattr(
        running_build, "_running_build_id_from_registry", lambda **_kwargs: "111111111111"
    )
    assert running_build._running_build_id(plugin_root=plain_root) == "111111111111"


def test_registry_helpers_reject_unknown_shapes(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Malformed registry data yields unknown currency rather than a crash."""
    plugin_root = tmp_path / "cache" / "livespec"
    plugin_root.mkdir(parents=True)
    home = tmp_path / "home"
    registry = home / ".claude" / "plugins" / "installed_plugins.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(json.dumps({"version": 2, "plugins": "not-a-list"}), encoding="utf-8")
    monkeypatch.setattr(Path, "home", lambda: home)

    assert running_build._running_build_id_from_registry(plugin_root=plugin_root) is None
    assert (
        running_build._registry_plugin_build_id(
            plugin="not-a-dict",
            normalized_plugin_root=plugin_root,
        )
        is None
    )
    assert (
        running_build._registry_plugin_build_id(
            plugin={"installPath": str(tmp_path / "other"), "gitCommitSha": "abcdef123456"},
            normalized_plugin_root=plugin_root,
        )
        is None
    )


def test_registry_helpers_reject_missing_registry_file(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A missing installed_plugins.json leaves the registry source unknown."""
    plugin_root = tmp_path / "cache" / "livespec"
    plugin_root.mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    assert running_build._running_build_id_from_registry(plugin_root=plugin_root) is None


def test_registry_helpers_read_real_installed_plugin_registry_shape(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The installed-plugin registry is keyed by plugin@marketplace."""
    plugin_root = tmp_path / "cache" / "livespec" / "0.6.1"
    plugin_root.mkdir(parents=True)
    home = tmp_path / "home"
    registry = home / ".claude" / "plugins" / "installed_plugins.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        json.dumps(
            {
                "version": 2,
                "plugins": {
                    "broken@marketplace": {"installPath": str(plugin_root)},
                    "livespec@livespec": [
                        {
                            "scope": "user",
                            "installPath": str(plugin_root),
                            "version": "0.6.1",
                            "installedAt": "2026-07-04T00:00:00.000Z",
                            "lastUpdated": "2026-07-04T00:01:00.000Z",
                            "gitCommitSha": "abcdef1234567890",
                        }
                    ],
                    "other@marketplace": [
                        {
                            "scope": "user",
                            "installPath": str(tmp_path / "other"),
                            "version": "1.0.0",
                            "installedAt": "2026-07-04T00:00:00.000Z",
                            "lastUpdated": "2026-07-04T00:01:00.000Z",
                            "gitCommitSha": "1111111111112222",
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(Path, "home", lambda: home)

    assert running_build._running_build_id_from_registry(plugin_root=plugin_root) == "abcdef123456"


def test_registry_returns_none_when_no_installed_record_matches(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A registry whose records all fail to match falls through to unknown.

    Exercises the loop-exhaustion path (a non-matching install path plus a
    record missing its `gitCommitSha`) that reaches the trailing `return None`.
    """
    plugin_root = tmp_path / "cache" / "livespec" / "0.6.1"
    plugin_root.mkdir(parents=True)
    home = tmp_path / "home"
    registry = home / ".claude" / "plugins" / "installed_plugins.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        json.dumps(
            {
                "version": 2,
                "plugins": {
                    "livespec@livespec": [
                        {
                            "installPath": str(tmp_path / "elsewhere"),
                            "gitCommitSha": "abcdef1234567890",
                        },
                        {"installPath": str(plugin_root)},
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(Path, "home", lambda: home)

    assert running_build._running_build_id_from_registry(plugin_root=plugin_root) is None


def test_registry_helpers_ignore_legacy_list_registry_shape(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A synthetic list-shaped registry is not a supported source."""
    plugin_root = tmp_path / "cache" / "livespec" / "0.6.1"
    plugin_root.mkdir(parents=True)
    home = tmp_path / "home"
    registry = home / ".claude" / "plugins" / "installed_plugins.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        json.dumps(
            {
                "version": 2,
                "plugins": [
                    {
                        "scope": "user",
                        "installPath": str(plugin_root),
                        "version": "0.6.1",
                        "installedAt": "2026-07-04T00:00:00.000Z",
                        "lastUpdated": "2026-07-04T00:01:00.000Z",
                        "gitCommitSha": "abcdef1234567890",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(Path, "home", lambda: home)

    assert running_build._running_build_id_from_registry(plugin_root=plugin_root) is None
