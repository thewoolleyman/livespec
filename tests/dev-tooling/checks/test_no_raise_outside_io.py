"""Tests for dev-tooling/checks/no_raise_outside_io.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import no_raise_outside_io  # noqa: E402

__all__: list[str] = []


_ERRORS_REL = Path(".claude-plugin/scripts/livespec/errors.py")
_IO_REL = Path(".claude-plugin/scripts/livespec/io/fs.py")
_PURE_REL = Path(".claude-plugin/scripts/livespec/parse/jsonc.py")
_COMMANDS_REL = Path(".claude-plugin/scripts/livespec/commands/seed.py")

_DOMAIN_NAMES = frozenset({
    "LivespecError",
    "UsageError",
    "PreconditionError",
    "ValidationError",
    "GitUnavailableError",
    "PermissionDeniedError",
    "ToolMissingError",
})

_RAISE_USAGE_ERROR = '''"""docstring"""
def helper() -> None:
    raise UsageError("bad input")
'''

_RAISE_PRECONDITION = '''"""docstring"""
def helper() -> None:
    raise PreconditionError("missing file")
'''

_RAISE_LIVESPEC_ERROR_BASE = '''"""docstring"""
def helper() -> None:
    raise LivespecError("base raise")
'''

_RAISE_TYPE_ERROR_OK = '''"""docstring"""
def helper() -> None:
    raise TypeError("bug class is fine anywhere")
'''

_RAISE_HELP_REQUESTED_OK = '''"""docstring"""
def helper() -> None:
    raise HelpRequested(text="...")
'''

_RAISE_VALUE_ERROR_OK = '''"""docstring"""
def helper() -> None:
    raise ValueError("bug-style — not in domain set")
'''

_BARE_RERAISE_OK = '''"""docstring"""
def helper() -> None:
    try:
        do_thing()
    except Exception:
        raise
'''


def test_io_file_can_raise_domain_errors(*, tmp_path: Path) -> None:
    target = tmp_path / "fs.py"
    target.write_text(_RAISE_PRECONDITION, encoding="utf-8")
    assert no_raise_outside_io.check_file(
        path=target,
        relative=_IO_REL,
        domain_names=_DOMAIN_NAMES,
    ) == []


def test_errors_file_can_raise_livespec_error(*, tmp_path: Path) -> None:
    target = tmp_path / "errors.py"
    target.write_text(_RAISE_LIVESPEC_ERROR_BASE, encoding="utf-8")
    assert no_raise_outside_io.check_file(
        path=target,
        relative=_ERRORS_REL,
        domain_names=_DOMAIN_NAMES,
    ) == []


def test_pure_file_raising_usage_error_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "jsonc.py"
    target.write_text(_RAISE_USAGE_ERROR, encoding="utf-8")
    violations = no_raise_outside_io.check_file(
        path=target,
        relative=_PURE_REL,
        domain_names=_DOMAIN_NAMES,
    )
    assert len(violations) == 1
    assert "UsageError" in violations[0]


def test_commands_file_raising_precondition_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "seed.py"
    target.write_text(_RAISE_PRECONDITION, encoding="utf-8")
    violations = no_raise_outside_io.check_file(
        path=target,
        relative=_COMMANDS_REL,
        domain_names=_DOMAIN_NAMES,
    )
    assert len(violations) == 1
    assert "PreconditionError" in violations[0]


def test_pure_file_raising_type_error_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "jsonc.py"
    target.write_text(_RAISE_TYPE_ERROR_OK, encoding="utf-8")
    assert no_raise_outside_io.check_file(
        path=target,
        relative=_PURE_REL,
        domain_names=_DOMAIN_NAMES,
    ) == []


def test_pure_file_raising_help_requested_passes(*, tmp_path: Path) -> None:
    """HelpRequested is NOT a LivespecError subclass; allowed anywhere."""
    target = tmp_path / "jsonc.py"
    target.write_text(_RAISE_HELP_REQUESTED_OK, encoding="utf-8")
    assert no_raise_outside_io.check_file(
        path=target,
        relative=_PURE_REL,
        domain_names=_DOMAIN_NAMES,
    ) == []


def test_pure_file_raising_value_error_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "jsonc.py"
    target.write_text(_RAISE_VALUE_ERROR_OK, encoding="utf-8")
    assert no_raise_outside_io.check_file(
        path=target,
        relative=_PURE_REL,
        domain_names=_DOMAIN_NAMES,
    ) == []


def test_bare_reraise_passes(*, tmp_path: Path) -> None:
    """`raise` with no expression (re-raise inside except) is not classified."""
    target = tmp_path / "jsonc.py"
    target.write_text(_BARE_RERAISE_OK, encoding="utf-8")
    assert no_raise_outside_io.check_file(
        path=target,
        relative=_PURE_REL,
        domain_names=_DOMAIN_NAMES,
    ) == []


def test_domain_error_names_parses_real_errors_py() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    errors_path = repo_root / _ERRORS_REL
    names = no_raise_outside_io.domain_error_names(errors_path=errors_path)
    expected = {
        "LivespecError",
        "UsageError",
        "PreconditionError",
        "ValidationError",
        "GitUnavailableError",
        "PermissionDeniedError",
        "ToolMissingError",
    }
    assert expected <= set(names)
    assert "HelpRequested" not in names


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Shipped code restricts LivespecError raises to io/** and errors.py."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert no_raise_outside_io.main() == 0
