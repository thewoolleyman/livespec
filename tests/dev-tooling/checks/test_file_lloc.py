"""Tests for dev-tooling/checks/file_lloc.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import file_lloc  # noqa: E402

__all__: list[str] = []


_TINY = '"""docstring"""\n__all__: list[str] = []\n'

# Shaped fixture: docstring + x = 1 + y = 2 + multi-line z = (...)
# expression. The parenthesized expression is ONE logical line per
# tokenize NEWLINE-token semantics.
_SHAPED = '"""docstring"""\nx = 1\ny = 2\nz = (\n    1\n    + 2\n    + 3\n)\n'
_SHAPED_LLOC = 4

_BLANK_LINES_DONT_COUNT = '"""docstring"""\n\n\nx = 1\n\ny = 2\n'
_BLANK_LLOC = 3

_COMMENTS_DONT_COUNT = (
    '"""docstring"""\n'
    "# top-level comment\n"
    "x = 1  # trailing comment\n"
    "# another comment\n"
    "y = 2\n"
)
_COMMENT_LLOC = 3

_BAD_SYNTAX = '"""docstring"""\ndef oops(\n'  # unterminated def


def _make_oversized(*, lloc: int) -> str:
    """Return a Python source whose tokenize-NEWLINE count is `lloc + 1`
    (the docstring + `lloc` `x = N` lines)."""
    return '"""d"""\n' + "\n".join(f"x = {i}" for i in range(lloc)) + "\n"


def test_tiny_file_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "tiny.py"
    target.write_text(_TINY, encoding="utf-8")
    assert file_lloc.check_file(path=target) == []


def test_count_logical_lines_returns_newline_token_count(*, tmp_path: Path) -> None:
    target = tmp_path / "shaped.py"
    target.write_text(_SHAPED, encoding="utf-8")
    assert file_lloc.count_logical_lines(path=target) == _SHAPED_LLOC


def test_blank_lines_excluded(*, tmp_path: Path) -> None:
    target = tmp_path / "blanks.py"
    target.write_text(_BLANK_LINES_DONT_COUNT, encoding="utf-8")
    assert file_lloc.count_logical_lines(path=target) == _BLANK_LLOC


def test_comments_excluded(*, tmp_path: Path) -> None:
    target = tmp_path / "comments.py"
    target.write_text(_COMMENTS_DONT_COUNT, encoding="utf-8")
    assert file_lloc.count_logical_lines(path=target) == _COMMENT_LLOC


def test_at_budget_passes(*, tmp_path: Path) -> None:
    """Exactly BUDGET logical lines is OK; only > BUDGET fails."""
    target = tmp_path / "at_budget.py"
    # _make_oversized(lloc=N) yields N+1 logical lines. To hit exactly
    # BUDGET, pass BUDGET-1.
    target.write_text(_make_oversized(lloc=file_lloc.BUDGET - 1), encoding="utf-8")
    assert file_lloc.count_logical_lines(path=target) == file_lloc.BUDGET
    assert file_lloc.check_file(path=target) == []


def test_above_budget_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "over.py"
    target.write_text(_make_oversized(lloc=file_lloc.BUDGET), encoding="utf-8")
    violations = file_lloc.check_file(path=target)
    assert len(violations) == 1
    assert f"exceeds budget {file_lloc.BUDGET}" in violations[0]


def test_syntax_error_returns_violation(*, tmp_path: Path) -> None:
    """Malformed source surfaces as a tokenize error, not a crash."""
    target = tmp_path / "bad.py"
    target.write_text(_BAD_SYNTAX, encoding="utf-8")
    violations = file_lloc.check_file(path=target)
    assert len(violations) == 1
    assert "tokenize error" in violations[0]


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """All scoped Python files in this repo are at or under the budget
    (sub-step 14a/14b refactored seed.py + revise.py to fit)."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert file_lloc.main() == 0
