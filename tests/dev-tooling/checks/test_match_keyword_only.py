"""Tests for dev-tooling/checks/match_keyword_only.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import match_keyword_only  # noqa: E402

__all__: list[str] = []


_LIVESPEC_KEYWORD_OK = '''"""docstring"""
from livespec.errors import HelpRequested

def main() -> int:
    match value:
        case HelpRequested(text=text):
            return 0
        case _:
            return 1
'''

_LIVESPEC_POSITIONAL_FAILS = '''"""docstring"""
from livespec.errors import HelpRequested

def main() -> int:
    match value:
        case HelpRequested(text):
            return 0
        case _:
            return 1
'''

_THIRD_PARTY_POSITIONAL_OK = '''"""docstring"""
from returns.result import Success, Failure

def main() -> int:
    match value:
        case Success(payload):
            return 0
        case Failure(err):
            return 1
        case _:
            return 1
'''

_NESTED_LIVESPEC_KEYWORD_OK = '''"""docstring"""
from returns.io import IOFailure
from livespec.errors import HelpRequested

def main() -> int:
    match value:
        case IOFailure(HelpRequested(text=text)):
            return 0
        case _:
            return 1
'''

_NESTED_LIVESPEC_POSITIONAL_FAILS = '''"""docstring"""
from returns.io import IOFailure
from livespec.errors import HelpRequested

def main() -> int:
    match value:
        case IOFailure(HelpRequested(text)):
            return 0
        case _:
            return 1
'''

_LOCAL_CLASS_POSITIONAL_FAILS = '''"""docstring"""
class MyLocal:
    pass

def main() -> int:
    match value:
        case MyLocal(field):
            return 0
        case _:
            return 1
'''

_EMPTY_LIVESPEC_PATTERN_OK = '''"""docstring"""
from livespec.errors import HelpRequested

def main() -> int:
    match value:
        case HelpRequested():
            return 0
        case _:
            return 1
'''

_WILDCARD_AS_PATTERN_OK = '''"""docstring"""
def main() -> int:
    match value:
        case _ as unreachable:
            return 1
'''


def test_livespec_keyword_pattern_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_LIVESPEC_KEYWORD_OK, encoding="utf-8")
    assert match_keyword_only.check_file(path=target) == []


def test_livespec_positional_pattern_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_LIVESPEC_POSITIONAL_FAILS, encoding="utf-8")
    violations = match_keyword_only.check_file(path=target)
    assert any("HelpRequested" in v for v in violations)


def test_third_party_positional_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_THIRD_PARTY_POSITIONAL_OK, encoding="utf-8")
    assert match_keyword_only.check_file(path=target) == []


def test_nested_livespec_keyword_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_NESTED_LIVESPEC_KEYWORD_OK, encoding="utf-8")
    assert match_keyword_only.check_file(path=target) == []


def test_nested_livespec_positional_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_NESTED_LIVESPEC_POSITIONAL_FAILS, encoding="utf-8")
    violations = match_keyword_only.check_file(path=target)
    assert any("HelpRequested" in v for v in violations)


def test_local_class_positional_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_LOCAL_CLASS_POSITIONAL_FAILS, encoding="utf-8")
    violations = match_keyword_only.check_file(path=target)
    assert any("MyLocal" in v for v in violations)


def test_empty_livespec_pattern_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_EMPTY_LIVESPEC_PATTERN_OK, encoding="utf-8")
    assert match_keyword_only.check_file(path=target) == []


def test_wildcard_as_pattern_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_WILDCARD_AS_PATTERN_OK, encoding="utf-8")
    assert match_keyword_only.check_file(path=target) == []


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Shipped code uses keyword-form for livespec class destructures."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert match_keyword_only.main() == 0
