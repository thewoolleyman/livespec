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
    # Reliable read via list-panes (not the flaky display-message); the row is
    # `#{pane_id}\t#{pane_active}\t<field>`.
    io, fake = _io(stdout="%1\t1\tnode\n")
    assert io.pane_current_command("s") == "node"
    assert fake.calls[0]["argv"] == [
        "tmux",
        "list-panes",
        "-t",
        "s",
        "-F",
        "#{pane_id}\t#{pane_active}\t#{pane_current_command}",
    ]
    io2, _ = _io(stdout="%1\t1\t   \n")  # whitespace-only field → None
    assert io2.pane_current_command("s") is None
    io3, _ = _io(returncode=1)
    assert io3.pane_current_command("s") is None


def test_pane_current_path_format():
    io, fake = _io(stdout="%1\t1\t/data/projects/livespec\n")
    assert io.pane_current_path("s") == "/data/projects/livespec"
    assert fake.calls[0]["argv"][-1] == "#{pane_id}\t#{pane_active}\t#{pane_current_path}"


def test_pane_id_format():
    # RB3: resolve the exact pane id to target instead of the prefix-prone name.
    io, fake = _io(stdout="%5\t1\t%5\n")
    assert io.pane_id("s") == "%5"
    assert fake.calls[0]["argv"] == [
        "tmux",
        "list-panes",
        "-t",
        "s",
        "-F",
        "#{pane_id}\t#{pane_active}\t#{pane_id}",
    ]
    io2, _ = _io(returncode=1)  # session gone → None (fail-soft)
    assert io2.pane_id("s") is None


def test_pane_field_pane_id_target_filters_exact_pane():
    # A PANE-ID target selects THAT pane's field, not the active/first (RB3).
    io, _ = _io(stdout="%1\t0\tzsh\n%5\t1\tnode\n")
    assert io.pane_current_command("%5") == "node"
    assert io.pane_current_command("%1") == "zsh"


def test_pane_field_session_target_picks_active_pane():
    # A SESSION-NAME target selects the active pane (pane_active == 1).
    io, _ = _io(stdout="%1\t0\tzsh\n%5\t1\tnode\n")
    assert io.pane_current_command("s") == "node"


def test_pane_field_pane_id_not_present_is_none():
    io, _ = _io(stdout="%1\t1\tnode\n")
    assert io.pane_current_command("%9") is None


def test_pane_field_empty_output_is_none():
    io, _ = _io(stdout="")
    assert io.pane_current_command("s") is None


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


def test_pane_pid_parses_int_and_fails_soft():
    # The pane PID is read through the same `list-panes` row as every other
    # per-pane field, then int-parsed; anything unparseable fails soft to None.
    io, fake = _io(stdout="%5\t1\t482913\n")
    assert io.pane_pid("s") == 482913
    assert fake.calls[0]["argv"] == [
        "tmux",
        "list-panes",
        "-t",
        "s",
        "-F",
        "#{pane_id}\t#{pane_active}\t#{pane_pid}",
    ]
    io2, _ = _io(stdout="%5\t1\tnot-a-pid\n")  # non-numeric value → None
    assert io2.pane_pid("s") is None
    io3, _ = _io(stdout="%5\t1\t   \n")  # unreadable/empty field → None
    assert io3.pane_pid("s") is None
    io4, _ = _io(returncode=1)  # session gone → None (fail-soft)
    assert io4.pane_pid("s") is None


def test_pane_pid_sessions_parses_every_pane_across_sessions():
    # The process-side of the registry→tmux join: EVERY pane, all sessions.
    io, fake = _io(stdout="482913\tlivespec:a\n482920\tlivespec:a\n99001\tother:b\n")
    assert io.pane_pid_sessions() == {
        482913: "livespec:a",
        482920: "livespec:a",
        99001: "other:b",
    }
    assert fake.calls[0]["argv"] == [
        "tmux",
        "list-panes",
        "-a",
        "-F",
        "#{pane_pid}\t#{session_name}",
    ]


def test_pane_pid_sessions_skips_malformed_rows():
    # A non-integer pid, a blank line, and a row with no session name are each
    # skipped fail-soft rather than crashing the whole enumeration.
    io, _ = _io(stdout="482913\tlivespec:a\nnot-a-pid\tlivespec:b\n\n7\t   \n99001\tother:b\n")
    assert io.pane_pid_sessions() == {482913: "livespec:a", 99001: "other:b"}


def test_pane_pid_sessions_empty_on_error():
    io, _ = _io(returncode=1, stdout="482913\tlivespec:a\n")
    assert io.pane_pid_sessions() == {}


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


def test_split_window_top_argv_and_pane_id():
    # The two-pane bootstrap: split THIS pane's window, new pane ABOVE (-b -v),
    # keep focus (-d), print the new pane id (-P -F). Target is the skill's own
    # $TMUX_PANE — never a session grabbed by name.
    io, fake = _io(stdout="%47\n")
    assert io.split_window_top("%20", "/data/projects/livespec", "overseerd") == "%47"
    assert fake.calls[0]["argv"] == [
        "tmux",
        "split-window",
        "-v",
        "-b",
        "-d",
        "-P",
        "-F",
        "#{pane_id}",
        "-t",
        "%20",
        "-c",
        "/data/projects/livespec",
        "overseerd",
    ]
    io2, _ = _io(returncode=1)  # split failed → None (fail-soft)
    assert io2.split_window_top("%20", "/tmp", "overseerd") is None
    io3, _ = _io(stdout="   \n")  # empty pane id → None
    assert io3.split_window_top("%20", "/tmp", "overseerd") is None


def test_set_pane_title_argv():
    io, fake = _io()
    assert io.set_pane_title("%47", "overseer-daemon") is True
    assert fake.calls[0]["argv"] == [
        "tmux",
        "select-pane",
        "-t",
        "%47",
        "-T",
        "overseer-daemon",
    ]


def test_select_layout_even_argv():
    io, fake = _io()
    assert io.select_layout_even("%20") is True
    assert fake.calls[0]["argv"] == ["tmux", "select-layout", "-t", "%20", "even-vertical"]
    io2, _ = _io(returncode=1)  # fail-soft
    assert io2.select_layout_even("%20") is False


def test_pane_by_title_finds_matching_pane_id():
    # The idempotent-path read: which pane in THIS window carries the title.
    io, fake = _io(stdout="%20\tzsh\n%47\toverseer-daemon\n")
    assert io.pane_by_title("%20", "overseer-daemon") == "%47"
    assert fake.calls[0]["argv"] == [
        "tmux",
        "list-panes",
        "-t",
        "%20",
        "-F",
        "#{pane_id}\t#{pane_title}",
    ]
    io2, _ = _io(stdout="%20\tzsh\n")  # title absent in this window → None
    assert io2.pane_by_title("%20", "overseer-daemon") is None
    io3, _ = _io(returncode=1)  # list failed → None (fail-soft)
    assert io3.pane_by_title("%20", "overseer-daemon") is None


def test_set_pane_height_percent_argv():
    # Percentage sizing (tmux 3.5a) — the `%` suffix is what makes it a share of
    # the window rather than an absolute row count.
    io, fake = _io()
    assert io.set_pane_height_percent("%47", 25) is True
    assert fake.calls[0]["argv"] == ["tmux", "resize-pane", "-t", "%47", "-y", "25%"]
    io2, _ = _io(returncode=1)  # fail-soft
    assert io2.set_pane_height_percent("%47", 25) is False


def test_rename_window_renames_then_pins_automatic_rename_off():
    # Pinning is PART of renaming: without `automatic-rename off` tmux re-derives
    # the window name from its foreground command and overwrites NAME.
    io, fake = _io()
    assert io.rename_window("%20", "overseer") is True
    assert fake.calls[0]["argv"] == ["tmux", "rename-window", "-t", "%20", "overseer"]
    assert fake.calls[1]["argv"] == [
        "tmux",
        "set-window-option",
        "-t",
        "%20",
        "automatic-rename",
        "off",
    ]


def test_rename_window_false_when_rename_fails_and_skips_the_pin():
    io, fake = _io(returncode=1)
    assert io.rename_window("%20", "overseer") is False
    # the pin is never attempted once the rename itself failed
    assert len(fake.calls) == 1


def test_window_pane_titles_parses_and_fail_soft():
    io, fake = _io(stdout="overseer-daemon\nzsh\n\n")
    assert io.window_pane_titles("%20") == ["overseer-daemon", "zsh"]
    assert fake.calls[0]["argv"] == ["tmux", "list-panes", "-t", "%20", "-F", "#{pane_title}"]
    io2, _ = _io(returncode=1)
    assert io2.window_pane_titles("%20") == []


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
