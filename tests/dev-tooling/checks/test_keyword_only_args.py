"""Tests for dev-tooling/checks/keyword_only_args.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import keyword_only_args  # noqa: E402

__all__: list[str] = []


_KW_ONLY_OK = '''"""docstring"""
def helper(*, x: int, y: int) -> int:
    return x + y
'''

_NO_STAR_FAILS = '''"""docstring"""
def helper(x: int, y: int) -> int:
    return x + y
'''

_DUNDER_OK = '''"""docstring"""
class Foo:
    def __eq__(self, other: object) -> bool:
        return False
    def __hash__(self) -> int:
        return 0
'''

_POST_INIT_OK = '''"""docstring"""
class Foo:
    def __post_init__(self) -> None:
        pass
'''

_ROP_BIND_EXEMPT = '''"""docstring"""
def _orchestrate(namespace: object) -> object:
    return namespace

def caller() -> object:
    parsed = ...  # noqa
    return parsed.bind(_orchestrate)
'''

_ROP_MAP_EXEMPT = '''"""docstring"""
def _compute(entries: list[str]) -> int:
    return len(entries)

def caller() -> object:
    return io_op().map(_compute)
'''

_ROP_LASH_EXEMPT = '''"""docstring"""
def _recover(err: object) -> object:
    return err

def caller() -> object:
    return io_op().lash(_recover)
'''

_NON_ROP_NOT_EXEMPT = '''"""docstring"""
def _helper(arg: int) -> int:
    return arg

def caller() -> int:
    return _helper(5)
'''

_DATACLASS_TRIPLE_OK = '''"""docstring"""
from dataclasses import dataclass

@dataclass(frozen=True, kw_only=True, slots=True)
class Foo:
    x: int
'''

_DATACLASS_BARE_FAILS = '''"""docstring"""
from dataclasses import dataclass

@dataclass
class Foo:
    x: int
'''

_DATACLASS_MISSING_TRIPLE_FAILS = '''"""docstring"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Foo:
    x: int
'''

_NO_PARAMS_OK = '''"""docstring"""
def main() -> int:
    return 0
'''

_SELF_ONLY_METHOD_OK = '''"""docstring"""
class Foo:
    def method(self) -> None:
        pass
'''

_METHOD_WITH_KWONLY_OK = '''"""docstring"""
class Foo:
    def method(self, *, x: int) -> int:
        return x
'''

_METHOD_WITHOUT_STAR_FAILS = '''"""docstring"""
class Foo:
    def method(self, x: int) -> int:
        return x
'''

_PROTOCOL_METHODS_EXEMPT = '''"""docstring"""
from typing import Protocol

class MyApi(Protocol):
    def call(self, message: str, **kwargs: object) -> None: ...
    def query(self, name: str, *, kind: str) -> int: ...
'''

_NON_PROTOCOL_METHOD_NOT_EXEMPT = '''"""docstring"""
class Concrete:
    def call(self, message: str) -> None:
        pass
'''


def test_kw_only_def_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_KW_ONLY_OK, encoding="utf-8")
    assert keyword_only_args.check_file(path=target) == []


def test_no_star_def_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_NO_STAR_FAILS, encoding="utf-8")
    violations = keyword_only_args.check_file(path=target)
    assert any("lacks `*` separator" in v for v in violations)


def test_dunder_methods_exempt(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_DUNDER_OK, encoding="utf-8")
    assert keyword_only_args.check_file(path=target) == []


def test_post_init_exempt(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_POST_INIT_OK, encoding="utf-8")
    assert keyword_only_args.check_file(path=target) == []


def test_rop_bind_callback_exempt(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_ROP_BIND_EXEMPT, encoding="utf-8")
    assert keyword_only_args.check_file(path=target) == []


def test_rop_map_callback_exempt(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_ROP_MAP_EXEMPT, encoding="utf-8")
    assert keyword_only_args.check_file(path=target) == []


def test_rop_lash_callback_exempt(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_ROP_LASH_EXEMPT, encoding="utf-8")
    assert keyword_only_args.check_file(path=target) == []


def test_non_rop_callback_not_exempt(*, tmp_path: Path) -> None:
    """Single-arg helpers called normally are still subject to the `*` rule."""
    target = tmp_path / "f.py"
    target.write_text(_NON_ROP_NOT_EXEMPT, encoding="utf-8")
    violations = keyword_only_args.check_file(path=target)
    assert any("_helper" in v for v in violations)


def test_dataclass_triple_ok(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_DATACLASS_TRIPLE_OK, encoding="utf-8")
    assert keyword_only_args.check_file(path=target) == []


def test_dataclass_bare_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_DATACLASS_BARE_FAILS, encoding="utf-8")
    violations = keyword_only_args.check_file(path=target)
    assert any("bare `@dataclass`" in v for v in violations)


def test_dataclass_missing_triple_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_DATACLASS_MISSING_TRIPLE_FAILS, encoding="utf-8")
    violations = keyword_only_args.check_file(path=target)
    assert any("strict triple" in v for v in violations)


def test_no_params_def_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_NO_PARAMS_OK, encoding="utf-8")
    assert keyword_only_args.check_file(path=target) == []


def test_self_only_method_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_SELF_ONLY_METHOD_OK, encoding="utf-8")
    assert keyword_only_args.check_file(path=target) == []


def test_method_with_star_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_METHOD_WITH_KWONLY_OK, encoding="utf-8")
    assert keyword_only_args.check_file(path=target) == []


def test_method_without_star_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_METHOD_WITHOUT_STAR_FAILS, encoding="utf-8")
    violations = keyword_only_args.check_file(path=target)
    assert any("method" in v for v in violations)


def test_protocol_methods_exempt(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_PROTOCOL_METHODS_EXEMPT, encoding="utf-8")
    assert keyword_only_args.check_file(path=target) == []


def test_non_protocol_method_not_exempt(*, tmp_path: Path) -> None:
    target = tmp_path / "f.py"
    target.write_text(_NON_PROTOCOL_METHOD_NOT_EXEMPT, encoding="utf-8")
    violations = keyword_only_args.check_file(path=target)
    assert any("call" in v for v in violations)


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """After repo-wide refactor: every def has `*` separator (modulo exemptions)."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert keyword_only_args.main() == 0
