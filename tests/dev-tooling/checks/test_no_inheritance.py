"""Tests for dev-tooling/checks/no_inheritance.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import no_inheritance  # noqa: E402

__all__: list[str] = []


_NO_INHERITANCE = '"""docstring"""\nclass Foo:\n    pass\n'
_EXCEPTION_OK = '"""docstring"""\nclass MyErr(Exception):\n    pass\n'
_LIVESPEC_ERROR_OK = '"""docstring"""\nclass MyDomain(LivespecError):\n    pass\n'
_PROTOCOL_OK = '"""docstring"""\nclass MyIface(Protocol):\n    pass\n'
_FORBIDDEN_BASE = '"""docstring"""\nclass MyThing(SomeUserClass):\n    pass\n'
_FORBIDDEN_LIVESPEC_SUBCLASS = (
    '"""docstring"""\nclass MyError(UsageError):\n    pass\n'
)
_ATTRIBUTE_BASE = '"""docstring"""\nimport typing\nclass MyIface(typing.Protocol):\n    pass\n'
_PARAMETRIC_PROTOCOL_OK = (
    '"""docstring"""\nfrom typing import Protocol, TypeVar\n'
    "T = TypeVar('T')\nclass MyGeneric(Protocol[T]):\n    pass\n"
)


def test_no_inheritance_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "no_inh.py"
    target.write_text(_NO_INHERITANCE, encoding="utf-8")
    assert no_inheritance.check_file(path=target) == []


def test_exception_base_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "exc.py"
    target.write_text(_EXCEPTION_OK, encoding="utf-8")
    assert no_inheritance.check_file(path=target) == []


def test_livespec_error_base_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "livespec_err.py"
    target.write_text(_LIVESPEC_ERROR_OK, encoding="utf-8")
    assert no_inheritance.check_file(path=target) == []


def test_protocol_base_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "proto.py"
    target.write_text(_PROTOCOL_OK, encoding="utf-8")
    assert no_inheritance.check_file(path=target) == []


def test_forbidden_base_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "forbidden.py"
    target.write_text(_FORBIDDEN_BASE, encoding="utf-8")
    violations = no_inheritance.check_file(path=target)
    assert len(violations) == 1
    assert "SomeUserClass" in violations[0]
    assert "not in direct-parent allowlist" in violations[0]


def test_livespec_subclass_fails(*, tmp_path: Path) -> None:
    """v013 M5: subclassing UsageError (or any LivespecError subclass) is forbidden."""
    target = tmp_path / "livespec_sub.py"
    target.write_text(_FORBIDDEN_LIVESPEC_SUBCLASS, encoding="utf-8")
    violations = no_inheritance.check_file(path=target)
    assert len(violations) == 1
    assert "UsageError" in violations[0]


def test_attribute_base_fails(*, tmp_path: Path) -> None:
    """`class X(typing.Protocol):` is flagged — convention is bare-name `Protocol`."""
    target = tmp_path / "attr_base.py"
    target.write_text(_ATTRIBUTE_BASE, encoding="utf-8")
    violations = no_inheritance.check_file(path=target)
    assert len(violations) == 1
    assert "non-name base" in violations[0]


def test_parametric_protocol_passes(*, tmp_path: Path) -> None:
    """`class X(Protocol[T]):` is permitted; the base resolves to `Protocol`."""
    target = tmp_path / "param_proto.py"
    target.write_text(_PARAMETRIC_PROTOCOL_OK, encoding="utf-8")
    assert no_inheritance.check_file(path=target) == []


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Shipped code conforms to the direct-parent allowlist."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert no_inheritance.main() == 0
