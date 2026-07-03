"""Rule test for the orchestrator-plugin template's GitHub auth guard hook.

Asserts the template-shipped PreToolUse guard
(`templates/orchestrator-plugin/.claude/hooks/github_auth_guard.py`) blocks bare
`gh` / `git push` invocations that could fall through to ambient human OAuth,
while allowing unrelated commands and commands that name the configured
credential wrapper or App-token helper path.
"""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path
from types import ModuleType

import pytest

__all__: list[str] = []

_GUARD_PATH = (
    Path(__file__).resolve().parents[1]
    / "templates/orchestrator-plugin/.claude/hooks/github_auth_guard.py"
)
_SHELL_PATH = (
    Path(__file__).resolve().parents[1]
    / "templates/orchestrator-plugin/.claude/hooks/github-auth-guard.sh"
)


def _load_guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location("github_auth_guard", _GUARD_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_main(
    *,
    stdin_text: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str]:
    guard = _load_guard()
    monkeypatch.setattr(guard.sys, "stdin", io.StringIO(stdin_text))
    code = guard.main()
    return code, capsys.readouterr().out


def _write_config(*, project_dir: Path, body: str) -> None:
    (project_dir / ".livespec.jsonc").write_text(body, encoding="utf-8")


def test_shell_hook_is_executable() -> None:
    assert _SHELL_PATH.exists()
    assert _SHELL_PATH.stat().st_mode & 0o111


def test_blocks_bare_gh() -> None:
    assert _load_guard().should_block(command="gh pr create --fill") is True


def test_blocks_bare_git_push() -> None:
    assert _load_guard().should_block(command="git push origin HEAD") is True


def test_blocks_git_push_after_status() -> None:
    assert _load_guard().should_block(command="git status && git push") is True


def test_allows_unrelated_git_command() -> None:
    assert _load_guard().should_block(command="git status --short") is False


def test_allows_unrelated_command() -> None:
    assert _load_guard().should_block(command="just check") is False


def test_allows_configured_wrapper_token(*, tmp_path: Path) -> None:
    _write_config(
        project_dir=tmp_path,
        body='{ "credential_wrapper": ["with-openbrain-env.sh", "--"] }\n',
    )
    wrapped = "with-openbrain-env.sh -- gh pr create --fill"
    assert _load_guard().should_block(command=wrapped, project_dir=str(tmp_path)) is False


def test_configured_wrapper_absent_from_command_still_blocks(*, tmp_path: Path) -> None:
    _write_config(
        project_dir=tmp_path,
        body='{ "credential_wrapper": ["with-openbrain-env.sh", "--"] }\n',
    )
    assert _load_guard().should_block(command="gh pr create", project_dir=str(tmp_path)) is True


def test_allows_conventional_wrapper_fallback() -> None:
    wrapped = "with-livespec-env.sh -- git push origin HEAD"
    assert _load_guard().should_block(command=wrapped) is False


def test_allows_app_token_helper_path() -> None:
    helper = ".claude-plugin/scripts/bin/mint_app_token.py"
    command = f"GH_TOKEN=$({helper}) gh pr create --fill"
    assert _load_guard().should_block(command=command) is False


def test_main_emits_deny_for_bare_gh(
    *, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _run_main(
        stdin_text='{"tool_input": {"command": "gh pr create --fill"}}',
        monkeypatch=monkeypatch,
        capsys=capsys,
    )
    assert code == 0
    assert '"permissionDecision": "deny"' in out
    assert ".claude-plugin/scripts/bin/mint_app_token.py" in out


def test_main_passes_wrapped(
    *, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _run_main(
        stdin_text='{"tool_input": {"command": "with-livespec-env.sh -- gh pr create"}}',
        monkeypatch=monkeypatch,
        capsys=capsys,
    )
    assert code == 0
    assert out == ""


def test_main_passes_when_no_command(
    *, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _run_main(stdin_text='{"tool_input": {}}', monkeypatch=monkeypatch, capsys=capsys)
    assert code == 0
    assert out == ""


def test_main_passes_non_dict_payload(
    *, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _run_main(stdin_text="[]", monkeypatch=monkeypatch, capsys=capsys)
    assert code == 0
    assert out == ""


def test_main_fail_open_on_malformed_json(
    *, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _run_main(stdin_text="not json", monkeypatch=monkeypatch, capsys=capsys)
    assert code == 0
    assert out == ""
