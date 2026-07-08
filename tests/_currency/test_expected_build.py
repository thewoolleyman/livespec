"""Focused coverage for _currency.expected_build pin resolution."""

# ruff: noqa: SLF001

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from _currency import expected_build

__all__: list[str] = []


def test_expected_build_id_reads_claude_marketplace_for_claude_cache(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A Claude installed-cache root resolves the Claude marketplace clone HEAD."""
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    claude_root = home / ".claude" / "plugins" / "cache" / "livespec" / "0.6.1"
    expected_marketplace = home / ".claude" / "plugins" / "marketplaces" / "livespec"

    def fake_head(*, repository: Path) -> str:
        assert repository == expected_marketplace
        return "abcdef123456"

    monkeypatch.setattr(expected_build, "_git_rev_parse_head", fake_head)
    assert expected_build._expected_build_id(plugin_root=claude_root) == "abcdef123456"


def test_expected_build_id_reads_codex_marketplace_for_codex_cache(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A Codex installed-cache root resolves the Codex marketplace clone HEAD."""
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    codex_root = home / ".codex" / "plugins" / "cache" / "livespec" / "livespec" / "0.6.1"
    expected_marketplace = home / ".codex" / ".tmp" / "marketplaces" / "livespec"

    def fake_head(*, repository: Path) -> str:
        assert repository == expected_marketplace
        return "cccccccccccc"

    monkeypatch.setattr(expected_build, "_git_rev_parse_head", fake_head)
    assert expected_build._expected_build_id(plugin_root=codex_root) == "cccccccccccc"


def test_git_rev_parse_head_returns_none_for_missing_repository(*, tmp_path: Path) -> None:
    """A non-existent marketplace clone leaves expected currency unknown."""
    assert expected_build._git_rev_parse_head(repository=tmp_path / "absent") is None


def test_git_rev_parse_head_accepts_success(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Expected-build lookup accepts a successful 12-hex git result."""
    repository = tmp_path / "marketplace"
    repository.mkdir()

    def successful_run(
        args: list[str], *, capture_output: bool, check: bool, text: bool
    ) -> SimpleNamespace:
        assert args == ["/usr/bin/git", "-C", str(repository), "rev-parse", "--short=12", "HEAD"]
        assert capture_output is True
        assert check is False
        assert text is True
        return SimpleNamespace(returncode=0, stdout="abcdef123456\n")

    monkeypatch.setattr(expected_build.subprocess, "run", successful_run)
    assert expected_build._git_rev_parse_head(repository=repository) == "abcdef123456"


def test_git_rev_parse_head_rejects_failed_git(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A non-zero git process result leaves expected currency unknown."""
    repository = tmp_path / "marketplace"
    repository.mkdir()

    def failing_run(
        args: list[str], *, capture_output: bool, check: bool, text: bool
    ) -> SimpleNamespace:
        assert args[0] == "/usr/bin/git"
        assert capture_output is True
        assert check is False
        assert text is True
        return SimpleNamespace(returncode=1, stdout="abcdef123456\n")

    monkeypatch.setattr(expected_build.subprocess, "run", failing_run)
    assert expected_build._git_rev_parse_head(repository=repository) is None


def test_git_rev_parse_head_rejects_invalid_sha(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A successful git process with a non-SHA stdout stays unknown."""
    repository = tmp_path / "marketplace"
    repository.mkdir()

    def invalid_sha_run(
        args: list[str], *, capture_output: bool, check: bool, text: bool
    ) -> SimpleNamespace:
        assert args[0] == "/usr/bin/git"
        assert capture_output is True
        assert check is False
        assert text is True
        return SimpleNamespace(returncode=0, stdout="not-a-sha\n")

    monkeypatch.setattr(expected_build.subprocess, "run", invalid_sha_run)
    assert expected_build._git_rev_parse_head(repository=repository) is None


def test_git_rev_parse_head_handles_missing_git(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An OSError from process launch leaves expected currency unknown."""
    repository = tmp_path / "marketplace"
    repository.mkdir()

    def raising_run(args: list[str], *, capture_output: bool, check: bool, text: bool) -> None:
        assert args[0] == "/usr/bin/git"
        assert capture_output is True
        assert check is False
        assert text is True
        raise OSError("git unavailable")

    monkeypatch.setattr(expected_build.subprocess, "run", raising_run)
    assert expected_build._git_rev_parse_head(repository=repository) is None
