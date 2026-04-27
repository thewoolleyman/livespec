"""Tests for dev-tooling/checks/global_writes.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import global_writes  # noqa: E402

__all__: list[str] = []


_NO_MUTATION = (
    '"""docstring"""\n'
    "_CACHE: dict[str, int] = {}\n"
    "\n"
    "def lookup(*, key: str) -> int | None:\n"
    "    return _CACHE.get(key)\n"
)
_SUBSCRIPT_MUTATION = (
    '"""docstring"""\n'
    "_CACHE: dict[str, int] = {}\n"
    "\n"
    "def store(*, key: str, value: int) -> None:\n"
    "    _CACHE[key] = value\n"
)
_ATTRIBUTE_MUTATION = (
    '"""docstring"""\n'
    "class C: pass\n"
    "_INSTANCE = C()\n"
    "\n"
    "def mutate() -> None:\n"
    "    _INSTANCE.attr = 42\n"
)
_LOCAL_VAR_OK = (
    '"""docstring"""\n'
    "def f() -> None:\n"
    "    local: dict[str, int] = {}\n"
    "    local['k'] = 1\n"
)

_RELATIVE_GENERIC = Path(".claude-plugin/scripts/livespec/io/some_module.py")
_RELATIVE_FASTJSONSCHEMA = Path(
    ".claude-plugin/scripts/livespec/io/fastjsonschema_facade.py",
)


def test_no_mutation_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "module.py"
    target.write_text(_NO_MUTATION, encoding="utf-8")
    assert global_writes.check_file(path=target, relative=_RELATIVE_GENERIC) == []


def test_subscript_mutation_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "module.py"
    target.write_text(_SUBSCRIPT_MUTATION, encoding="utf-8")
    violations = global_writes.check_file(path=target, relative=_RELATIVE_GENERIC)
    assert len(violations) == 1
    assert "_CACHE" in violations[0]
    assert "subscript assignment" in violations[0]


def test_subscript_mutation_in_fastjsonschema_facade_passes(*, tmp_path: Path) -> None:
    """`_COMPILED[...] = ...` is exempted in fastjsonschema_facade.py per style doc."""
    text = _SUBSCRIPT_MUTATION.replace("_CACHE", "_COMPILED")
    target = tmp_path / "facade.py"
    target.write_text(text, encoding="utf-8")
    assert global_writes.check_file(path=target, relative=_RELATIVE_FASTJSONSCHEMA) == []


def test_other_subscript_mutation_in_fastjsonschema_facade_fails(*, tmp_path: Path) -> None:
    """The exemption is name-specific: only `_COMPILED` in that file passes."""
    target = tmp_path / "facade.py"
    target.write_text(_SUBSCRIPT_MUTATION, encoding="utf-8")
    violations = global_writes.check_file(path=target, relative=_RELATIVE_FASTJSONSCHEMA)
    assert len(violations) == 1
    assert "_CACHE" in violations[0]


def test_attribute_mutation_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "module.py"
    target.write_text(_ATTRIBUTE_MUTATION, encoding="utf-8")
    violations = global_writes.check_file(path=target, relative=_RELATIVE_GENERIC)
    assert len(violations) == 1
    assert "_INSTANCE" in violations[0]
    assert "attribute assignment" in violations[0]


def test_local_var_subscript_passes(*, tmp_path: Path) -> None:
    """Subscript assignment to a LOCAL variable (not a module-level binding) passes."""
    target = tmp_path / "module.py"
    target.write_text(_LOCAL_VAR_OK, encoding="utf-8")
    assert global_writes.check_file(path=target, relative=_RELATIVE_GENERIC) == []


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert global_writes.main() == 0
