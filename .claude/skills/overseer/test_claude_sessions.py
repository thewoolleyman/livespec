"""Tests for claude_sessions.py — the Claude session-registry → tmux PID join.

Run: ``uv run pytest .claude/skills/overseer/ -q``. The pure functions are driven
with a tmp registry dir + fake ``/proc`` readers (``starttime_of`` / ``ppid_of``),
so nothing touches real ``/proc`` or ``~/.claude``; the two real ``/proc`` readers
are checked against THIS test process (a safe, always-present PID).
"""

import json
import os

import claude_sessions


def _write(directory, pid, *, name, cwd, proc_start):
    payload = {"pid": pid, "name": name, "cwd": cwd, "procStart": proc_start, "status": "idle"}
    (directory / f"{pid}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_read_live_sessions_keeps_live_named_drops_stale(tmp_path):
    _write(tmp_path, 100, name="alpha", cwd="/r/a", proc_start="111")  # live (starttime matches)
    _write(tmp_path, 200, name="beta", cwd="/r/b", proc_start="222")  # dead (starttime None)
    _write(tmp_path, 300, name="gamma", cwd="/r/c", proc_start="333")  # PID reused (mismatch)
    _write(tmp_path, 400, name="", cwd="/r/d", proc_start="444")  # no name → skip
    starttimes = {100: "111", 300: "999"}  # 100 matches; 300 mismatches; 200/400 absent

    live = claude_sessions.read_live_sessions(tmp_path, starttime_of=starttimes.get)
    assert [(s.pid, s.name, s.cwd) for s in live] == [(100, "alpha", "/r/a")]


def test_read_live_sessions_skips_malformed_files(tmp_path):
    (tmp_path / "bad.json").write_text("{not json", encoding="utf-8")
    _write(tmp_path, 100, name="alpha", cwd="/r/a", proc_start="111")
    live = claude_sessions.read_live_sessions(tmp_path, starttime_of=lambda _pid: "111")
    assert [s.name for s in live] == ["alpha"]


def test_read_live_sessions_missing_dir_is_empty(tmp_path):
    got = claude_sessions.read_live_sessions(tmp_path / "nope", starttime_of=lambda _pid: "x")
    assert got == []


def test_resolve_tmux_session_walks_parent_chain():
    # claude 100 → shell 50 (a pane PID of session "s") → init.
    ppid = {100: 50, 50: 1}
    got = claude_sessions.resolve_tmux_session(100, pane_pid_to_session={50: "s"}, ppid_of=ppid.get)
    assert got == "s"


def test_resolve_tmux_session_pid_is_the_pane_itself():
    got = claude_sessions.resolve_tmux_session(
        50, pane_pid_to_session={50: "s"}, ppid_of=lambda _pid: None
    )
    assert got == "s"


def test_resolve_tmux_session_none_when_not_in_tmux():
    ppid = {100: 50, 50: 1, 1: 0}
    got = claude_sessions.resolve_tmux_session(
        100, pane_pid_to_session={999: "other"}, ppid_of=ppid.get
    )
    assert got is None


def test_resolve_tmux_session_cycle_is_fail_soft():
    ppid = {100: 200, 200: 100}  # a cycle, and neither is a pane PID
    got = claude_sessions.resolve_tmux_session(100, pane_pid_to_session={}, ppid_of=ppid.get)
    assert got is None


def test_map_named_sessions_joins_only_live_in_tmux(tmp_path):
    _write(tmp_path, 100, name="alpha", cwd="/r/a", proc_start="111")  # live, in tmux sA
    _write(tmp_path, 300, name="gamma", cwd="/r/c", proc_start="333")  # live, NOT in tmux
    _write(tmp_path, 400, name="delta", cwd="/r/d", proc_start="444")  # dead
    starttimes = {100: "111", 300: "333"}  # 400 absent → dead
    ppid = {100: 50, 50: 1, 300: 60, 60: 1}
    pane_pid_to_session = {50: "sA"}  # only 100's chain reaches a pane PID

    mapped = claude_sessions.map_named_sessions(
        tmp_path, pane_pid_to_session, ppid_of=ppid.get, starttime_of=starttimes.get
    )
    assert mapped == [("sA", "alpha", "/r/a")]


def test_proc_readers_on_this_process():
    # The real /proc readers, exercised against THIS process (safe, always present).
    assert claude_sessions.proc_ppid(os.getpid()) == os.getppid()
    assert claude_sessions.proc_starttime(os.getpid()) is not None
    # A PID that cannot exist → fail-soft None (never raises).
    assert claude_sessions.proc_ppid(2**30) is None
    assert claude_sessions.proc_starttime(2**30) is None


# --------------------------------------------------------------------------- #
# has_active_subshell: a DESCENDANT shell ⇒ active background work ⇒ not idle.
# --------------------------------------------------------------------------- #


def _tree(children, comms):
    """A pair of fake /proc readers over a static process tree."""
    return (lambda pid: children.get(pid, [])), comms.get


def test_has_active_subshell_true_when_direct_child_is_shell():
    # root 100 → node runtime (200) + a background-command shell (300, zsh).
    children_of, comm_of = _tree({100: [200, 300]}, {200: "node", 300: "zsh"})
    assert (
        claude_sessions.has_active_subshell(100, children_of=children_of, comm_of=comm_of) is True
    )


def test_has_active_subshell_false_when_descendants_are_only_non_shells():
    # root 100 → node runtime (200) → an MCP server (300, node). No shell anywhere.
    children_of, comm_of = _tree({100: [200], 200: [300]}, {200: "node", 300: "node"})
    assert (
        claude_sessions.has_active_subshell(100, children_of=children_of, comm_of=comm_of) is False
    )


def test_has_active_subshell_true_for_deep_shell():
    # A shell nested two levels down: 100 → 200 (node) → 300 (bash).
    children_of, comm_of = _tree({100: [200], 200: [300]}, {200: "node", 300: "bash"})
    assert (
        claude_sessions.has_active_subshell(100, children_of=children_of, comm_of=comm_of) is True
    )


def test_has_active_subshell_false_when_no_children():
    assert (
        claude_sessions.has_active_subshell(
            100, children_of=lambda _pid: [], comm_of=lambda _pid: None
        )
        is False
    )


def test_has_active_subshell_root_itself_is_not_counted():
    # root_pid (the login shell) is itself a shell but has NO descendants → False:
    # only DESCENDANTS count, never root itself.
    children_of, comm_of = _tree({}, {100: "zsh"})
    assert (
        claude_sessions.has_active_subshell(100, children_of=children_of, comm_of=comm_of) is False
    )


def test_has_active_subshell_cycle_is_fail_soft():
    # A cycle among non-shells must TERMINATE (visited-set) and return False, no hang.
    children_of, comm_of = _tree({100: [200], 200: [100]}, {100: "node", 200: "node"})
    assert (
        claude_sessions.has_active_subshell(100, children_of=children_of, comm_of=comm_of) is False
    )


def test_proc_comm_and_children_on_this_process():
    # The real /proc readers, exercised against THIS process (safe, always present).
    comm = claude_sessions.proc_comm(os.getpid())
    assert comm is not None and comm != ""
    children = claude_sessions.proc_children(os.getpid())
    assert isinstance(children, list)
    assert all(isinstance(pid, int) for pid in children)
    # A PID that cannot exist → fail-soft (None / []), never raises.
    assert claude_sessions.proc_comm(2**30) is None
    assert claude_sessions.proc_children(2**30) == []
