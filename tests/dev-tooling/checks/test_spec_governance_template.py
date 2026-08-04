"""Tests for dev-tooling/checks/spec_governance_template.py."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from typing import Protocol, cast

import pytest

__all__: list[str] = []

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK = _REPO_ROOT / "dev-tooling" / "checks" / "spec_governance_template.py"
_MANIFEST_REL = (
    Path(".claude-plugin")
    / "scripts"
    / "livespec"
    / "spec_governance"
    / "api_configurable_keys.json"
)
_TEMPLATE_REL = Path("templates") / "orchestrator-plugin" / ".livespec.jsonc.jinja"


class _CheckModule(Protocol):
    def main(self) -> int: ...


def _load_module() -> _CheckModule:
    assert _CHECK.is_file(), f"expected check script at {_CHECK}"
    spec = importlib.util.spec_from_file_location("spec_governance_template_check", _CHECK)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(_CheckModule, module)


def _run_check(
    *,
    cwd: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str]:
    module = _load_module()
    monkeypatch.chdir(cwd)
    monkeypatch.setattr(sys, "argv", ["spec_governance_template.py"])
    result = module.main()
    captured = capsys.readouterr()
    return result, captured.err


def test_spec_governance_template_accepts_real_committed_template(
    *, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The shipped template documents every manifest key at its safe default."""
    returncode, stderr = _run_check(cwd=_REPO_ROOT, monkeypatch=monkeypatch, capsys=capsys)

    assert returncode == 0, (
        "real committed template must agree with the spec_governance manifest; "
        f"got returncode={returncode} stderr={stderr!r}"
    )
    assert (
        "spec-governance-template-ok" in stderr
    ), f"expected success diagnostic in stderr; got stderr={stderr!r}"


def test_spec_governance_template_rejects_missing_manifest_key(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Positive control: removing one manifest key from the template fails."""
    manifest_target = tmp_path / _MANIFEST_REL
    manifest_target.parent.mkdir(parents=True)
    shutil.copyfile(_REPO_ROOT / _MANIFEST_REL, manifest_target)

    template_target = tmp_path / _TEMPLATE_REL
    template_target.parent.mkdir(parents=True)
    source_text = (_REPO_ROOT / _TEMPLATE_REL).read_text(encoding="utf-8")
    removed_text = source_text.replace(
        '  //     "propose_change_mode": "interactive",\n',
        "",
    )
    template_target.write_text(removed_text, encoding="utf-8")

    returncode, _stderr = _run_check(cwd=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    assert (
        returncode == 1
    ), "verify should fail when a manifest key is absent from the template block"


def test_spec_governance_template_rejects_safe_default_drift(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Agreement includes the shipped safe default, not only key presence."""
    manifest_target = tmp_path / _MANIFEST_REL
    manifest_target.parent.mkdir(parents=True)
    shutil.copyfile(_REPO_ROOT / _MANIFEST_REL, manifest_target)

    template_target = tmp_path / _TEMPLATE_REL
    template_target.parent.mkdir(parents=True)
    source_text = (_REPO_ROOT / _TEMPLATE_REL).read_text(encoding="utf-8")
    drifted_text = source_text.replace(
        '  //     "critique_mode": "interactive",\n',
        '  //     "critique_mode": "batch",\n',
    )
    template_target.write_text(drifted_text, encoding="utf-8")

    returncode, _stderr = _run_check(cwd=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    assert returncode == 1, "verify should fail when a documented safe default drifts"
