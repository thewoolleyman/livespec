"""Tests for dev-tooling/checks/all_declared.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import all_declared  # noqa: E402

__all__: list[str] = []


_GOOD_MODULE = (
    '"""docstring"""\n'
    '__all__: list[str] = ["foo", "Bar"]\n'
    "\n"
    "def foo() -> None: pass\n"
    "\n"
    "class Bar: pass\n"
)
_MISSING_ALL = '"""docstring"""\ndef foo() -> None: pass\n'
_UNTYPED_ALL = (
    '"""docstring"""\n'
    # missing list[str] annotation
    '__all__ = ["foo"]\n'
    "def foo() -> None: pass\n"
)
_UNDEFINED_NAME = (
    '"""docstring"""\n__all__: list[str] = ["foo", "missing"]\ndef foo() -> None: pass\n'
)
# value is a string, not a list
_NON_LIST_VALUE = '"""docstring"""\n__all__: list[str] = "foo"\n'


def test_good_module_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "good.py"
    target.write_text(_GOOD_MODULE, encoding="utf-8")
    assert all_declared.check_file(path=target) == []


def test_missing_all_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "missing.py"
    target.write_text(_MISSING_ALL, encoding="utf-8")
    violations = all_declared.check_file(path=target)
    assert len(violations) == 1
    assert "missing module-level" in violations[0]


def test_untyped_all_fails(*, tmp_path: Path) -> None:
    """Plain `__all__ = [...]` without `list[str]` annotation is rejected."""
    target = tmp_path / "untyped.py"
    target.write_text(_UNTYPED_ALL, encoding="utf-8")
    violations = all_declared.check_file(path=target)
    assert len(violations) == 1
    assert "missing module-level" in violations[0]


def test_undefined_name_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "undef.py"
    target.write_text(_UNDEFINED_NAME, encoding="utf-8")
    violations = all_declared.check_file(path=target)
    assert len(violations) == 1
    assert "missing" in violations[0]


def test_non_list_value_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "non_list.py"
    target.write_text(_NON_LIST_VALUE, encoding="utf-8")
    violations = all_declared.check_file(path=target)
    assert len(violations) == 1
    assert "list of string literals" in violations[0]


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every shipped livespec/** module declares __all__ correctly."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert all_declared.main() == 0
