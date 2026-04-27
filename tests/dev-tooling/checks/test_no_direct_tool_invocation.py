"""Tests for dev-tooling/checks/no_direct_tool_invocation.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import no_direct_tool_invocation  # noqa: E402

__all__: list[str] = []


_GOOD_LEFTHOOK = """pre-commit:
  commands:
    check:
      run: just check

pre-push:
  commands:
    check:
      run: just check
"""

_BAD_DIRECT_RUFF = """pre-commit:
  commands:
    lint:
      run: ruff check .
"""

_BAD_DIRECT_PYTEST = """jobs:
  test:
    steps:
      - run: pytest tests/
"""

_COMMENT_ONLY_OK = """# A comment mentioning ruff and pytest is fine.
pre-commit:
  commands:
    check:
      run: just check
"""

_TOOL_AS_TARGET_NAME_OK = """jobs:
  test:
    steps:
      - run: just check-tests
"""


def test_good_lefthook_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "lefthook.yml"
    target.write_text(_GOOD_LEFTHOOK, encoding="utf-8")
    assert no_direct_tool_invocation.check_file(path=target) == []


def test_direct_ruff_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "lefthook.yml"
    target.write_text(_BAD_DIRECT_RUFF, encoding="utf-8")
    violations = no_direct_tool_invocation.check_file(path=target)
    assert any("ruff" in v for v in violations)


def test_direct_pytest_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "ci.yml"
    target.write_text(_BAD_DIRECT_PYTEST, encoding="utf-8")
    violations = no_direct_tool_invocation.check_file(path=target)
    assert any("pytest" in v for v in violations)


def test_comments_exempt(*, tmp_path: Path) -> None:
    """Tool names inside YAML comments are not violations."""
    target = tmp_path / "lefthook.yml"
    target.write_text(_COMMENT_ONLY_OK, encoding="utf-8")
    assert no_direct_tool_invocation.check_file(path=target) == []


def test_tool_as_substring_in_target_name_ok(*, tmp_path: Path) -> None:
    """`just check-tests` shouldn't trigger the `pytest` rule (word-boundary match)."""
    target = tmp_path / "ci.yml"
    target.write_text(_TOOL_AS_TARGET_NAME_OK, encoding="utf-8")
    assert no_direct_tool_invocation.check_file(path=target) == []


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """The shipped lefthook.yml + .github/workflows/*.yml only invoke `just <target>`."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert no_direct_tool_invocation.main() == 0
