"""Tests for dev-tooling/checks/supervisor_discipline.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import supervisor_discipline  # noqa: E402

__all__: list[str] = []


_COMMANDS_REL = Path(".claude-plugin/scripts/livespec/commands/seed.py")
_HELPER_REL = Path(".claude-plugin/scripts/livespec/parse/jsonc.py")
_DOCTOR_REL = Path(".claude-plugin/scripts/livespec/doctor/run_static.py")

_GOOD_SUPERVISOR = '''"""docstring"""
def main() -> int:
    log = ...  # noqa
    try:
        return 0
    except Exception as exc:
        log.error("oops", error=str(exc))
        return 1
'''

_SUPERVISOR_NO_CATCHALL = '''"""docstring"""
def main() -> int:
    return 0
'''

_SUPERVISOR_TWO_CATCHALLS = '''"""docstring"""
def main() -> int:
    log = ...  # noqa
    try:
        return 0
    except Exception:
        log.error("first")
        return 1
    finally:
        try:
            pass
        except Exception:
            log.error("second")
            return 1
'''

_SUPERVISOR_NO_LOGGING = '''"""docstring"""
def main() -> int:
    try:
        return 0
    except Exception:
        return 1
'''

_SUPERVISOR_NO_RETURN_INT = '''"""docstring"""
def main() -> int:
    log = ...  # noqa
    try:
        return 0
    except Exception as exc:
        log.error("oops", error=str(exc))
        raise
'''

_HELPER_WITH_CATCHALL = '''"""docstring"""
def helper() -> int:
    try:
        return 0
    except Exception:
        return 1
'''

_HELPER_WITH_SYS_EXIT = '''"""docstring"""
import sys
def helper() -> None:
    sys.exit(1)
'''

_HELPER_WITH_RAISE_SYSTEM_EXIT = '''"""docstring"""
def helper() -> None:
    raise SystemExit(1)
'''

_HELPER_OK = '''"""docstring"""
def helper(*, x: int) -> int:
    return x + 1
'''


def test_good_supervisor_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "seed.py"
    target.write_text(_GOOD_SUPERVISOR, encoding="utf-8")
    assert supervisor_discipline.check_file(path=target, relative=_COMMANDS_REL) == []


def test_supervisor_missing_catchall_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "seed.py"
    target.write_text(_SUPERVISOR_NO_CATCHALL, encoding="utf-8")
    violations = supervisor_discipline.check_file(path=target, relative=_COMMANDS_REL)
    assert len(violations) == 1
    assert "lacks the required catch-all" in violations[0]


def test_supervisor_two_catchalls_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "seed.py"
    target.write_text(_SUPERVISOR_TWO_CATCHALLS, encoding="utf-8")
    violations = supervisor_discipline.check_file(path=target, relative=_COMMANDS_REL)
    assert any("exactly one permitted" in v for v in violations)


def test_supervisor_no_logging_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "seed.py"
    target.write_text(_SUPERVISOR_NO_LOGGING, encoding="utf-8")
    violations = supervisor_discipline.check_file(path=target, relative=_COMMANDS_REL)
    assert any("logging call" in v for v in violations)


def test_supervisor_no_return_int_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "seed.py"
    target.write_text(_SUPERVISOR_NO_RETURN_INT, encoding="utf-8")
    violations = supervisor_discipline.check_file(path=target, relative=_COMMANDS_REL)
    assert any("exit-code emission" in v for v in violations)


def test_helper_with_catchall_outside_supervisor_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "jsonc.py"
    target.write_text(_HELPER_WITH_CATCHALL, encoding="utf-8")
    violations = supervisor_discipline.check_file(path=target, relative=_HELPER_REL)
    assert any("outside supervisor scope" in v for v in violations)


def test_sys_exit_outside_bin_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "jsonc.py"
    target.write_text(_HELPER_WITH_SYS_EXIT, encoding="utf-8")
    violations = supervisor_discipline.check_file(path=target, relative=_HELPER_REL)
    assert any("sys.exit()" in v for v in violations)


def test_raise_system_exit_outside_bin_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "jsonc.py"
    target.write_text(_HELPER_WITH_RAISE_SYSTEM_EXIT, encoding="utf-8")
    violations = supervisor_discipline.check_file(path=target, relative=_HELPER_REL)
    assert any("raise SystemExit" in v for v in violations)


def test_helper_no_supervisor_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "jsonc.py"
    target.write_text(_HELPER_OK, encoding="utf-8")
    assert supervisor_discipline.check_file(path=target, relative=_HELPER_REL) == []


def test_doctor_run_static_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "run_static.py"
    target.write_text(_GOOD_SUPERVISOR, encoding="utf-8")
    assert supervisor_discipline.check_file(path=target, relative=_DOCTOR_REL) == []


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Shipped code conforms to the supervisor-discipline rules."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert supervisor_discipline.main() == 0
