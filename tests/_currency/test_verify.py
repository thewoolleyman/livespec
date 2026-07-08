"""Coverage for _currency.verify — verdict orchestration and the message."""

# ruff: noqa: SLF001

from __future__ import annotations

from pathlib import Path

import pytest
from _currency import verify
from _currency.verify import CurrencyVerdict

__all__: list[str] = []

_CLAUDE_CACHE = ".claude/plugins/cache/livespec/0.6.1"
_CODEX_CACHE = ".codex/plugins/cache/livespec/livespec/0.6.1"
_NON_CACHE = "repo/.claude-plugin"


def test_verify_currency_reports_checkout_mode_outside_installed_cache(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A non-cache plugin root yields the informational checkout verdict."""
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path / _NON_CACHE))
    verdict = verify.verify_currency()
    assert verdict == CurrencyVerdict(
        message=verify._CHECKOUT_MODE_MESSAGE, hard_fail=False, gate_sensitive=False
    )


def test_verify_currency_is_silent_when_running_matches_expected(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Matching running/expected builds yield a silent, non-failing verdict."""
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path / _CLAUDE_CACHE))
    monkeypatch.setattr(verify, "_running_build_id", lambda **_kwargs: "aaaaaaaaaaaa")
    monkeypatch.setattr(verify, "_expected_build_id", lambda **_kwargs: "aaaaaaaaaaaa")
    assert verify.verify_currency() == CurrencyVerdict(
        message=None, hard_fail=False, gate_sensitive=False
    )


def test_verify_currency_is_gate_sensitive_when_currency_unknown(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Unknown running or expected build is a gate-sensitive (not hard) verdict."""
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path / _CLAUDE_CACHE))
    monkeypatch.setattr(verify, "_running_build_id", lambda **_kwargs: None)
    monkeypatch.setattr(verify, "_expected_build_id", lambda **_kwargs: "bbbbbbbbbbbb")
    verdict = verify.verify_currency()
    assert verdict.message is not None
    assert "could not be verified" in verdict.message
    assert verdict.hard_fail is False
    assert verdict.gate_sensitive is True


def test_verify_currency_hard_fails_when_running_is_stale(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Both builds known and mismatched is a hard-fail verdict."""
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path / _CLAUDE_CACHE))
    monkeypatch.setattr(verify, "_running_build_id", lambda **_kwargs: "aaaaaaaaaaaa")
    monkeypatch.setattr(verify, "_expected_build_id", lambda **_kwargs: "bbbbbbbbbbbb")
    verdict = verify.verify_currency()
    assert verdict.message is not None
    assert "is stale" in verdict.message
    assert verdict.hard_fail is True
    assert verdict.gate_sensitive is False


def test_verify_currency_stale_message_names_claude_command_for_claude_cache(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A stale Claude install is told to run the scope-correct `claude plugin update`."""
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path / _CLAUDE_CACHE))
    monkeypatch.setattr(verify, "_running_build_id", lambda **_kwargs: "aaaaaaaaaaaa")
    monkeypatch.setattr(verify, "_expected_build_id", lambda **_kwargs: "bbbbbbbbbbbb")
    verdict = verify.verify_currency()
    assert verdict.message is not None
    assert "claude plugin update livespec@livespec --scope project" in verdict.message
    assert "just ensure-plugins" not in verdict.message
    assert "mise" not in verdict.message
    assert "codex plugin marketplace upgrade" not in verdict.message


def test_verify_currency_stale_message_names_codex_command_for_codex_cache(
    *, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A stale Codex install is told to run `codex plugin marketplace upgrade`."""
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path / _CODEX_CACHE))
    monkeypatch.setattr(verify, "_running_build_id", lambda **_kwargs: "aaaaaaaaaaaa")
    monkeypatch.setattr(verify, "_expected_build_id", lambda **_kwargs: "bbbbbbbbbbbb")
    verdict = verify.verify_currency()
    assert verdict.message is not None
    assert "codex plugin marketplace upgrade livespec" in verdict.message
    assert "claude plugin update" not in verdict.message
    assert "just ensure-plugins" not in verdict.message


def test_currency_message_covers_unknown_match_and_per_runtime_stale() -> None:
    """`_currency_message` returns unknown/None text and runtime-specific stale text."""
    unknown = verify._currency_message(
        running_build_id=None, expected_build_id="bbbbbbbbbbbb", codex=False
    )
    assert unknown is not None
    assert "could not be verified" in unknown
    assert (
        verify._currency_message(running_build_id="a" * 12, expected_build_id="a" * 12, codex=False)
        is None
    )
    claude_stale = verify._currency_message(
        running_build_id="aaaaaaaaaaaa", expected_build_id="bbbbbbbbbbbb", codex=False
    )
    assert claude_stale is not None
    assert "claude plugin update livespec@livespec --scope project" in claude_stale
    assert "just ensure-plugins" not in claude_stale
    codex_stale = verify._currency_message(
        running_build_id="aaaaaaaaaaaa", expected_build_id="bbbbbbbbbbbb", codex=True
    )
    assert codex_stale is not None
    assert "codex plugin marketplace upgrade livespec" in codex_stale
    assert "claude plugin update" not in codex_stale
