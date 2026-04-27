"""Tests for dev-tooling/checks/main_guard.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import main_guard  # noqa: E402

__all__: list[str] = []


_NO_GUARD = '"""docstring"""\n__all__: list[str] = []\n'
_WITH_GUARD = '"""docstring"""\nif __name__ == "__main__":\n    pass\n'
_NESTED_NOT_FLAGGED = (
    '"""docstring"""\n'
    "def main() -> None:\n"
    '    if __name__ == "__main__":\n'  # nested inside def — not a top-level guard
    "        pass\n"
)


def test_no_guard_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "module.py"
    target.write_text(_NO_GUARD, encoding="utf-8")
    assert main_guard.check_file(path=target) == []


def test_top_level_guard_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "bad_module.py"
    target.write_text(_WITH_GUARD, encoding="utf-8")
    violations = main_guard.check_file(path=target)
    assert len(violations) == 1
    assert "forbidden in livespec/**" in violations[0]


def test_nested_guard_passes(*, tmp_path: Path) -> None:
    """Nested `if __name__ == "__main__":` (e.g., inside def) is not a top-level guard."""
    target = tmp_path / "nested.py"
    target.write_text(_NESTED_NOT_FLAGGED, encoding="utf-8")
    assert main_guard.check_file(path=target) == []


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """The shipped livespec/ tree has no top-level main guards — main() exits 0."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert main_guard.main() == 0
