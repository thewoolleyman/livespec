"""Tests for claude_sessions.py — the Claude session-registry → tmux PID join.

Run: ``uv run pytest .claude/skills/overseer/ -q``. The pure functions are driven
with a tmp registry dir + fake ``/proc`` readers (``starttime_of`` / ``ppid_of``),
so nothing touches real ``/proc`` or ``~/.claude``; the two real ``/proc`` readers
are checked against THIS test process (a safe, always-present PID).
"""

import json
import os
from pathlib import Path

import claude_sessions


def _write(directory, pid, *, name, cwd, proc_start, status="idle"):
    payload = {"pid": pid, "name": name, "cwd": cwd, "procStart": proc_start, "status": status}
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


def test_read_live_sessions_carries_the_status_field(tmp_path):
    _write(tmp_path, 100, name="alpha", cwd="/r/a", proc_start="111", status="busy")
    live = claude_sessions.read_live_sessions(tmp_path, starttime_of={100: "111"}.get)
    assert [(s.name, s.status) for s in live] == [("alpha", "busy")]


def test_read_live_sessions_missing_status_defaults_empty(tmp_path):
    # A registry file with no `status` key must not crash the read; status defaults to "".
    (tmp_path / "100.json").write_text(
        json.dumps({"pid": 100, "name": "alpha", "cwd": "/r/a", "procStart": "111"}),
        encoding="utf-8",
    )
    live = claude_sessions.read_live_sessions(tmp_path, starttime_of={100: "111"}.get)
    assert live[0].status == ""


def test_status_by_tmux_session_keys_status_by_tmux(tmp_path):
    _write(tmp_path, 100, name="alpha", cwd="/r/a", proc_start="111", status="busy")
    _write(tmp_path, 300, name="gamma", cwd="/r/c", proc_start="333", status="busy")  # not in tmux
    starttimes = {100: "111", 300: "333"}
    ppid = {100: 50, 50: 1, 300: 60, 60: 1}
    pane_pid_to_session = {50: "sA"}  # only 100's chain reaches a pane PID

    status = claude_sessions.status_by_tmux_session(
        tmp_path, pane_pid_to_session, ppid_of=ppid.get, starttime_of=starttimes.get
    )
    assert status == {"sA": "busy"}  # gamma omitted (not held in any tmux pane)


def test_names_by_tmux_session_collects_all_names_per_tmux(tmp_path):
    """R2/SF5: the identity gate needs the SET of all live Claude names in a tmux session, so
    a HELPER Claude sharing the session cannot shadow the track's own name (a last-wins single
    would). Two live sessions in one tmux → both names; an out-of-tmux session is omitted."""
    _write(tmp_path, 100, name="alpha", cwd="/r/a", proc_start="111")
    _write(tmp_path, 200, name="helper", cwd="/r/a", proc_start="222")  # a second Claude in sA
    _write(tmp_path, 300, name="gamma", cwd="/r/c", proc_start="333")  # not in tmux
    starttimes = {100: "111", 200: "222", 300: "333"}
    # both 100 and 200 walk up to pane pids that map to the SAME tmux session `sA`.
    ppid = {100: 50, 50: 1, 200: 51, 51: 1, 300: 60, 60: 1}
    pane_pid_to_session = {50: "sA", 51: "sA"}

    names = claude_sessions.names_by_tmux_session(
        tmp_path, pane_pid_to_session, ppid_of=ppid.get, starttime_of=starttimes.get
    )
    assert names == {"sA": {"alpha", "helper"}}  # BOTH names kept; gamma (out of tmux) omitted


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


# --------------------------------------------------------------------------- #
# The /proc readers' CORRUPT-INPUT arms, driven against a FAKE /proc tree.
#
# The readers above are checked against this live process, which can only ever
# produce well-formed input. A truncated `stat` line or a garbled `children`
# token is exactly what a pid dying mid-read yields, and the module's documented
# guarantee is that such a read degrades ONE reader to None/[] rather than
# raising. `/proc` is interpolated directly in these readers (it IS the host
# coupling the injected seams replace elsewhere), so the module-level `Path` is
# redirected at a tmp tree — no live process is read.
# --------------------------------------------------------------------------- #


def _fake_proc(tmp_path, monkeypatch):
    """Point the module's hardcoded ``/proc`` reads at a writable tmp tree."""
    root = tmp_path / "proc"
    root.mkdir(exist_ok=True)

    def _redirect(arg):
        text = str(arg)
        if text == "/proc":
            return root
        if text.startswith("/proc/"):
            return root / text[len("/proc/") :]
        return Path(text)

    monkeypatch.setattr(claude_sessions, "Path", _redirect)
    return root


def _write_stat(root, pid, text):
    (root / str(pid)).mkdir(parents=True, exist_ok=True)
    (root / str(pid) / "stat").write_text(text, encoding="utf-8")


def test_proc_readers_are_none_when_the_stat_line_has_no_comm_parens(tmp_path, monkeypatch):
    # `stat` is split AFTER the LAST `)` (comm may itself contain spaces and parens).
    # A line carrying no `)` at all — a truncated read of a vanishing pid — must yield
    # None from both readers rather than a mis-split field.
    root = _fake_proc(tmp_path, monkeypatch)
    _write_stat(root, 100, "100 truncated-with-no-parens 12345")
    assert claude_sessions.proc_ppid(100) is None
    assert claude_sessions.proc_starttime(100) is None


def test_proc_ppid_is_none_when_the_ppid_field_is_not_a_number(tmp_path, monkeypatch):
    # A garbled ppid degrades that ONE reader to None; the SAME line's start-time
    # (field 22) is still read, so one corrupt field never blinds the liveness check.
    root = _fake_proc(tmp_path, monkeypatch)
    fields = ["S", "not-a-pid"] + ["0"] * 17 + ["99887766"]
    _write_stat(root, 100, "100 (cla ude) " + " ".join(fields))
    assert claude_sessions.proc_ppid(100) is None
    assert claude_sessions.proc_starttime(100) == "99887766"


def test_proc_children_skips_a_non_numeric_token(tmp_path, monkeypatch):
    # The children file is whitespace-separated pids; a garbled token is dropped and
    # the readable pids still come back — fail-soft per TOKEN, not per file.
    root = _fake_proc(tmp_path, monkeypatch)
    children = root / "100" / "task" / "100"
    children.mkdir(parents=True)
    (children / "children").write_text("200 not-a-pid 300\n", encoding="utf-8")
    assert claude_sessions.proc_children(100) == [200, 300]


def test_read_live_sessions_is_fail_soft_when_the_registry_dir_cannot_be_listed(
    tmp_path, monkeypatch
):
    # An unlistable registry dir (an EIO/ESTALE directory scan) yields NO sessions
    # instead of propagating — one bad reader must never crash a daemon tick. Stubbed
    # rather than chmod'ed because `Path.glob` swallows the ordinary EACCES case itself.
    class _UnlistableDir:
        def glob(self, _pattern):
            raise OSError(5, "Input/output error")

    monkeypatch.setattr(claude_sessions, "Path", lambda _path: _UnlistableDir())
    assert claude_sessions.read_live_sessions(tmp_path, starttime_of=lambda _pid: "111") == []


def test_read_live_sessions_skips_records_with_wrongly_typed_fields(tmp_path):
    # pid/name/cwd of the wrong TYPE are skipped, never coerced: a corrupt registry
    # file degrades to "that one session is invisible", and the good ones still read.
    (tmp_path / "1.json").write_text(
        json.dumps({"pid": "100", "name": "alpha", "cwd": "/r/a", "procStart": "444"}),
        encoding="utf-8",
    )
    (tmp_path / "2.json").write_text(
        json.dumps({"pid": 200, "name": ["beta"], "cwd": "/r/b", "procStart": "444"}),
        encoding="utf-8",
    )
    (tmp_path / "3.json").write_text(
        json.dumps({"pid": 300, "name": "gamma", "cwd": 7, "procStart": "444"}),
        encoding="utf-8",
    )
    _write(tmp_path, 400, name="delta", cwd="/r/d", proc_start="444")

    live = claude_sessions.read_live_sessions(tmp_path, starttime_of=lambda _pid: "444")
    assert [(s.pid, s.name) for s in live] == [(400, "delta")]


def test_resolve_tmux_session_gives_up_after_the_bounded_parent_walk():
    # The walk is BOUNDED, not merely cycle-guarded: an unbroken ancestor chain (every
    # pid distinct, so the visited-set never fires) whose pane PID sits beyond the bound
    # returns None rather than climbing forever.
    got = claude_sessions.resolve_tmux_session(
        100, pane_pid_to_session={1000: "far-away"}, ppid_of=lambda pid: pid + 1
    )
    assert got is None
