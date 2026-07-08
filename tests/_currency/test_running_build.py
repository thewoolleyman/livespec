"""Focused coverage for _currency.running_build detection helpers."""

# ruff: noqa: SLF001

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from _currency import running_build

__all__: list[str] = []


def _codex_plugin_root(*, home: Path) -> Path:
    return home / ".codex" / "plugins" / "cache" / "livespec" / "livespec" / "0.6.1"


def _commit_temp_repo(*, repository: Path) -> str:
    repository.mkdir(parents=True)
    subprocess.run(["/usr/bin/git", "-C", str(repository), "init"], check=True)
    (repository / ".claude-plugin").mkdir()
    (repository / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    subprocess.run(["/usr/bin/git", "-C", str(repository), "add", ".claude-plugin"], check=True)
    subprocess.run(
        [
            "/usr/bin/git",
            "-C",
            str(repository),
            "-c",
            "user.name=Test User",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "seed marketplace",
        ],
        check=True,
    )
    completed = subprocess.run(
        ["/usr/bin/git", "-C", str(repository), "rev-parse", "--short=12", "HEAD"],
        capture_output=True,
        check=True,
        text=True,
    )
    return completed.stdout.strip().lower()


def test_running_build_id_prefers_registry_then_codex_then_sha_dir(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`_running_build_id` tries registry, then Codex plugin list, then a 12-hex dir name."""
    sha_root = tmp_path / "cache" / "livespec" / "abcdef123456"
    monkeypatch.setattr(running_build, "_running_build_id_from_registry", lambda **_kwargs: None)
    monkeypatch.setattr(
        running_build, "_running_build_id_from_codex_plugin_list", lambda **_kwargs: None
    )
    assert running_build._running_build_id(plugin_root=sha_root) == "abcdef123456"

    plain_root = tmp_path / "cache" / "livespec" / "0.6.1"
    assert running_build._running_build_id(plugin_root=plain_root) is None

    monkeypatch.setattr(
        running_build, "_running_build_id_from_registry", lambda **_kwargs: "111111111111"
    )
    assert running_build._running_build_id(plugin_root=plain_root) == "111111111111"

    monkeypatch.setattr(running_build, "_running_build_id_from_registry", lambda **_kwargs: None)
    monkeypatch.setattr(
        running_build,
        "_running_build_id_from_codex_plugin_list",
        lambda **_kwargs: "222222222222",
    )
    assert running_build._running_build_id(plugin_root=plain_root) == "222222222222"


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


def test_codex_local_source_build_id_rejects_unusable_sources() -> None:
    """Local-source fallback only accepts a local source with a string path."""
    assert running_build._codex_local_source_build_id(plugin={}) is None
    assert (
        running_build._codex_local_source_build_id(
            plugin={"source": {"source": "github", "path": "/tmp/livespec"}}
        )
        is None
    )
    assert (
        running_build._codex_local_source_build_id(
            plugin={"source": {"source": "local", "path": 123}}
        )
        is None
    )


def test_codex_running_build_ignores_non_codex_paths_and_missing_plugin_list(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    codex_root = _codex_plugin_root(home=home)
    codex_root.mkdir(parents=True)
    non_codex_root = home / ".claude" / "plugins" / "cache" / "livespec" / "0.6.1"
    non_codex_root.mkdir(parents=True)
    monkeypatch.setattr(running_build, "_codex_plugin_list_json", lambda: None)

    assert (
        running_build._running_build_id_from_codex_plugin_list(plugin_root=non_codex_root) is None
    )
    assert running_build._running_build_id_from_codex_plugin_list(plugin_root=codex_root) is None


def test_codex_running_build_accepts_mapping_shaped_plugin_list(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    codex_root = _codex_plugin_root(home=home)
    codex_root.mkdir(parents=True)
    monkeypatch.setattr(
        running_build,
        "_codex_plugin_list_json",
        lambda: {
            "plugins": {
                "ignored-scalar": "not-a-record",
                "list-records": [
                    {
                        "installPath": str(codex_root),
                        "commitSha": "aaaaaaaaaaaa9999",
                    }
                ],
                "dict-record": {"name": "not-livespec"},
            }
        },
    )

    assert (
        running_build._running_build_id_from_codex_plugin_list(plugin_root=codex_root)
        == "aaaaaaaaaaaa"
    )


def test_codex_running_build_accepts_real_local_source_shape_without_commit_field(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The real `codex plugin list --json` keys records under top-level `installed`.

    Its top level is `installed`/`available`, not `plugins`; a local-source record
    carries `source:{local,path}`, `pluginId`, `marketplaceName`, and no commit field.
    The gate must resolve the running build from that real shape.
    """
    home = tmp_path / "home"
    codex_root = _codex_plugin_root(home=home)
    codex_root.mkdir(parents=True)
    marketplace = home / ".codex" / ".tmp" / "marketplaces" / "livespec"
    running_build_id = _commit_temp_repo(repository=marketplace)
    monkeypatch.setattr(
        running_build,
        "_codex_plugin_list_json",
        lambda: {
            "installed": [
                {
                    "authPolicy": "prompt",
                    "enabled": True,
                    "installPolicy": "allow",
                    "installed": True,
                    "marketplaceName": "livespec",
                    "name": "livespec",
                    "pluginId": "livespec@livespec",
                    "source": {
                        "source": "local",
                        "path": str(marketplace / ".claude-plugin"),
                    },
                    "version": "0.6.5",
                }
            ],
            "available": [],
        },
    )

    assert (
        running_build._running_build_id_from_codex_plugin_list(plugin_root=codex_root)
        == running_build_id
    )


def test_codex_running_build_returns_none_for_unusable_plugin_records(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    codex_root = _codex_plugin_root(home=home)
    codex_root.mkdir(parents=True)

    monkeypatch.setattr(running_build, "_codex_plugin_list_json", lambda: {"plugins": "bad"})
    assert running_build._running_build_id_from_codex_plugin_list(plugin_root=codex_root) is None

    monkeypatch.setattr(
        running_build,
        "_codex_plugin_list_json",
        lambda: {"plugins": [{"name": "not-livespec"}]},
    )
    assert running_build._running_build_id_from_codex_plugin_list(plugin_root=codex_root) is None


def test_codex_plugin_build_id_matches_install_path_name_marketplace_and_id(
    *, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    codex_root = _codex_plugin_root(home=home)
    normalized_root = codex_root.resolve(strict=False)

    assert (
        running_build._codex_plugin_build_id(
            plugin=object(), normalized_plugin_root=normalized_root
        )
        is None
    )
    assert (
        running_build._codex_plugin_build_id(
            plugin={"name": "not-livespec", "gitCommitSha": "1111111111119999"},
            normalized_plugin_root=normalized_root,
        )
        is None
    )
    assert (
        running_build._codex_plugin_build_id(
            plugin={"id": "livespec@livespec"}, normalized_plugin_root=normalized_root
        )
        is None
    )
    assert (
        running_build._codex_plugin_build_id(
            plugin={"installPath": str(codex_root), "buildId": "bbbbbbbbbbbb9999"},
            normalized_plugin_root=normalized_root,
        )
        == "bbbbbbbbbbbb"
    )
    assert (
        running_build._codex_plugin_build_id(
            plugin={
                "name": "livespec",
                "marketplace": "livespec",
                "gitCommitSha": 123,
                "sourceCommitSha": "cccccccccccc9999",
            },
            normalized_plugin_root=normalized_root,
        )
        == "cccccccccccc"
    )
    assert (
        running_build._codex_plugin_build_id(
            plugin={"id": "livespec@livespec", "commit": "dddddddddddd9999"},
            normalized_plugin_root=normalized_root,
        )
        == "dddddddddddd"
    )


def test_codex_plugin_list_json_handles_cli_failures_and_success(
    *, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(running_build.shutil, "which", lambda _name: None)
    assert running_build._codex_plugin_list_json() is None

    monkeypatch.setattr(running_build.shutil, "which", lambda _name: "/usr/bin/codex")

    def raise_os_error(*_args: object, **_kwargs: object) -> object:
        raise OSError

    monkeypatch.setattr(running_build.subprocess, "run", raise_os_error)
    assert running_build._codex_plugin_list_json() is None

    monkeypatch.setattr(
        running_build.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="{}"),
    )
    assert running_build._codex_plugin_list_json() is None

    monkeypatch.setattr(
        running_build.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="not-json"),
    )
    assert running_build._codex_plugin_list_json() is None

    monkeypatch.setattr(
        running_build.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="[]"),
    )
    assert running_build._codex_plugin_list_json() is None

    monkeypatch.setattr(
        running_build.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout='{"plugins": []}'),
    )
    assert running_build._codex_plugin_list_json() == {"plugins": []}
