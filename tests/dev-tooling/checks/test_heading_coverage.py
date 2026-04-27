"""Tests for dev-tooling/checks/heading_coverage.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import heading_coverage  # noqa: E402

__all__: list[str] = []


def _write_spec(*, repo: Path, rel: str, content: str) -> None:
    full = repo / rel
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")


def _write_coverage(*, repo: Path, entries: list[dict[str, str]]) -> None:
    target = repo / "tests" / "heading-coverage.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(entries), encoding="utf-8")


def test_no_spec_trees_pre_phase_6_passes(*, tmp_path: Path) -> None:
    """No SPECIFICATION/ + no SPECIFICATION.md → vacuously passes."""
    assert heading_coverage.check_repo(repo_root=tmp_path) == []


def test_main_spec_with_full_coverage_passes(*, tmp_path: Path) -> None:
    _write_spec(
        repo=tmp_path,
        rel="SPECIFICATION/intro.md",
        content="# Intro\n\n## Section A\n\n## Section B\n",
    )
    _write_coverage(
        repo=tmp_path,
        entries=[
            {"spec_root": "SPECIFICATION/", "heading": "## Section A", "test": "tests/x::test_a"},
            {"spec_root": "SPECIFICATION/", "heading": "## Section B", "test": "tests/x::test_b"},
        ],
    )
    assert heading_coverage.check_repo(repo_root=tmp_path) == []


def test_missing_coverage_entry_fails(*, tmp_path: Path) -> None:
    _write_spec(
        repo=tmp_path,
        rel="SPECIFICATION/intro.md",
        content="## Section A\n\n## Section B\n",
    )
    _write_coverage(
        repo=tmp_path,
        entries=[
            {"spec_root": "SPECIFICATION/", "heading": "## Section A", "test": "tests/x::test_a"},
        ],
    )
    violations = heading_coverage.check_repo(repo_root=tmp_path)
    assert len(violations) == 1
    assert "Section B" in violations[0]


def test_sub_spec_tree_uses_distinct_spec_root(*, tmp_path: Path) -> None:
    _write_spec(
        repo=tmp_path,
        rel="SPECIFICATION/intro.md",
        content="## Main A\n",
    )
    _write_spec(
        repo=tmp_path,
        rel="SPECIFICATION/templates/livespec/sub.md",
        content="## Sub A\n",
    )
    _write_coverage(
        repo=tmp_path,
        entries=[
            {"spec_root": "SPECIFICATION/", "heading": "## Main A", "test": "tests/x"},
            {
                "spec_root": "SPECIFICATION/templates/livespec/",
                "heading": "## Sub A",
                "test": "tests/y",
            },
        ],
    )
    assert heading_coverage.check_repo(repo_root=tmp_path) == []


def test_minimal_template_uses_empty_spec_root(*, tmp_path: Path) -> None:
    """Minimal template has SPECIFICATION.md at repo root and uses empty `spec_root`."""
    _write_spec(repo=tmp_path, rel="SPECIFICATION.md", content="## Single\n")
    _write_coverage(
        repo=tmp_path,
        entries=[{"spec_root": "", "heading": "## Single", "test": "tests/x"}],
    )
    assert heading_coverage.check_repo(repo_root=tmp_path) == []


def test_malformed_coverage_json_fails(*, tmp_path: Path) -> None:
    _write_spec(repo=tmp_path, rel="SPECIFICATION/x.md", content="## A\n")
    target = tmp_path / "tests" / "heading-coverage.json"
    target.parent.mkdir(parents=True)
    target.write_text("{not a list}", encoding="utf-8")
    violations = heading_coverage.check_repo(repo_root=tmp_path)
    assert any("cannot load" in v for v in violations)


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Pre-Phase-6: no SPECIFICATION/ tree exists; check vacuously passes."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert heading_coverage.main() == 0
