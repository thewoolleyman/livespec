"""Tests for .claude-plugin/scripts/bin/_bootstrap.py.

Covers `_bootstrap.bootstrap()`: both sides of the
`sys.version_info < (3, 10)` check are exercised via
`monkeypatch.setattr(sys, "version_info", ...)`. Pragma exclusions
on `bin/*.py` are forbidden by the coverage-thresholds spec, so
branch coverage of the exit-127 path is achieved exclusively
through monkeypatching.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

__all__: list[str] = []


_BIN_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "bin"
_BUNDLE_SCRIPTS = _BIN_DIR.parent
_BUNDLE_VENDOR = _BUNDLE_SCRIPTS / "_vendor"
_EXIT_CODE_VERSION_MISMATCH = 127
_EXIT_CODE_STALE_PLUGIN = 78


def _import_bootstrap() -> object:
    """Import `_bootstrap` fresh, ensuring `bin/` is on sys.path.

    Removes any stale module entry first so each test sees a clean
    import (the wrapper-coverage tests pre-populate
    sys.modules['_bootstrap'] with a stub; this helper replaces
    that stub with the real module under test).
    """
    if str(_BIN_DIR) not in sys.path:
        sys.path.insert(0, str(_BIN_DIR))
    sys.modules.pop("_bootstrap", None)
    return importlib.import_module("_bootstrap")


def test_bootstrap_exits_on_old_python(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """sys.version_info < (3, 10) raises SystemExit(127) with the canonical message."""
    bootstrap_module = _import_bootstrap()
    monkeypatch.setattr(sys, "version_info", (3, 9, 0, "final", 0))
    with pytest.raises(SystemExit) as excinfo:
        bootstrap_module.bootstrap()  # type: ignore[attr-defined]
    assert excinfo.value.code == _EXIT_CODE_VERSION_MISMATCH


def test_bootstrap_inserts_paths_when_missing(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """sys.version_info >= (3, 10) inserts the bundle scripts/ and _vendor/ paths into sys.path."""
    bootstrap_module = _import_bootstrap()
    fresh_path: list[str] = ["/usr/lib/python3.10"]
    monkeypatch.setattr(sys, "path", fresh_path)
    monkeypatch.setattr(sys, "version_info", (3, 12, 0, "final", 0))
    bootstrap_module.bootstrap()  # type: ignore[attr-defined]
    assert str(_BUNDLE_SCRIPTS) in sys.path
    assert str(_BUNDLE_VENDOR) in sys.path


def test_bootstrap_skips_paths_already_present(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """When a bundle path is already in sys.path, bootstrap() does NOT duplicate it.

    Covers the False branch of `if path_str not in sys.path` so
    branch coverage of the loop body stays at 100%.
    """
    bootstrap_module = _import_bootstrap()
    seeded_path: list[str] = [str(_BUNDLE_SCRIPTS), str(_BUNDLE_VENDOR), "/usr/lib/python3.10"]
    monkeypatch.setattr(sys, "path", seeded_path)
    monkeypatch.setattr(sys, "version_info", (3, 12, 0, "final", 0))
    bootstrap_module.bootstrap()  # type: ignore[attr-defined]
    assert sys.path.count(str(_BUNDLE_SCRIPTS)) == 1
    assert sys.path.count(str(_BUNDLE_VENDOR)) == 1


def test_bootstrap_fails_loudly_when_running_plugin_is_stale(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A stale running gitCommitSha refuses to proceed before command imports."""
    bootstrap_module = _import_bootstrap()
    plugin_root = tmp_path / "cache" / "livespec"
    plugin_root.mkdir(parents=True)
    home = tmp_path / "home"
    marketplace = home / ".claude" / "plugins" / "marketplaces" / "livespec"
    marketplace.mkdir(parents=True)
    registry = home / ".claude" / "plugins" / "installed_plugins.json"
    registry.write_text(
        json.dumps(
            {
                "version": 2,
                "plugins": [
                    {
                        "name": "livespec",
                        "installPath": str(plugin_root),
                        "gitCommitSha": "111111111111",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "path", ["/usr/lib/python3.10"])
    monkeypatch.setattr(sys, "version_info", (3, 12, 0, "final", 0))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setattr(Path, "home", lambda: home)

    def expected_build_id(*, repository: Path) -> str:
        assert repository == marketplace
        return "222222222222"

    monkeypatch.setattr(bootstrap_module, "_git_rev_parse_head", expected_build_id)

    with pytest.raises(SystemExit) as excinfo:
        bootstrap_module.bootstrap()  # type: ignore[attr-defined]

    assert excinfo.value.code == _EXIT_CODE_STALE_PLUGIN


def test_bootstrap_proceeds_when_running_plugin_matches_expected_pin(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The registry gitCommitSha is the primary running-build source."""
    bootstrap_module = _import_bootstrap()
    plugin_root = tmp_path / "cache" / "semver-name"
    plugin_root.mkdir(parents=True)
    home = tmp_path / "home"
    marketplace = home / ".claude" / "plugins" / "marketplaces" / "livespec"
    marketplace.mkdir(parents=True)
    registry = home / ".claude" / "plugins" / "installed_plugins.json"
    registry.write_text(
        json.dumps(
            {
                "version": 2,
                "plugins": [
                    {
                        "name": "livespec",
                        "installPath": str(plugin_root),
                        "gitCommitSha": "222222222222",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    fresh_path: list[str] = ["/usr/lib/python3.10"]
    monkeypatch.setattr(sys, "path", fresh_path)
    monkeypatch.setattr(sys, "version_info", (3, 12, 0, "final", 0))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setattr(Path, "home", lambda: home)

    def expected_build_id(*, repository: Path) -> str:
        assert repository == marketplace
        return "222222222222"

    monkeypatch.setattr(bootstrap_module, "_git_rev_parse_head", expected_build_id)

    bootstrap_module.bootstrap()  # type: ignore[attr-defined]

    assert str(_BUNDLE_SCRIPTS) in sys.path
    assert str(_BUNDLE_VENDOR) in sys.path


def test_bootstrap_falls_back_to_sha_cache_dir_when_registry_lacks_commit(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A 12-hex cache directory basename is a fallback running-build source."""
    bootstrap_module = _import_bootstrap()
    plugin_root = tmp_path / "cache" / "333333333333"
    plugin_root.mkdir(parents=True)
    home = tmp_path / "home"
    marketplace = home / ".claude" / "plugins" / "marketplaces" / "livespec"
    marketplace.mkdir(parents=True)
    registry = home / ".claude" / "plugins" / "installed_plugins.json"
    registry.write_text(
        json.dumps(
            {
                "version": 2,
                "plugins": [{"name": "livespec", "installPath": str(plugin_root)}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "path", ["/usr/lib/python3.10"])
    monkeypatch.setattr(sys, "version_info", (3, 12, 0, "final", 0))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setattr(Path, "home", lambda: home)

    def expected_build_id(*, repository: Path) -> str:
        assert repository == marketplace
        return "333333333333"

    monkeypatch.setattr(bootstrap_module, "_git_rev_parse_head", expected_build_id)

    bootstrap_module.bootstrap()  # type: ignore[attr-defined]

    assert str(_BUNDLE_SCRIPTS) in sys.path


def test_bootstrap_warns_by_default_when_currency_is_unknown(
    *, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Unknown currency warns by default so local sessions can still proceed."""
    bootstrap_module = _import_bootstrap()
    plugin_root = tmp_path / "cache" / "semver-name"
    plugin_root.mkdir(parents=True)
    home = tmp_path / "home"
    monkeypatch.setattr(sys, "path", ["/usr/lib/python3.10"])
    monkeypatch.setattr(sys, "version_info", (3, 12, 0, "final", 0))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setattr(Path, "home", lambda: home)

    bootstrap_module.bootstrap()  # type: ignore[attr-defined]

    captured = capsys.readouterr()
    assert "livespec plugin currency could not be verified" in captured.err
    assert str(_BUNDLE_SCRIPTS) in sys.path


def test_bootstrap_warns_by_default_when_running_build_is_unknown_but_expected_pin_is_known(
    *, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Unknown running-build currency is not stale unless the fail lever is set."""
    bootstrap_module = _import_bootstrap()
    plugin_root = tmp_path / "cache" / "semver-name"
    plugin_root.mkdir(parents=True)
    home = tmp_path / "home"
    marketplace = home / ".claude" / "plugins" / "marketplaces" / "livespec"
    marketplace.mkdir(parents=True)
    monkeypatch.setattr(sys, "path", ["/usr/lib/python3.10"])
    monkeypatch.setattr(sys, "version_info", (3, 12, 0, "final", 0))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setenv("LIVESPEC_CURRENCY_GATE", "warn")
    monkeypatch.setattr(Path, "home", lambda: home)

    def expected_build_id(*, repository: Path) -> str:
        assert repository == marketplace
        return "222222222222"

    monkeypatch.setattr(bootstrap_module, "_git_rev_parse_head", expected_build_id)

    bootstrap_module.bootstrap()  # type: ignore[attr-defined]

    captured = capsys.readouterr()
    assert "livespec plugin currency could not be verified" in captured.err
    assert str(_BUNDLE_SCRIPTS) in sys.path


def test_bootstrap_fails_when_currency_is_unknown_and_gate_is_fail(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """CI and dispatch can promote unknown currency from warning to failure."""
    bootstrap_module = _import_bootstrap()
    plugin_root = tmp_path / "cache" / "semver-name"
    plugin_root.mkdir(parents=True)
    home = tmp_path / "home"
    monkeypatch.setattr(sys, "path", ["/usr/lib/python3.10"])
    monkeypatch.setattr(sys, "version_info", (3, 12, 0, "final", 0))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setenv("LIVESPEC_CURRENCY_GATE", "fail")
    monkeypatch.setattr(Path, "home", lambda: home)

    with pytest.raises(SystemExit) as excinfo:
        bootstrap_module.bootstrap()  # type: ignore[attr-defined]

    assert excinfo.value.code == _EXIT_CODE_STALE_PLUGIN
