"""Tests for dev-tooling/checks/spec_governance_manifest.py."""

from __future__ import annotations

import importlib.util
import io
import json
from collections.abc import Callable
from contextlib import redirect_stderr
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest

__all__: list[str] = []

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK = _REPO_ROOT / "dev-tooling" / "checks" / "spec_governance_manifest.py"


def test_spec_governance_manifest_accepts_matching_projection(*, tmp_path: Path) -> None:
    _write_fixture(tmp_path=tmp_path, manifest_key="x")

    result, _stderr = _run_check(tmp_path=tmp_path)

    assert result == 0


def test_spec_governance_manifest_rejects_drift(*, tmp_path: Path) -> None:
    _write_fixture(tmp_path=tmp_path, manifest_key="y")

    result, stderr = _run_check(tmp_path=tmp_path)

    assert result != 0
    assert "registry/manifest drift" in stderr


def test_spec_governance_manifest_accepts_empty_repo(*, tmp_path: Path) -> None:
    result, _stderr = _run_check(tmp_path=tmp_path)

    assert result == 0


def test_spec_governance_manifest_accepts_non_list_manifest(*, tmp_path: Path) -> None:
    package = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "spec_governance"
    package.mkdir(parents=True)
    (package / "registry.py").write_text("", encoding="utf-8")
    (package / "api_configurable_keys.json").write_text("{}", encoding="utf-8")

    result, _stderr = _run_check(tmp_path=tmp_path)

    assert result == 0


def test_spec_governance_manifest_ignores_non_dict_manifest_items(*, tmp_path: Path) -> None:
    package = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "spec_governance"
    package.mkdir(parents=True)
    (package / "registry.py").write_text("", encoding="utf-8")
    (package / "api_configurable_keys.json").write_text("[1]", encoding="utf-8")

    result, _stderr = _run_check(tmp_path=tmp_path)

    assert result == 0


def test_spec_governance_manifest_ignores_kwargs_expansion(*, tmp_path: Path) -> None:
    package = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "spec_governance"
    package.mkdir(parents=True)
    (package / "registry.py").write_text("ConfigKey(**row)\n", encoding="utf-8")
    (package / "api_configurable_keys.json").write_text("[]", encoding="utf-8")

    result, _stderr = _run_check(tmp_path=tmp_path)

    assert result == 0


def test_spec_governance_manifest_ignores_non_name_calls(*, tmp_path: Path) -> None:
    package = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "spec_governance"
    package.mkdir(parents=True)
    (package / "registry.py").write_text("factory.ConfigKey()\n", encoding="utf-8")
    (package / "api_configurable_keys.json").write_text("[]", encoding="utf-8")

    result, _stderr = _run_check(tmp_path=tmp_path)

    assert result == 0


def _run_check(*, tmp_path: Path) -> tuple[int, str]:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(tmp_path)
        main = cast(Callable[[], int], _load_check().main)
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = main()
    return result, stderr.getvalue()


def _load_check() -> ModuleType:
    spec = importlib.util.spec_from_file_location("spec_governance_manifest_check", _CHECK)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_fixture(*, tmp_path: Path, manifest_key: str) -> None:
    package = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "spec_governance"
    package.mkdir(parents=True)
    (package / "registry.py").write_text(
        """
from __future__ import annotations

CONFIG_KEYS = (
    ConfigKey(
        key="x",
        value_type="enum",
        safe_default="a",
        per_proposal_override=None,
        allowed_values=["a"],
    ),
)
""",
        encoding="utf-8",
    )
    (package / "api_configurable_keys.json").write_text(
        json.dumps(
            [
                {
                    "key": manifest_key,
                    "value_type": "enum",
                    "safe_default": "a",
                    "per_proposal_override": None,
                    "allowed_values": ["a"],
                },
            ],
        ),
        encoding="utf-8",
    )
