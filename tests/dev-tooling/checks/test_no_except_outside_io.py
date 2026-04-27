"""Tests for dev-tooling/checks/no_except_outside_io.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import no_except_outside_io  # noqa: E402

__all__: list[str] = []


_IO_REL = Path(".claude-plugin/scripts/livespec/io/fs.py")
_PURE_REL = Path(".claude-plugin/scripts/livespec/parse/jsonc.py")
_DOCTOR_STATIC_REL = Path(".claude-plugin/scripts/livespec/doctor/static/foo.py")
_COMMANDS_REL = Path(".claude-plugin/scripts/livespec/commands/seed.py")
_DOCTOR_RUN_STATIC_REL = Path(".claude-plugin/scripts/livespec/doctor/run_static.py")

_SUPERVISOR_CATCHALL_OK = '''"""docstring"""
def main() -> int:
    log = ...  # noqa
    try:
        return 0
    except Exception as exc:
        log.error("oops", error=str(exc))
        return 1
'''

_SUPERVISOR_SPECIFIC_FORBIDDEN = '''"""docstring"""
def main() -> int:
    try:
        return 0
    except FileNotFoundError:
        return 1
    except Exception:
        return 1
'''

_PURE_SPECIFIC_EXCEPT = '''"""docstring"""
import json
def helper() -> None:
    try:
        json.loads("")
    except json.JSONDecodeError:
        pass
'''

_PURE_CATCHALL_EXCEPT = '''"""docstring"""
def helper() -> None:
    try:
        do_thing()
    except Exception:
        pass
'''

_PURE_NO_EXCEPT_OK = '''"""docstring"""
def helper(*, x: int) -> int:
    return x + 1
'''

_IO_SPECIFIC_EXCEPT_OK = '''"""docstring"""
def helper(*, x: str) -> None:
    try:
        open(x).read()
    except FileNotFoundError:
        pass
    except PermissionError:
        pass
'''

_DOCTOR_STATIC_EXCEPT_FORBIDDEN = '''"""docstring"""
def helper(*, x: str) -> None:
    try:
        do_thing()
    except OSError:
        pass
'''


def test_supervisor_catchall_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "seed.py"
    target.write_text(_SUPERVISOR_CATCHALL_OK, encoding="utf-8")
    assert no_except_outside_io.check_file(path=target, relative=_COMMANDS_REL) == []


def test_supervisor_specific_except_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "seed.py"
    target.write_text(_SUPERVISOR_SPECIFIC_FORBIDDEN, encoding="utf-8")
    violations = no_except_outside_io.check_file(path=target, relative=_COMMANDS_REL)
    assert any("FileNotFoundError" in v for v in violations)


def test_pure_specific_except_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "jsonc.py"
    target.write_text(_PURE_SPECIFIC_EXCEPT, encoding="utf-8")
    violations = no_except_outside_io.check_file(path=target, relative=_PURE_REL)
    assert any("JSONDecodeError" in v for v in violations)


def test_pure_catchall_except_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "jsonc.py"
    target.write_text(_PURE_CATCHALL_EXCEPT, encoding="utf-8")
    violations = no_except_outside_io.check_file(path=target, relative=_PURE_REL)
    assert any("Exception" in v for v in violations)


def test_pure_file_no_except_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "jsonc.py"
    target.write_text(_PURE_NO_EXCEPT_OK, encoding="utf-8")
    assert no_except_outside_io.check_file(path=target, relative=_PURE_REL) == []


def test_io_file_specific_except_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "fs.py"
    target.write_text(_IO_SPECIFIC_EXCEPT_OK, encoding="utf-8")
    assert no_except_outside_io.check_file(path=target, relative=_IO_REL) == []


def test_doctor_static_except_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "foo.py"
    target.write_text(_DOCTOR_STATIC_EXCEPT_FORBIDDEN, encoding="utf-8")
    violations = no_except_outside_io.check_file(path=target, relative=_DOCTOR_STATIC_REL)
    assert any("OSError" in v for v in violations)


def test_doctor_run_static_supervisor_catchall_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "run_static.py"
    target.write_text(_SUPERVISOR_CATCHALL_OK, encoding="utf-8")
    assert (
        no_except_outside_io.check_file(
            path=target,
            relative=_DOCTOR_RUN_STATIC_REL,
        )
        == []
    )


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """After parse/jsonc.py + proposed_change_topic_format.py refactors, repo conforms."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert no_except_outside_io.main() == 0
