"""Edge-case tests for dev-tooling/checks/spec_governance_template.py."""

from __future__ import annotations

import importlib.util
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
    spec = importlib.util.spec_from_file_location("spec_governance_template_check", _CHECK)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(_CheckModule, module)


def _run_check(*, cwd: Path, monkeypatch: pytest.MonkeyPatch) -> int:
    module = _load_module()
    monkeypatch.chdir(cwd)
    monkeypatch.setattr(sys, "argv", ["spec_governance_template.py"])
    return module.main()


def _write_fixture(*, root: Path, manifest_text: str, template_text: str) -> None:
    manifest_path = root / _MANIFEST_REL
    _ = manifest_path.parent.mkdir(parents=True)
    _ = manifest_path.write_text(manifest_text, encoding="utf-8")
    template_path = root / _TEMPLATE_REL
    _ = template_path.parent.mkdir(parents=True)
    _ = template_path.write_text(template_text, encoding="utf-8")


def test_spec_governance_template_rejects_missing_files(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The check fails closed when run outside the livespec-core repo shape."""
    assert _run_check(cwd=tmp_path, monkeypatch=monkeypatch) == 1


def test_spec_governance_template_rejects_absent_block(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A template without the optional spec_governance section is invalid."""
    _write_fixture(
        root=tmp_path,
        manifest_text="[]",
        template_text="// Optional \u2014 credential_wrapper: next block\n",
    )

    assert _run_check(cwd=tmp_path, monkeypatch=monkeypatch) == 1


def test_spec_governance_template_rejects_unterminated_block(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A block header without the following optional section delimiter is invalid."""
    _write_fixture(
        root=tmp_path,
        manifest_text="[]",
        template_text='// Optional \u2014 spec_governance: policy\n//   "spec_governance": {}\n',
    )

    assert _run_check(cwd=tmp_path, monkeypatch=monkeypatch) == 1


def test_spec_governance_template_rejects_empty_commented_block(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A marker-only block is present but not usable documentation."""
    _write_fixture(
        root=tmp_path,
        manifest_text="[]",
        template_text=(
            "// Optional \u2014 spec_governance: policy\n"
            "not a comment\n"
            "// Optional \u2014 credential_wrapper: next block\n"
        ),
    )

    assert _run_check(cwd=tmp_path, monkeypatch=monkeypatch) == 1


def test_spec_governance_template_rejects_non_object_documented_block(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The documented spec_governance value must be an object."""
    _write_fixture(
        root=tmp_path,
        manifest_text="[]",
        template_text=(
            "// Optional \u2014 spec_governance: policy\n"
            '//   "spec_governance": []\n'
            "// Optional \u2014 credential_wrapper: next block\n"
        ),
    )

    assert _run_check(cwd=tmp_path, monkeypatch=monkeypatch) == 1


def test_spec_governance_template_accepts_empty_non_list_manifest(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-list manifest projects to no expected keys."""
    _write_fixture(
        root=tmp_path,
        manifest_text="{}",
        template_text=(
            "// Optional \u2014 spec_governance: policy\n"
            '//   "spec_governance": {}\n'
            "// Optional \u2014 credential_wrapper: next block\n"
        ),
    )

    assert _run_check(cwd=tmp_path, monkeypatch=monkeypatch) == 0


def test_spec_governance_template_ignores_non_dict_manifest_items(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only manifest object rows contribute expected keys."""
    _write_fixture(
        root=tmp_path,
        manifest_text='["ignored", {"key": "x", "safe_default": "safe"}]',
        template_text=(
            "// Optional \u2014 spec_governance: policy\n"
            '//   "spec_governance": {\n'
            "//     // descriptive comment ignored by the parser\n"
            '//     "x": "safe"\n'
            "//   }\n"
            "// Optional \u2014 credential_wrapper: next block\n"
        ),
    )

    assert _run_check(cwd=tmp_path, monkeypatch=monkeypatch) == 0
