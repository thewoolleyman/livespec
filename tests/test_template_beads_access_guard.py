"""Rule test for the impl-plugin template's beads-access guard hook.

Asserts the template-shipped PreToolUse guard
(`templates/impl-plugin/.claude/hooks/beads_access_guard.py`) blocks an
un-wrapped `bd` / `dolt` / tenant-`mysql` invocation and passes a wrapped or
unrelated command through. The pure `should_block` predicate and the
`main` stdin->decision path are exercised directly by import — no subprocess —
realizing `contracts.md` section "Family agent-instruction core" (the
beads-access guard surface).
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
    / "templates/impl-plugin/.claude/hooks/beads_access_guard.py"
)


def _load_guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location("beads_access_guard", _GUARD_PATH)
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


def test_blocks_bare_bd() -> None:
    assert _load_guard().should_block(command="bd list --status all --json") is True


def test_blocks_dolt_sql() -> None:
    assert _load_guard().should_block(command="dolt sql -q 'select 1'") is True


def test_blocks_tenant_mysql() -> None:
    assert _load_guard().should_block(command="mysql -h 127.0.0.1 -P 3307 -u root") is True


def test_allows_wrapped_bd() -> None:
    wrapped = "/data/projects/1password-env-wrapper/with-livespec-env.sh -- bd list --json"
    assert _load_guard().should_block(command=wrapped) is False


def test_allows_unrelated_command() -> None:
    assert _load_guard().should_block(command="git status && ls -la") is False


def test_allows_plain_mysql_without_tenant_hint() -> None:
    assert _load_guard().should_block(command="mysql --help") is False


def test_main_emits_deny_for_bare_bd(
    *, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _run_main(
        stdin_text='{"tool_input": {"command": "bd list"}}',
        monkeypatch=monkeypatch,
        capsys=capsys,
    )
    assert code == 0
    assert '"permissionDecision": "deny"' in out


def test_main_passes_wrapped(
    *, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _run_main(
        stdin_text='{"tool_input": {"command": "with-livespec-env.sh -- bd list"}}',
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


def test_main_passes_tool_input_non_dict(
    *, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _run_main(stdin_text='{"tool_input": "x"}', monkeypatch=monkeypatch, capsys=capsys)
    assert code == 0
    assert out == ""


def test_main_passes_command_non_str(
    *, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _run_main(
        stdin_text='{"tool_input": {"command": 123}}',
        monkeypatch=monkeypatch,
        capsys=capsys,
    )
    assert code == 0
    assert out == ""


def test_main_fail_open_on_malformed_json(
    *, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _run_main(stdin_text="not json", monkeypatch=monkeypatch, capsys=capsys)
    assert code == 0
    assert out == ""
