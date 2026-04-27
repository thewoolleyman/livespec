"""Tests for dev-tooling/checks/rop_pipeline_shape.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import rop_pipeline_shape  # noqa: E402

__all__: list[str] = []


_ONE_PUBLIC_OK = '''"""docstring"""
from livespec.types import rop_pipeline

@rop_pipeline
class SeedPipeline:
    def run(self, *, argv) -> int:
        return self._step1()

    def _step1(self) -> int:
        return 0
'''

_ZERO_PUBLIC_FAILS = '''"""docstring"""
from livespec.types import rop_pipeline

@rop_pipeline
class SeedPipeline:
    def _step1(self) -> int:
        return 0

    def _step2(self) -> int:
        return 1
'''

_TWO_PUBLIC_FAILS = '''"""docstring"""
from livespec.types import rop_pipeline

@rop_pipeline
class SeedPipeline:
    def run(self, *, argv) -> int:
        return self._step1()

    def status(self) -> str:
        return "ok"

    def _step1(self) -> int:
        return 0
'''

_DUNDERS_NOT_COUNTED_OK = '''"""docstring"""
from livespec.types import rop_pipeline

@rop_pipeline
class SeedPipeline:
    def __init__(self, *, config) -> None:
        self._config = config

    def __call__(self, *, argv) -> int:
        return self._step1()

    def _step1(self) -> int:
        return 0
'''

_NO_DECORATOR_EXEMPT = '''"""docstring"""
class HelperClass:
    def public_a(self) -> int:
        return 0

    def public_b(self) -> int:
        return 1

    def public_c(self) -> int:
        return 2
'''

_DUNDER_ENTRY_FAILS = '''"""docstring"""
from livespec.types import rop_pipeline

@rop_pipeline
class JustDunders:
    def __init__(self) -> None:
        pass

    def _step(self) -> int:
        return 0
'''

_ATTRIBUTE_DECORATOR_OK = '''"""docstring"""
import livespec.types

@livespec.types.rop_pipeline
class SeedPipeline:
    def run(self, *, argv) -> int:
        return self._step()

    def _step(self) -> int:
        return 0
'''

_OTHER_DECORATOR_IGNORED = '''"""docstring"""
def some_other_decorator(cls):
    return cls

@some_other_decorator
class NotAPipeline:
    def public_a(self) -> int:
        return 0

    def public_b(self) -> int:
        return 1
'''


def test_one_public_method_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_ONE_PUBLIC_OK, encoding="utf-8")
    assert rop_pipeline_shape.check_file(path=target) == []


def test_zero_public_methods_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_ZERO_PUBLIC_FAILS, encoding="utf-8")
    violations = rop_pipeline_shape.check_file(path=target)
    assert any("0 public methods" in v for v in violations)


def test_two_public_methods_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_TWO_PUBLIC_FAILS, encoding="utf-8")
    violations = rop_pipeline_shape.check_file(path=target)
    assert any("2 public methods" in v for v in violations)


def test_dunders_not_counted(*, tmp_path: Path) -> None:
    """Dunder-only class fails count-of-1.

    `__init__` + `__call__` aren't counted; `__call__` IS the public entry here,
    but as a dunder it's exempt — there's no non-dunder public method, so this
    fails the count-of-1 check.
    """
    target = tmp_path / "f.py"
    target.write_text(_DUNDERS_NOT_COUNTED_OK, encoding="utf-8")
    violations = rop_pipeline_shape.check_file(path=target)
    assert any("0 public methods" in v for v in violations)


def test_no_decorator_exempt(*, tmp_path: Path) -> None:
    """Helper class without `@rop_pipeline` is unconstrained."""
    target = tmp_path / "f.py"
    target.write_text(_NO_DECORATOR_EXEMPT, encoding="utf-8")
    assert rop_pipeline_shape.check_file(path=target) == []


def test_dunder_only_class_fails(*, tmp_path: Path) -> None:
    """A pipeline with only dunders + private methods fails (no public entry)."""
    target = tmp_path / "f.py"
    target.write_text(_DUNDER_ENTRY_FAILS, encoding="utf-8")
    violations = rop_pipeline_shape.check_file(path=target)
    assert any("0 public methods" in v for v in violations)


def test_attribute_decorator_recognized(*, tmp_path: Path) -> None:
    """`@livespec.types.rop_pipeline` (attribute form) is recognized."""
    target = tmp_path / "f.py"
    target.write_text(_ATTRIBUTE_DECORATOR_OK, encoding="utf-8")
    assert rop_pipeline_shape.check_file(path=target) == []


def test_other_decorators_ignored(*, tmp_path: Path) -> None:
    """Classes with non-`rop_pipeline` decorators aren't subject to the rule."""
    target = tmp_path / "f.py"
    target.write_text(_OTHER_DECORATOR_IGNORED, encoding="utf-8")
    assert rop_pipeline_shape.check_file(path=target) == []


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """No `@rop_pipeline` classes exist yet (Phase 4 sub-step 13 lands the
    decorator + check; the seed.py / revise.py refactor is sub-step 14)."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert rop_pipeline_shape.main() == 0
