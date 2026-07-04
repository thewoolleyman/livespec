"""Focused coverage for the _bootstrap plugin-currency helpers."""

# ruff: noqa: SLF001

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

__all__: list[str] = []

_BIN_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "bin"


def _import_bootstrap() -> ModuleType:
    """Import `_bootstrap` fresh, ensuring `bin/` is on sys.path."""
    if str(_BIN_DIR) not in sys.path:
        sys.path.insert(0, str(_BIN_DIR))
    sys.modules.pop("_bootstrap", None)
    return importlib.import_module("_bootstrap")


def test_registry_helpers_reject_unknown_shapes(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Malformed registry data yields unknown currency rather than a crash."""
    bootstrap_module = _import_bootstrap()
    plugin_root = tmp_path / "cache" / "livespec"
    plugin_root.mkdir(parents=True)
    home = tmp_path / "home"
    registry = home / ".claude" / "plugins" / "installed_plugins.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(json.dumps({"version": 2, "plugins": "not-a-list"}), encoding="utf-8")
    monkeypatch.setattr(Path, "home", lambda: home)

    assert bootstrap_module._running_build_id_from_registry(plugin_root=plugin_root) is None
    assert (
        bootstrap_module._registry_plugin_build_id(
            plugin="not-a-dict",
            normalized_plugin_root=plugin_root,
        )
        is None
    )
    assert (
        bootstrap_module._registry_plugin_build_id(
            plugin={"installPath": str(tmp_path / "other"), "gitCommitSha": "abcdef123456"},
            normalized_plugin_root=plugin_root,
        )
        is None
    )
    registry.write_text("[]", encoding="utf-8")
    assert bootstrap_module._read_json_object(path=registry) is None


def test_registry_helpers_read_real_installed_plugin_registry_shape(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The installed-plugin registry is keyed by plugin@marketplace."""
    bootstrap_module = _import_bootstrap()
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

    assert (
        bootstrap_module._running_build_id_from_registry(plugin_root=plugin_root) == "abcdef123456"
    )


def test_registry_helpers_ignore_legacy_list_registry_shape(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A synthetic list-shaped registry is not a supported source."""
    bootstrap_module = _import_bootstrap()
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

    assert bootstrap_module._running_build_id_from_registry(plugin_root=plugin_root) is None


def test_installed_plugin_cache_path_detection_covers_claude_and_codex(*, tmp_path: Path) -> None:
    """Only installed plugin-cache roots are inside the currency gate."""
    bootstrap_module = _import_bootstrap()

    assert bootstrap_module._is_installed_plugin_cache_path(
        plugin_root=tmp_path / "home" / ".claude" / "plugins" / "cache" / "livespec" / "0.6.1"
    )
    assert bootstrap_module._is_installed_plugin_cache_path(
        plugin_root=tmp_path / "home" / ".codex" / "plugins" / "cache" / "livespec" / "0.6.1"
    )
    assert not bootstrap_module._is_installed_plugin_cache_path(
        plugin_root=tmp_path / "repo" / ".claude-plugin"
    )


def test_git_rev_parse_head_accepts_success(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Expected-build lookup accepts a successful 12-hex git result."""
    bootstrap_module = _import_bootstrap()
    repository = tmp_path / "marketplace"
    repository.mkdir()

    def successful_run(
        args: list[str], *, capture_output: bool, check: bool, text: bool
    ) -> SimpleNamespace:
        assert args == ["/usr/bin/git", "-C", str(repository), "rev-parse", "--short=12", "HEAD"]
        assert capture_output is True
        assert check is False
        assert text is True
        return SimpleNamespace(returncode=0, stdout="abcdef123456\n")

    monkeypatch.setattr(bootstrap_module.subprocess, "run", successful_run)
    assert bootstrap_module._git_rev_parse_head(repository=repository) == "abcdef123456"


def test_git_rev_parse_head_rejects_failed_git(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A non-zero git process result leaves expected currency unknown."""
    bootstrap_module = _import_bootstrap()
    repository = tmp_path / "marketplace"
    repository.mkdir()

    def failing_run(
        args: list[str], *, capture_output: bool, check: bool, text: bool
    ) -> SimpleNamespace:
        assert args[0] == "/usr/bin/git"
        assert capture_output is True
        assert check is False
        assert text is True
        return SimpleNamespace(returncode=1, stdout="abcdef123456\n")

    monkeypatch.setattr(bootstrap_module.subprocess, "run", failing_run)
    assert bootstrap_module._git_rev_parse_head(repository=repository) is None


def test_git_rev_parse_head_rejects_invalid_sha(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A successful git process with a non-SHA stdout stays unknown."""
    bootstrap_module = _import_bootstrap()
    repository = tmp_path / "marketplace"
    repository.mkdir()

    def invalid_sha_run(
        args: list[str], *, capture_output: bool, check: bool, text: bool
    ) -> SimpleNamespace:
        assert args[0] == "/usr/bin/git"
        assert capture_output is True
        assert check is False
        assert text is True
        return SimpleNamespace(returncode=0, stdout="not-a-sha\n")

    monkeypatch.setattr(bootstrap_module.subprocess, "run", invalid_sha_run)
    assert bootstrap_module._git_rev_parse_head(repository=repository) is None


def test_git_rev_parse_head_handles_missing_git(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An OSError from process launch leaves expected currency unknown."""
    bootstrap_module = _import_bootstrap()
    repository = tmp_path / "marketplace"
    repository.mkdir()

    def raising_run(args: list[str], *, capture_output: bool, check: bool, text: bool) -> None:
        assert args[0] == "/usr/bin/git"
        assert capture_output is True
        assert check is False
        assert text is True
        raise OSError("git unavailable")

    monkeypatch.setattr(bootstrap_module.subprocess, "run", raising_run)
    assert bootstrap_module._git_rev_parse_head(repository=repository) is None
