"""Rule test for the orchestrator-plugin template's beads-access guard hook.

Asserts the template-shipped PreToolUse guard
(`templates/orchestrator-plugin/.claude/hooks/beads_access_guard.py`) blocks an
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
    / "templates/orchestrator-plugin/.claude/hooks/beads_access_guard.py"
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


def test_allows_independent_wrapper_bd() -> None:
    """An INDEPENDENT (non-family) tenant's own `with-<project>-env.sh` wrapper allows.

    Per `contracts.md` (v130): the guard
    recognizes ANY per-project credential-injection wrapper (`with-<id>-env.sh`),
    not only the family `with-livespec-env.sh`. A non-family wrapper such as
    `with-openbrain-env.sh` injecting the bare `BEADS_DOLT_PASSWORD` MUST pass
    through rather than be blocked.
    """
    wrapped = "with-openbrain-env.sh -- bd list --status all --json"
    assert _load_guard().should_block(command=wrapped) is False


def test_blocks_bare_bd_without_any_wrapper() -> None:
    """A bare `bd` with no `with-<id>-env.sh` wrapper at all is still blocked."""
    assert _load_guard().should_block(command="env BD=1 bd list --json") is True


def test_allows_unrelated_command() -> None:
    assert _load_guard().should_block(command="git status && ls -la") is False


def test_allows_plain_mysql_without_tenant_hint() -> None:
    assert _load_guard().should_block(command="mysql --help") is False


def _write_config(*, project_dir: Path, body: str) -> None:
    (project_dir / ".livespec.jsonc").write_text(body, encoding="utf-8")


def test_allows_configured_wrapper_token(*, tmp_path: Path) -> None:
    """A command under the CONFIGURED `credential_wrapper` token is allowed even
    when it is not a `with-<id>-env.sh` name (e.g. an `aws-vault` wrapper).
    """
    _write_config(
        project_dir=tmp_path,
        body=(
            "{\n"
            "  // the credential-injection wrapper for this repo\n"
            '  "credential_wrapper": ["aws-vault", "exec", "x", "--"]\n'
            "}\n"
        ),
    )
    wrapped = "aws-vault exec x -- bd list --status all --json"
    assert _load_guard().should_block(command=wrapped, project_dir=str(tmp_path)) is False


def test_configured_wrapper_absent_from_command_still_blocks(*, tmp_path: Path) -> None:
    """A configured wrapper whose token is NOT present in the command does not
    excuse a bare `bd` — it is still blocked.
    """
    _write_config(
        project_dir=tmp_path,
        body='{ "credential_wrapper": ["aws-vault", "exec", "x", "--"] }\n',
    )
    assert _load_guard().should_block(command="bd list --json", project_dir=str(tmp_path)) is True


def test_fallback_wrapper_when_no_credential_wrapper(*, tmp_path: Path) -> None:
    """With a readable config that declares NO `credential_wrapper`, the
    `with-<id>-env.sh` fallback still recognizes the conventional wrapper.
    """
    _write_config(project_dir=tmp_path, body='{ "template": "livespec" }\n')
    guard = _load_guard()
    wrapped = "with-openbrain-env.sh -- bd list --json"
    assert guard.should_block(command=wrapped, project_dir=str(tmp_path)) is False
    assert guard.should_block(command="bd list --json", project_dir=str(tmp_path)) is True


def test_non_string_wrapper_token_falls_back(*, tmp_path: Path) -> None:
    """A `credential_wrapper` whose first token is not a string is ignored; the
    guard falls back to the `with-<id>-env.sh` regex and blocks a bare `bd`.
    """
    _write_config(project_dir=tmp_path, body='{ "credential_wrapper": [123] }\n')
    assert _load_guard().should_block(command="bd list --json", project_dir=str(tmp_path)) is True


def test_fail_open_absent_config(*, tmp_path: Path) -> None:
    """No `.livespec.jsonc` at `project_dir`: the read fails open (no crash) and
    the guard falls back to the regex — a bare `bd` is still blocked.
    """
    guard = _load_guard()
    assert guard.should_block(command="bd list --json", project_dir=str(tmp_path)) is True
    wrapped = "with-livespec-env.sh -- bd list --json"
    assert guard.should_block(command=wrapped, project_dir=str(tmp_path)) is False


def test_fail_open_malformed_config(*, tmp_path: Path) -> None:
    """A malformed `.livespec.jsonc` fails open (no crash); the guard falls back
    to the regex and a bare `bd` is still blocked.
    """
    _write_config(project_dir=tmp_path, body="{ this is not valid json\n")
    assert _load_guard().should_block(command="bd list --json", project_dir=str(tmp_path)) is True


def test_no_project_dir_blocks_bare_bd() -> None:
    """With no `project_dir` (the default), only the regex fallback applies — a
    bare `bd` is blocked.
    """
    assert _load_guard().should_block(command="bd list --json") is True


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


def test_main_passes_independent_wrapper(
    *, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _run_main(
        stdin_text='{"tool_input": {"command": "with-openbrain-env.sh -- bd list"}}',
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
