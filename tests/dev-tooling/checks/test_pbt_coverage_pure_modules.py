"""Tests for dev-tooling/checks/pbt_coverage_pure_modules.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import pbt_coverage_pure_modules  # noqa: E402

__all__: list[str] = []


_GIVEN_BARE = '''"""docstring"""
from hypothesis import given, strategies as st

__all__: list[str] = []


@given(st.integers())
def test_thing(x):
    assert x == x
'''

_GIVEN_ATTRIBUTE = '''"""docstring"""
import hypothesis
from hypothesis import strategies as st

__all__: list[str] = []


@hypothesis.given(st.integers())
def test_thing(x):
    assert x == x
'''

_NO_GIVEN_FAILS = '''"""docstring"""

__all__: list[str] = []


def test_thing():
    assert 1 == 1
'''

_GIVEN_ON_NONTEST_DOESNT_COUNT = '''"""docstring"""
from hypothesis import given, strategies as st

__all__: list[str] = []


@given(st.integers())
def helper_thing(x):
    return x


def test_uses_helper():
    assert helper_thing(x=1) == 1
'''


def test_bare_given_decorator_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "test_thing.py"
    target.write_text(_GIVEN_BARE, encoding="utf-8")
    assert pbt_coverage_pure_modules.check_file(path=target) == []


def test_attribute_given_decorator_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "test_thing.py"
    target.write_text(_GIVEN_ATTRIBUTE, encoding="utf-8")
    assert pbt_coverage_pure_modules.check_file(path=target) == []


def test_no_given_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "test_thing.py"
    target.write_text(_NO_GIVEN_FAILS, encoding="utf-8")
    violations = pbt_coverage_pure_modules.check_file(path=target)
    assert len(violations) == 1
    assert "lacks any `@given(...)`-decorated test" in violations[0]


def test_given_on_non_test_function_doesnt_count(*, tmp_path: Path) -> None:
    """Only `test_*`-prefixed functions count toward the rule."""
    target = tmp_path / "test_thing.py"
    target.write_text(_GIVEN_ON_NONTEST_DOESNT_COUNT, encoding="utf-8")
    violations = pbt_coverage_pure_modules.check_file(path=target)
    assert len(violations) == 1


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """tests/livespec/parse|validate/ directories don't exist yet (Phase 5+);
    main() vacuously passes pre-Phase-5."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert pbt_coverage_pure_modules.main() == 0
