"""Outside-in coverage test for `.claude/hooks/livespec_footgun_guard.py`.

The guard is a Claude Code PreToolUse(Bash) hook: it reads a tool-call JSON
payload on stdin and either stays SILENT (allow) or prints a `deny` decision
and exits 0. This drives the real stdin→stdout contract end to end and asserts
BOTH the new fail-closed memory-write rule AND the pre-existing git-footgun
rules, to full line+branch coverage of the guard.

The guard lives at `.claude/hooks/` — agent-runtime infra excluded from ruff and
pyright (per pyproject) — so it is loaded by file path via
`importlib.util.spec_from_file_location`, mirroring the loose-script test
precedent under `tests/dev-tooling/`.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_GUARD = _REPO_ROOT / ".claude" / "hooks" / "livespec_footgun_guard.py"

# A path under the per-project Claude auto-memory store. The `~`, `$HOME`, and
# absolute forms all carry the `.claude/projects/<slug>/memory/` infix the guard
# anchors on.
_MEM = "~/.claude/projects/-data-projects-livespec/memory"
_MEM_ABS = "/home/ubuntu/.claude/projects/-data-projects-livespec/memory"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("livespec_footgun_guard", _GUARD)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GUARD = _load_module()


def _bash(command: str) -> str:
    return json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})


def _run(
    payload: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> str:
    """Drive `main()` with `payload` on stdin; return whatever it prints."""
    monkeypatch.setattr(GUARD.sys, "stdin", io.StringIO(payload))
    with pytest.raises(SystemExit) as exc:
        GUARD.main()
    assert exc.value.code == 0
    return capsys.readouterr().out


def _assert_deny(out: str, reason_marker: str) -> None:
    assert out != ""
    assert '"permissionDecision": "deny"' in out
    assert reason_marker in out


def _assert_allow(out: str) -> None:
    assert out == ""


# --------------------------------------------------------------------------
# Fail-closed memory-write rule.
# --------------------------------------------------------------------------

_MEMORY_WRITE_VECTORS = [
    f"cat >> {_MEM}/x.md",
    f"echo hi > {_MEM}/y.md",
    f"printf x 1> {_MEM}/y.md",
    f"echo hi &> {_MEM}/y.md",
    f"cat >> {_MEM_ABS}/x.md",
    "cat >> $HOME/.claude/projects/-data-projects-livespec/memory/x.md",
    f"echo hi | tee {_MEM}/z.md",
    f"echo hi | tee -a {_MEM}/z.md",
    f"truncate -s 0 {_MEM}/z.md",
    f"dd if=/dev/null of={_MEM}/z.md",
    f"sed -i s/a/b/ {_MEM}/MEMORY.md",
    f"sed --in-place s/a/b/ {_MEM}/MEMORY.md",
    f"cp /tmp/src {_MEM}/dst.md",
    f"mv /tmp/src {_MEM}/dst.md",
    f"rsync /tmp/src {_MEM}/dst.md",
    f"install /tmp/src {_MEM}/dst.md",
    f"ln -s /tmp/src {_MEM}/dst.md",
    f"cat > {_MEM}/z.md <<'EOF'\nbody line\nEOF",
]


@pytest.mark.parametrize("command", _MEMORY_WRITE_VECTORS)
def test_memory_write_denied(
    command: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_deny(_run(_bash(command), monkeypatch, capsys), "auto-memory store")


_MEMORY_READ_VECTORS = [
    f"cat {_MEM}/x.md",
    f"grep foo {_MEM}/x.md",
    f"cp {_MEM}/x.md /tmp/out.md",
    f"cat {_MEM}/x.md > /tmp/out.md",
    f"ls {_MEM}/",
    f"diff {_MEM}/a.md {_MEM}/b.md",
    # A here-doc whose BODY mentions the bypass but whose TARGET is /tmp: the
    # body is stripped, so it must NOT trip the redirect rule.
    f"cat > /tmp/doc.md <<'EOF'\ncat >> {_MEM}/x.md\nEOF",
]


@pytest.mark.parametrize("command", _MEMORY_READ_VECTORS)
def test_memory_read_allowed(
    command: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_allow(_run(_bash(command), monkeypatch, capsys))


# --------------------------------------------------------------------------
# Pre-existing git-footgun rules (still enforced).
# --------------------------------------------------------------------------

_NO_VERIFY_VECTORS = [
    "git commit --no-verify -m x",
    "git push --no-verify",
    "FOO=bar git commit --no-verify -m x",
    "env FOO=1 BAR=2 git commit --no-verify",
    "mise exec -- git commit --no-verify -m x",
    "mise x -- git push --no-verify",
    "mise exec --verbose -- git commit --no-verify",
    "sudo mise exec -- git commit --no-verify",
    "git -C /repo commit --no-verify",
    "git --no-pager commit --no-verify",
]


@pytest.mark.parametrize("command", _NO_VERIFY_VECTORS)
def test_no_verify_denied(
    command: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_deny(_run(_bash(command), monkeypatch, capsys), "--no-verify")


_CORE_BARE_VECTORS = [
    "git config core.bare true",
    "git config core.bare=true",
    "git config core.bare=1",
    "git config core.bare yes",
    "sudo git config core.bare true",
]


@pytest.mark.parametrize("command", _CORE_BARE_VECTORS)
def test_core_bare_denied(
    command: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_deny(_run(_bash(command), monkeypatch, capsys), "core.bare")


def test_lefthook_disable_denied(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_deny(_run(_bash("LEFTHOOK=0 git commit -m x"), monkeypatch, capsys), "LEFTHOOK")


_GIT_ALLOW_VECTORS = [
    "git status",
    "git commit -m hello",  # commit without --no-verify
    "git config core.bare false",  # core.bare set to a falsy value
    "git config --get core.bare",  # a read, not a set
    "git config user.name someone",  # a non-core.bare config key
    "git -- status",  # bare `--` then a non-footgun subcommand
    "git -C /tmp",  # global opt consumes its arg, no subcommand left
    "mise",  # wrapper with nothing after it
    "echo hi",  # leading command isn't git
    "echo a ;  ; echo b",  # empty middle segment is dropped
    'echo "unterminated',  # unbalanced quote → shlex fails → fail open
]


@pytest.mark.parametrize("command", _GIT_ALLOW_VECTORS)
def test_git_like_allowed(
    command: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_allow(_run(_bash(command), monkeypatch, capsys))


# --------------------------------------------------------------------------
# main() dispatch / fail-open edges.
# --------------------------------------------------------------------------


def test_empty_stdin_allows(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_allow(_run("", monkeypatch, capsys))


def test_blank_stdin_allows(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_allow(_run("   \n  ", monkeypatch, capsys))


def test_whitespace_command_allows(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Non-empty command string but no real segments → the segment loop is skipped.
    _assert_allow(_run(_bash("   "), monkeypatch, capsys))


def test_heredoc_without_terminator_allows(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Here-doc body runs to EOF with no closing terminator line.
    _assert_allow(_run(_bash("cat <<EOF\nbody never closes"), monkeypatch, capsys))


def test_non_bash_tool_allows(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = json.dumps(
        {"tool_name": "Write", "tool_input": {"command": "git commit --no-verify"}}
    )
    _assert_allow(_run(payload, monkeypatch, capsys))


def test_missing_command_allows(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {}})
    _assert_allow(_run(payload, monkeypatch, capsys))


def test_invalid_json_allows(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _assert_allow(_run("this is not json", monkeypatch, capsys))


def test_non_object_json_allows(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Valid JSON, but a scalar — `.get` raises AttributeError → caught, fail open.
    _assert_allow(_run("5", monkeypatch, capsys))


def test_non_dict_tool_input_allows(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = json.dumps({"tool_name": "Bash", "tool_input": "oops"})
    _assert_allow(_run(payload, monkeypatch, capsys))
