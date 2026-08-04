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
    argv: list[str] | None = None,
) -> tuple[int, str]:
    module = _load_module()
    monkeypatch.chdir(cwd)
    monkeypatch.setattr(sys, "argv", ["spec_governance_template.py", *(argv or [])])
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
    _ = manifest_target.parent.mkdir(parents=True)
    _ = shutil.copyfile(_REPO_ROOT / _MANIFEST_REL, manifest_target)

    template_target = tmp_path / _TEMPLATE_REL
    _ = template_target.parent.mkdir(parents=True)
    source_text = (_REPO_ROOT / _TEMPLATE_REL).read_text(encoding="utf-8")
    removed_text = source_text.replace(
        '  //     "propose_change_mode": "interactive",\n',
        "",
    )
    _ = template_target.write_text(removed_text, encoding="utf-8")

    returncode, _stderr = _run_check(cwd=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    assert (
        returncode == 1
    ), "verify should fail when a manifest key is absent from the template block"


def test_spec_governance_template_rejects_safe_default_drift(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Agreement includes the shipped safe default, not only key presence."""
    manifest_target = tmp_path / _MANIFEST_REL
    _ = manifest_target.parent.mkdir(parents=True)
    _ = shutil.copyfile(_REPO_ROOT / _MANIFEST_REL, manifest_target)

    template_target = tmp_path / _TEMPLATE_REL
    _ = template_target.parent.mkdir(parents=True)
    source_text = (_REPO_ROOT / _TEMPLATE_REL).read_text(encoding="utf-8")
    drifted_text = source_text.replace(
        '  //     "critique_mode": "interactive",\n',
        '  //     "critique_mode": "batch",\n',
    )
    _ = template_target.write_text(drifted_text, encoding="utf-8")

    returncode, _stderr = _run_check(cwd=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    assert returncode == 1, "verify should fail when a documented safe default drifts"


def test_spec_governance_template_accepts_parameterized_consumer_config(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The generic check can compare a consumer-side `.livespec.jsonc` block."""
    manifest_target = tmp_path / "core-manifest.json"
    _ = shutil.copyfile(_REPO_ROOT / _MANIFEST_REL, manifest_target)
    config_target = tmp_path / ".livespec.jsonc"
    _ = config_target.write_text(_matching_consumer_config(), encoding="utf-8")

    returncode, stderr = _run_check(
        cwd=tmp_path,
        monkeypatch=monkeypatch,
        capsys=capsys,
        argv=[
            "--manifest-path",
            str(manifest_target),
            "--block-source",
            str(config_target),
        ],
    )

    assert returncode == 0, stderr


def test_spec_governance_template_rejects_parameterized_missing_consumer_key(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Positive control: a consumer block missing one manifest key fails."""
    manifest_target = tmp_path / "core-manifest.json"
    _ = shutil.copyfile(_REPO_ROOT / _MANIFEST_REL, manifest_target)
    config_target = tmp_path / ".livespec.jsonc"
    _ = config_target.write_text(
        _matching_consumer_config().replace(
            '  //     "propose_change_mode": "interactive",\n',
            "",
        ),
        encoding="utf-8",
    )

    returncode, stderr = _run_check(
        cwd=tmp_path,
        monkeypatch=monkeypatch,
        capsys=capsys,
        argv=[
            "--manifest-path",
            str(manifest_target),
            "--block-source",
            str(config_target),
        ],
    )

    assert returncode == 1
    assert "spec-governance-template-drift" in stderr


def _matching_consumer_config() -> str:
    return (
        "{\n"
        '  "template": "livespec"\n'
        "\n"
        "  // Optional \u2014 spec_governance: policy levers for livespec's spec-side\n"
        "  // operations. The commented defaults below are derived from the shipped\n"
        "  // spec-governance manifest.\n"
        '  //   "spec_governance": {\n'
        '  //     "propose_change_mode": "interactive",\n'
        '  //     "critique_mode": "interactive",\n'
        '  //     "in_flight_alignment": "prompt",\n'
        '  //     "doctor_dispositions": {},\n'
        '  //     "revise_decision_mode": "manual",\n'
        '  //     "ratification_review": "manual-spawn",\n'
        '  //     "ratification_reviewer_model": null\n'
        "  //   }\n"
        "  //\n"
        "  // Optional \u2014 credential_wrapper: next block\n"
        "}\n"
    )
