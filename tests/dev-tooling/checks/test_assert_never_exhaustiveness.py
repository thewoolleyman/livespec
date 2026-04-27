"""Tests for dev-tooling/checks/assert_never_exhaustiveness.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import assert_never_exhaustiveness  # noqa: E402

__all__: list[str] = []


_TERMINATES_OK = '''"""docstring"""
from typing_extensions import assert_never

def f(value: int) -> int:
    match value:
        case 1:
            return 1
        case 2:
            return 2
        case _:
            assert_never(value)
'''

_MISSING_WILDCARD_FAILS = '''"""docstring"""
def f(value: int) -> int:
    match value:
        case 1:
            return 1
        case 2:
            return 2
'''

_AS_BIND_NOT_BARE_FAILS = '''"""docstring"""
def f(value: int) -> int:
    match value:
        case 1:
            return 1
        case _ as bound:
            return -1
'''

_BODY_WRONG_FUNCTION_FAILS = '''"""docstring"""
def f(value: int) -> int:
    match value:
        case 1:
            return 1
        case _:
            raise RuntimeError("bad")
'''

_BODY_WRONG_ARG_FAILS = '''"""docstring"""
from typing_extensions import assert_never

def f(value: int, other: int) -> int:
    match value:
        case 1:
            return 1
        case _:
            assert_never(other)
'''

_BODY_TWO_STMTS_FAILS = '''"""docstring"""
from typing_extensions import assert_never

def f(value: int) -> int:
    match value:
        case 1:
            return 1
        case _:
            print("bad")
            assert_never(value)
'''

_NESTED_MATCH_BOTH_OK = '''"""docstring"""
from typing_extensions import assert_never

def f(outer: int, inner: int) -> int:
    match outer:
        case 1:
            match inner:
                case 1:
                    return 1
                case _:
                    assert_never(inner)
        case _:
            assert_never(outer)
'''

_GUARDED_WILDCARD_FAILS = '''"""docstring"""
def f(value: int) -> int:
    match value:
        case 1:
            return 1
        case _ if value > 0:
            return 2
'''

_NON_NAME_SUBJECT_OK = '''"""docstring"""
def f(obj: object) -> int:
    match obj.attr:
        case 1:
            return 1
'''


def test_terminating_case_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_TERMINATES_OK, encoding="utf-8")
    assert assert_never_exhaustiveness.check_file(path=target) == []


def test_missing_wildcard_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_MISSING_WILDCARD_FAILS, encoding="utf-8")
    violations = assert_never_exhaustiveness.check_file(path=target)
    assert any("does not terminate with `case _:`" in v for v in violations)


def test_as_binding_not_bare_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_AS_BIND_NOT_BARE_FAILS, encoding="utf-8")
    violations = assert_never_exhaustiveness.check_file(path=target)
    assert any("does not terminate with `case _:`" in v for v in violations)


def test_body_wrong_function_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_BODY_WRONG_FUNCTION_FAILS, encoding="utf-8")
    violations = assert_never_exhaustiveness.check_file(path=target)
    assert any("body is not" in v for v in violations)


def test_body_wrong_arg_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_BODY_WRONG_ARG_FAILS, encoding="utf-8")
    violations = assert_never_exhaustiveness.check_file(path=target)
    assert any("body is not" in v for v in violations)


def test_body_two_stmts_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_BODY_TWO_STMTS_FAILS, encoding="utf-8")
    violations = assert_never_exhaustiveness.check_file(path=target)
    assert any("body is not" in v for v in violations)


def test_nested_match_both_pass(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_NESTED_MATCH_BOTH_OK, encoding="utf-8")
    assert assert_never_exhaustiveness.check_file(path=target) == []


def test_guarded_wildcard_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_GUARDED_WILDCARD_FAILS, encoding="utf-8")
    violations = assert_never_exhaustiveness.check_file(path=target)
    assert any("does not terminate" in v for v in violations)


def test_non_name_subject_skipped(*, tmp_path: Path) -> None:
    """Non-Name subjects (e.g., `match obj.attr:`) are not enforced at v1."""
    target = tmp_path / "f.py"
    target.write_text(_NON_NAME_SUBJECT_OK, encoding="utf-8")
    assert assert_never_exhaustiveness.check_file(path=target) == []


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Shipped code terminates every match with `case _: assert_never(<subject>)`."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert assert_never_exhaustiveness.main() == 0
