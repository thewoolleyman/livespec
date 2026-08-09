"""Tests for dev-tooling/checks/spec_governance_manifest.py."""

from __future__ import annotations

import importlib.util
import io
import json
import shutil
from collections.abc import Callable
from contextlib import redirect_stderr
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

__all__: list[str] = []

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK = _REPO_ROOT / "dev-tooling" / "checks" / "spec_governance_manifest.py"
_MANIFEST_REL = (
    Path(".claude-plugin")
    / "scripts"
    / "_vendor"
    / "livespec_runtime"
    / "api_configurable_keys.json"
)


def test_spec_governance_manifest_accepts_matching_runtime_resource(*, tmp_path: Path) -> None:
    _copy_real_manifest(tmp_path=tmp_path)

    result, _stderr = _run_check(tmp_path=tmp_path)

    assert result == 0


def test_spec_governance_manifest_rejects_drift(*, tmp_path: Path) -> None:
    _copy_real_manifest(tmp_path=tmp_path)
    manifest_path = tmp_path / _MANIFEST_REL
    rows = cast(list[dict[str, Any]], json.loads(manifest_path.read_text(encoding="utf-8")))
    rows[0]["safe_default"] = "drifted"
    _ = manifest_path.write_text(json.dumps(rows), encoding="utf-8")

    result, stderr = _run_check(tmp_path=tmp_path)

    assert result != 0
    assert "spec-governance-manifest-drift" in stderr


def test_spec_governance_manifest_rejects_missing_resource(*, tmp_path: Path) -> None:
    result, stderr = _run_check(tmp_path=tmp_path)

    assert result != 0
    assert "spec-governance-manifest-missing" in stderr


def test_spec_governance_manifest_rejects_non_list_resource(*, tmp_path: Path) -> None:
    _write_manifest(tmp_path=tmp_path, text="{}")

    result, stderr = _run_check(tmp_path=tmp_path)

    assert result != 0
    assert "spec-governance-manifest-drift" in stderr


def test_spec_governance_manifest_ignores_non_object_resource_items(*, tmp_path: Path) -> None:
    _copy_real_manifest(tmp_path=tmp_path)
    manifest_path = tmp_path / _MANIFEST_REL
    rows = cast(list[dict[str, Any]], json.loads(manifest_path.read_text(encoding="utf-8")))
    _write_manifest(tmp_path=tmp_path, text=json.dumps(["ignored", *rows]))

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


def _copy_real_manifest(*, tmp_path: Path) -> None:
    target = tmp_path / _MANIFEST_REL
    target.parent.mkdir(parents=True)
    _ = shutil.copyfile(_REPO_ROOT / _MANIFEST_REL, target)


def _write_manifest(*, tmp_path: Path, text: str) -> None:
    target = tmp_path / _MANIFEST_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    _ = target.write_text(text, encoding="utf-8")
