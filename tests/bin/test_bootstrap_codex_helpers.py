"""Focused coverage for Codex plugin-currency helper branches."""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

__all__: list[str] = []

_BIN_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "bin"


def _import_bootstrap() -> object:
    if str(_BIN_DIR) not in sys.path:
        sys.path.insert(0, str(_BIN_DIR))
    _ = sys.modules.pop("_bootstrap", None)
    return importlib.import_module("_bootstrap")


def _codex_plugin_root(*, home: Path) -> Path:
    return home / ".codex" / "plugins" / "cache" / "livespec" / "livespec" / "0.6.1"


def _module_attr(*, module: object, name: str) -> object:
    return getattr(module, name)


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


def test_codex_running_build_ignores_non_codex_paths_and_missing_plugin_list(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bootstrap_module = _import_bootstrap()
    home = tmp_path / "home"
    codex_root = _codex_plugin_root(home=home)
    codex_root.mkdir(parents=True)
    non_codex_root = home / ".claude" / "plugins" / "cache" / "livespec" / "0.6.1"
    non_codex_root.mkdir(parents=True)
    monkeypatch.setattr(bootstrap_module, "_codex_plugin_list_json", lambda: None)

    running_build_id_from_codex_plugin_list = _module_attr(
        module=bootstrap_module, name="_running_build_id_from_codex_plugin_list"
    )

    assert running_build_id_from_codex_plugin_list(plugin_root=non_codex_root) is None
    assert running_build_id_from_codex_plugin_list(plugin_root=codex_root) is None


def test_codex_running_build_accepts_mapping_shaped_plugin_list(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bootstrap_module = _import_bootstrap()
    home = tmp_path / "home"
    codex_root = _codex_plugin_root(home=home)
    codex_root.mkdir(parents=True)
    monkeypatch.setattr(
        bootstrap_module,
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

    running_build_id_from_codex_plugin_list = _module_attr(
        module=bootstrap_module, name="_running_build_id_from_codex_plugin_list"
    )

    assert running_build_id_from_codex_plugin_list(plugin_root=codex_root) == "aaaaaaaaaaaa"


def test_codex_running_build_accepts_real_local_source_shape_without_commit_field(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bootstrap_module = _import_bootstrap()
    home = tmp_path / "home"
    codex_root = _codex_plugin_root(home=home)
    codex_root.mkdir(parents=True)
    marketplace = home / ".codex" / ".tmp" / "marketplaces" / "livespec"
    running_build_id = _commit_temp_repo(repository=marketplace)
    monkeypatch.setattr(
        bootstrap_module,
        "_codex_plugin_list_json",
        lambda: {
            "plugins": {
                "livespec@livespec": {
                    "version": "0.6.5",
                    "source": {
                        "source": "local",
                        "path": str(marketplace / ".claude-plugin"),
                    },
                }
            }
        },
    )

    running_build_id_from_codex_plugin_list = _module_attr(
        module=bootstrap_module, name="_running_build_id_from_codex_plugin_list"
    )

    assert running_build_id_from_codex_plugin_list(plugin_root=codex_root) == running_build_id


def test_codex_running_build_returns_none_for_unusable_plugin_records(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bootstrap_module = _import_bootstrap()
    home = tmp_path / "home"
    codex_root = _codex_plugin_root(home=home)
    codex_root.mkdir(parents=True)

    running_build_id_from_codex_plugin_list = _module_attr(
        module=bootstrap_module, name="_running_build_id_from_codex_plugin_list"
    )

    monkeypatch.setattr(bootstrap_module, "_codex_plugin_list_json", lambda: {"plugins": "bad"})
    assert running_build_id_from_codex_plugin_list(plugin_root=codex_root) is None

    monkeypatch.setattr(
        bootstrap_module,
        "_codex_plugin_list_json",
        lambda: {"plugins": [{"name": "not-livespec"}]},
    )
    assert running_build_id_from_codex_plugin_list(plugin_root=codex_root) is None


def test_codex_plugin_build_id_matches_install_path_name_marketplace_and_id(
    *, tmp_path: Path
) -> None:
    bootstrap_module = _import_bootstrap()
    home = tmp_path / "home"
    codex_root = _codex_plugin_root(home=home)
    normalized_root = codex_root.resolve(strict=False)

    codex_plugin_build_id = _module_attr(module=bootstrap_module, name="_codex_plugin_build_id")

    assert codex_plugin_build_id(plugin=object(), normalized_plugin_root=normalized_root) is None
    assert (
        codex_plugin_build_id(
            plugin={"name": "not-livespec", "gitCommitSha": "1111111111119999"},
            normalized_plugin_root=normalized_root,
        )
        is None
    )
    assert (
        codex_plugin_build_id(
            plugin={"id": "livespec@livespec"}, normalized_plugin_root=normalized_root
        )
        is None
    )
    assert (
        codex_plugin_build_id(
            plugin={"installPath": str(codex_root), "buildId": "bbbbbbbbbbbb9999"},
            normalized_plugin_root=normalized_root,
        )
        == "bbbbbbbbbbbb"
    )
    assert (
        codex_plugin_build_id(
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
        codex_plugin_build_id(
            plugin={"id": "livespec@livespec", "commit": "dddddddddddd9999"},
            normalized_plugin_root=normalized_root,
        )
        == "dddddddddddd"
    )


def test_codex_plugin_list_json_handles_cli_failures_and_success(
    *, monkeypatch: pytest.MonkeyPatch
) -> None:
    bootstrap_module = _import_bootstrap()

    codex_plugin_list_json = _module_attr(module=bootstrap_module, name="_codex_plugin_list_json")
    shutil_module = _module_attr(module=bootstrap_module, name="shutil")
    subprocess_module = _module_attr(module=bootstrap_module, name="subprocess")

    monkeypatch.setattr(shutil_module, "which", lambda _name: None)
    assert codex_plugin_list_json() is None

    monkeypatch.setattr(shutil_module, "which", lambda _name: "/usr/bin/codex")

    def raise_os_error(*_args: object, **_kwargs: object) -> object:
        raise OSError

    monkeypatch.setattr(subprocess_module, "run", raise_os_error)
    assert codex_plugin_list_json() is None

    monkeypatch.setattr(
        subprocess_module,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="{}"),
    )
    assert codex_plugin_list_json() is None

    monkeypatch.setattr(
        subprocess_module,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="not-json"),
    )
    assert codex_plugin_list_json() is None

    monkeypatch.setattr(
        subprocess_module,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="[]"),
    )
    assert codex_plugin_list_json() is None

    monkeypatch.setattr(
        subprocess_module,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout='{"plugins": []}'),
    )
    assert codex_plugin_list_json() == {"plugins": []}
