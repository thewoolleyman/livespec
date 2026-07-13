"""Tests for tmuxio.py — the tmux subprocess boundary.

Run: ``uv run pytest .claude/skills/overseer/ -q``. No REAL tmux runs: a fake
``run`` callable (same shape as ``subprocess.run``) is injected so we assert on
the exact argv tmux would be invoked with, and on fail-soft sentinels.
"""

import types

import tmuxio


class FakeRun:
    """Stands in for ``subprocess.run``; records argv + stdin, returns canned result."""

    def __init__(self, *, returncode=0, stdout="", raises=None):
        self.returncode = returncode
        self.stdout = stdout
        self.raises = raises
        self.calls = []

    def __call__(self, argv, *, input=None, capture_output=None, text=None, check=None):
        self.calls.append({"argv": argv, "input": input})
        if self.raises is not None:
            raise self.raises
        return types.SimpleNamespace(returncode=self.returncode, stdout=self.stdout, stderr="")


def _io(**kwargs):
    fake = FakeRun(**kwargs)
    return tmuxio.TmuxIO(run=fake), fake


# --------------------------------------------------------------------------- #
# Reads.
# --------------------------------------------------------------------------- #


def test_capture_pane_argv_and_output():
    io, fake = _io(stdout="pane text here\n")
    assert io.capture_pane("livespec:topic") == "pane text here\n"
    assert fake.calls[0]["argv"] == ["tmux", "capture-pane", "-p", "-t", "livespec:topic"]


def test_capture_pane_empty_on_error():
    io, _ = _io(returncode=1, stdout="ignored")
    assert io.capture_pane("s") == ""


def test_pane_current_command_strips_and_nones():
    io, fake = _io(stdout="node\n")
    assert io.pane_current_command("s") == "node"
    assert fake.calls[0]["argv"] == [
        "tmux",
        "display-message",
        "-p",
        "-t",
        "s",
        "#{pane_current_command}",
    ]
    io2, _ = _io(stdout="   \n")  # whitespace-only → None
    assert io2.pane_current_command("s") is None
    io3, _ = _io(returncode=1)
    assert io3.pane_current_command("s") is None


def test_pane_current_path_format():
    io, fake = _io(stdout="/data/projects/livespec\n")
    assert io.pane_current_path("s") == "/data/projects/livespec"
    assert fake.calls[0]["argv"][-1] == "#{pane_current_path}"


def test_session_exists_is_exact_membership_not_prefix():
    # B1: session_exists uses EXACT list-sessions membership, not the prefix-prone
    # `has-session -t <name>` (which matches `foobar` for target `foo`).
    io, fake = _io(stdout="foo\nbar\n")
    assert io.session_exists("foo") is True
    assert fake.calls[0]["argv"] == ["tmux", "list-sessions", "-F", "#{session_name}"]
    # a longer session sharing the prefix must NOT satisfy the exact target
    io2, _ = _io(stdout="foobar\n")
    assert io2.session_exists("foo") is False
    io3, _ = _io(returncode=1)  # no server / error → not live
    assert io3.session_exists("foo") is False


def test_list_sessions_parses_lines():
    io, fake = _io(stdout="livespec:a\nother:b\n\n")
    assert io.list_sessions() == ["livespec:a", "other:b"]
    assert fake.calls[0]["argv"] == ["tmux", "list-sessions", "-F", "#{session_name}"]
    io2, _ = _io(returncode=1)
    assert io2.list_sessions() == []


# --------------------------------------------------------------------------- #
# Writes.
# --------------------------------------------------------------------------- #


def test_send_keys_argv():
    io, fake = _io()
    assert io.send_keys("s", "Enter") is True
    assert fake.calls[0]["argv"] == ["tmux", "send-keys", "-t", "s", "Enter"]


def test_bracketed_paste_loads_then_pastes_with_stdin():
    io, fake = _io()
    assert io.bracketed_paste("livespec--t", "line1\nline2") is True
    # First call loads the buffer from stdin; second pastes bracketed + deletes.
    load_argv = fake.calls[0]["argv"]
    assert load_argv[:3] == ["tmux", "load-buffer", "-b"]
    buffer_name = load_argv[3]
    # B6: the buffer name is UNIQUE per paste (pid + counter), not the fixed global.
    assert buffer_name.startswith("overseer-inject-")
    assert load_argv[4] == "-"
    assert fake.calls[0]["input"] == "line1\nline2"
    # the SAME unique buffer is pasted then deleted.
    assert fake.calls[1]["argv"] == [
        "tmux",
        "paste-buffer",
        "-b",
        buffer_name,
        "-p",
        "-d",
        "-t",
        "livespec--t",
    ]


def test_bracketed_paste_false_when_load_fails():
    io, _ = _io(returncode=1)
    assert io.bracketed_paste("s", "x") is False


def test_respawn_pane_argv_is_kill_and_cwd():
    io, fake = _io()
    assert io.respawn_pane("livespec:t", "/data/projects/livespec", "claude -n t") is True
    assert fake.calls[0]["argv"] == [
        "tmux",
        "respawn-pane",
        "-k",
        "-c",
        "/data/projects/livespec",
        "-t",
        "livespec:t",
        "claude -n t",
    ]


def test_new_session_argv():
    io, fake = _io()
    assert io.new_session("livespec:t", "/data/projects/livespec") is True
    assert fake.calls[0]["argv"] == [
        "tmux",
        "new-session",
        "-d",
        "-s",
        "livespec:t",
        "-c",
        "/data/projects/livespec",
    ]


# --------------------------------------------------------------------------- #
# Fail-soft: a missing tmux binary never crashes the caller.
# --------------------------------------------------------------------------- #


def test_missing_binary_is_fail_soft():
    io, _ = _io(raises=FileNotFoundError("tmux not found"))
    assert io.capture_pane("s") == ""
    assert io.session_exists("s") is False
    assert io.list_sessions() == []
    assert io.pane_current_command("s") is None
    assert io.bracketed_paste("s", "x") is False
    assert io.respawn_pane("s", "/tmp", "claude") is False
