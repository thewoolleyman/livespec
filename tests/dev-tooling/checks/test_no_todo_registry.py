"""Tests for dev-tooling/checks/no_todo_registry.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import no_todo_registry  # noqa: E402

__all__: list[str] = []


def _write_coverage(*, repo: Path, entries: list[dict[str, str]]) -> None:
    target = repo / "tests" / "heading-coverage.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(entries), encoding="utf-8")


def test_missing_file_passes(*, tmp_path: Path) -> None:
    """Pre-Phase-6: file doesn't exist; vacuously passes."""
    assert no_todo_registry.check_repo(repo_root=tmp_path) == []


def test_empty_array_passes(*, tmp_path: Path) -> None:
    _write_coverage(repo=tmp_path, entries=[])
    assert no_todo_registry.check_repo(repo_root=tmp_path) == []


def test_real_test_passes(*, tmp_path: Path) -> None:
    _write_coverage(
        repo=tmp_path,
        entries=[
            {"spec_root": "SPECIFICATION/", "heading": "## A", "test": "tests/x::test_a"},
        ],
    )
    assert no_todo_registry.check_repo(repo_root=tmp_path) == []


def test_todo_test_fails(*, tmp_path: Path) -> None:
    _write_coverage(
        repo=tmp_path,
        entries=[
            {"spec_root": "SPECIFICATION/", "heading": "## A", "test": "TODO"},
        ],
    )
    violations = no_todo_registry.check_repo(repo_root=tmp_path)
    assert len(violations) == 1
    assert "TODO" in violations[0]
    assert "## A" in violations[0]


def test_mixed_passes_and_todos(*, tmp_path: Path) -> None:
    _write_coverage(
        repo=tmp_path,
        entries=[
            {"spec_root": "SPECIFICATION/", "heading": "## A", "test": "tests/x"},
            {"spec_root": "SPECIFICATION/", "heading": "## B", "test": "TODO"},
            {"spec_root": "SPECIFICATION/", "heading": "## C", "test": "tests/y"},
        ],
    )
    violations = no_todo_registry.check_repo(repo_root=tmp_path)
    assert len(violations) == 1
    assert "## B" in violations[0]


def test_malformed_file_fails(*, tmp_path: Path) -> None:
    target = tmp_path / "tests" / "heading-coverage.json"
    target.parent.mkdir(parents=True)
    target.write_text("{not a list}", encoding="utf-8")
    violations = no_todo_registry.check_repo(repo_root=tmp_path)
    assert any("cannot read or parse" in v for v in violations)


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Pre-Phase-6: tests/heading-coverage.json doesn't exist; vacuously passes."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert no_todo_registry.main() == 0
