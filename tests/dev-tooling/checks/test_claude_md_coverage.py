"""Tests for dev-tooling/checks/claude_md_coverage.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import claude_md_coverage  # noqa: E402

__all__: list[str] = []


def test_directory_with_claude_md_passes(*, tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("# scope\n", encoding="utf-8")
    assert claude_md_coverage.check_directory(directory=tmp_path) == []


def test_directory_without_claude_md_fails(*, tmp_path: Path) -> None:
    violations = claude_md_coverage.check_directory(directory=tmp_path)
    assert len(violations) == 1
    assert "lacks CLAUDE.md" in violations[0]


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every directory under scripts/, tests/, dev-tooling/ has CLAUDE.md."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert claude_md_coverage.main() == 0


def test_missing_in_scoped_dir_fails(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A scoped dir missing CLAUDE.md surfaces in main()."""
    scope = tmp_path / "dev-tooling" / "checks"
    scope.mkdir(parents=True)
    # No CLAUDE.md on either dev-tooling/ or dev-tooling/checks/
    monkeypatch.chdir(tmp_path)
    assert claude_md_coverage.main() == 1


def test_vendor_subtree_excluded(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`_vendor/` subtree is exempt — vendored content has its own LICENSE."""
    scripts = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    scripts.mkdir(parents=True)
    (scripts / "CLAUDE.md").write_text("# livespec\n", encoding="utf-8")
    vendor = scripts / "_vendor" / "lib"
    vendor.mkdir(parents=True)
    # Deliberately no CLAUDE.md inside _vendor/lib/
    monkeypatch.chdir(tmp_path)
    assert claude_md_coverage.main() == 0


def test_fixtures_subtree_excluded(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`tests/fixtures/` subtree at any depth is exempt — fixtures are payload."""
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "CLAUDE.md").write_text("# tests\n", encoding="utf-8")
    fixtures = tests / "fixtures" / "deep" / "subtree"
    fixtures.mkdir(parents=True)
    # No CLAUDE.md inside tests/fixtures/...
    monkeypatch.chdir(tmp_path)
    assert claude_md_coverage.main() == 0


def test_pycache_excluded(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`__pycache__/` directories are exempt."""
    dev_tooling = tmp_path / "dev-tooling"
    dev_tooling.mkdir()
    (dev_tooling / "CLAUDE.md").write_text("# dev-tooling\n", encoding="utf-8")
    pycache = dev_tooling / "__pycache__"
    pycache.mkdir()
    monkeypatch.chdir(tmp_path)
    assert claude_md_coverage.main() == 0
