"""Beside-tests for `codex_sessions` — the Codex twin of `claude_sessions`.

Every /proc + filesystem coupling is injected, so these run with no codex process and
no real `~/.codex`.
"""

from __future__ import annotations

from pathlib import Path

import codex_sessions

# --------------------------------------------------------------------------- #
# Helpers: a fake host (pids, comms, cwds, open fds) + a fake ~/.codex.
# --------------------------------------------------------------------------- #


def _index(tmp_path, records):
    """Write a `session_index.jsonl` with `records` (id, thread_name) pairs, in order."""
    home = tmp_path / "codex"
    home.mkdir(exist_ok=True)
    lines = [
        f'{{"id": "{i}", "thread_name": "{n}", "updated_at": "2026-07-16T08:00:00Z"}}'
        for i, n in records
    ]
    (home / "session_index.jsonl").write_text("\n".join(lines) + "\n")
    return home


def _rollout(session_id):
    """A rollout path of the real shape — the id is embedded in the FILENAME."""
    return f"/home/u/.codex/sessions/2026/07/16/rollout-2026-07-16T10-49-49-{session_id}.jsonl"


_ID_A = "019f6a1e-266d-7fc2-8eb2-15ec9d324fb8"
_ID_B = "019f548d-6071-7893-9c2e-472cce81da02"


def _host(*, comms=None, cwds=None, fds=None):
    """Injected host readers: pid→comm, pid→cwd, pid→open fd targets."""
    comms, cwds, fds = comms or {}, cwds or {}, fds or {}
    return {
        "pids_of_comm": lambda comm: sorted(p for p, c in comms.items() if c == comm),
        "cwd_of": cwds.get,
        "fd_targets_of": lambda pid: fds.get(pid, []),
    }


# --------------------------------------------------------------------------- #
# The join: pid -> open rollout fd -> session id -> thread_name (= the topic).
# --------------------------------------------------------------------------- #


def test_live_codex_session_joins_pid_to_its_thread_name_and_cwd(tmp_path):
    """The whole point: a running codex process HOLDS ITS ROLLOUT FILE OPEN, and the
    rollout filename embeds the session id, which the index maps to the thread_name —
    the plan topic. Verified live 2026-07-16 against a real 2-day-old codex TUI."""
    home = _index(tmp_path, [(_ID_A, "rop-sweep-consumer-cleanup")])
    host = _host(
        comms={4242: "codex"},
        cwds={4242: "/data/projects/livespec"},
        fds={4242: ["/dev/null", _rollout(_ID_A), "/some/other/file"]},
    )
    out = codex_sessions.read_live_codex_sessions(codex_home=home, **host)
    assert len(out) == 1
    assert out[0].pid == 4242
    assert out[0].name == "rop-sweep-consumer-cleanup"  # == the plan topic
    assert out[0].cwd == "/data/projects/livespec"
    assert out[0].session_id == _ID_A


def test_non_codex_processes_are_ignored(tmp_path):
    """Only `comm == codex`. The `bun` wrapper is the codex binary's PARENT (verified
    live: pid 1681795 `bun` -> pid 1682090 `codex`) and must not be mistaken for it."""
    home = _index(tmp_path, [(_ID_A, "some-topic")])
    host = _host(
        comms={1: "bun", 2: "node", 3: "zsh"},
        cwds={1: "/data/projects/livespec", 2: "/x", 3: "/y"},
        fds={1: [_rollout(_ID_A)]},  # even if it somehow held one
    )
    assert codex_sessions.read_live_codex_sessions(codex_home=home, **host) == []


def test_codex_process_holding_no_rollout_is_skipped(tmp_path):
    """No open rollout ⇒ no session id ⇒ no join. This is also what excludes the `bun`
    wrapper structurally: verified live, it holds ZERO rollout fds while its codex child
    holds exactly one."""
    home = _index(tmp_path, [(_ID_A, "some-topic")])
    host = _host(comms={7: "codex"}, cwds={7: "/data/projects/livespec"}, fds={7: ["/dev/null"]})
    assert codex_sessions.read_live_codex_sessions(codex_home=home, **host) == []


def test_unnamed_session_is_skipped(tmp_path):
    """THE real constraint (not a heuristic problem): only NAMED sessions are indexed —
    just 67 of 259 rollouts, live 2026-07-16. An unnamed session carries no topic
    ANYWHERE, so it cannot be joined to a plan and is correctly dropped. Codex adoption
    depends on a naming convention exactly as Claude's does via `claude -n <topic>`."""
    home = _index(tmp_path, [(_ID_A, "named-topic")])
    host = _host(
        comms={9: "codex"},
        cwds={9: "/data/projects/livespec"},
        fds={9: [_rollout(_ID_B)]},  # live, but its id is NOT in the index
    )
    assert codex_sessions.read_live_codex_sessions(codex_home=home, **host) == []


def test_companion_task_threads_are_returned_not_filtered_here(tmp_path):
    """`Codex Companion Task: …` threads (38 of 69 index records, live) are the codex
    plugin's own sub-agent runs, NOT plan topics. They are deliberately NOT filtered in
    this module: they simply fail the "is this an ACTIVE plan topic?" check at adoption,
    so the noise filters itself and this module stays a pure, dumb join."""
    home = _index(tmp_path, [(_ID_A, "Codex Companion Task: do a thing")])
    host = _host(
        comms={5: "codex"}, cwds={5: "/data/projects/livespec"}, fds={5: [_rollout(_ID_A)]}
    )
    out = codex_sessions.read_live_codex_sessions(codex_home=home, **host)
    assert [s.name for s in out] == ["Codex Companion Task: do a thing"]


def test_a_process_with_no_readable_cwd_is_skipped(tmp_path):
    """Fail-soft: a pid that vanished between enumeration and the cwd read is dropped,
    never raised."""
    home = _index(tmp_path, [(_ID_A, "topic")])
    host = _host(comms={5: "codex"}, cwds={}, fds={5: [_rollout(_ID_A)]})
    assert codex_sessions.read_live_codex_sessions(codex_home=home, **host) == []


def test_multiple_live_sessions_all_join(tmp_path):
    home = _index(tmp_path, [(_ID_A, "topic-a"), (_ID_B, "topic-b")])
    host = _host(
        comms={11: "codex", 12: "codex"},
        cwds={11: "/data/projects/livespec", 12: "/data/projects/other"},
        fds={11: [_rollout(_ID_A)], 12: [_rollout(_ID_B)]},
    )
    out = codex_sessions.read_live_codex_sessions(codex_home=home, **host)
    assert {(s.pid, s.name, s.cwd) for s in out} == {
        (11, "topic-a", "/data/projects/livespec"),
        (12, "topic-b", "/data/projects/other"),
    }


# --------------------------------------------------------------------------- #
# The index reader.
# --------------------------------------------------------------------------- #


def test_index_last_record_wins_for_a_repeated_id(tmp_path):
    """`session_index.jsonl` is an APPEND log — a renamed thread appends a new record for
    the same id, so the LAST one is current."""
    home = _index(tmp_path, [(_ID_A, "old-name"), (_ID_A, "new-name")])
    assert codex_sessions.read_thread_names(home)[_ID_A] == "new-name"


def test_index_skips_malformed_lines_and_never_raises(tmp_path):
    home = tmp_path / "codex"
    home.mkdir()
    (home / "session_index.jsonl").write_text(
        "not json at all\n"
        f'{{"id": "{_ID_A}", "thread_name": "good"}}\n'
        "\n"
        '{"id": 17, "thread_name": "id-not-a-string"}\n'
        '{"thread_name": "no-id"}\n'
        '{"id": "x", "thread_name": ""}\n'
    )
    assert codex_sessions.read_thread_names(home) == {_ID_A: "good"}


def test_missing_index_is_empty_not_an_error(tmp_path):
    assert codex_sessions.read_thread_names(tmp_path / "nonexistent") == {}


# --------------------------------------------------------------------------- #
# latest_session_for_thread_name + rollout_exists — the reboot-recovery reverse
# lookup (defect #5). The index SURVIVES a session's death, so a dead codex track's
# session id is recoverable from its plan topic; the rollout's on-disk presence gates
# whether `codex resume` can reattach (option c) or recovery must skip+surface (b).
# --------------------------------------------------------------------------- #


def _index_ts(tmp_path, records):
    """Write a `session_index.jsonl` from (id, thread_name, updated_at) TRIPLES, in order."""
    home = tmp_path / "codex"
    home.mkdir(exist_ok=True)
    lines = [f'{{"id": "{i}", "thread_name": "{n}", "updated_at": "{ts}"}}' for i, n, ts in records]
    (home / "session_index.jsonl").write_text("\n".join(lines) + "\n")
    return home


def _write_rollout(home, session_id, *, ymd="2026/06/22", ts="2026-06-22T18-35-28"):
    """Create a real-shape rollout file for `session_id` under `<home>/sessions/YYYY/MM/DD/`."""
    day = home / "sessions" / ymd
    day.mkdir(parents=True, exist_ok=True)
    path = day / f"rollout-{ts}-{session_id}.jsonl"
    path.write_text("{}\n")  # body is never read; presence is all that matters
    return path


def test_latest_session_for_thread_name_picks_the_newest_by_updated_at(tmp_path):
    """Two indexed sessions share a topic (the plan was driven by codex more than once);
    recovery resumes the MOST-RECENT by `updated_at` — distinct per id in real data."""
    home = _index_ts(
        tmp_path,
        [
            (_ID_A, "cloud-local-memory-cleanup", "2026-07-13T10:00:00Z"),
            (_ID_B, "cloud-local-memory-cleanup", "2026-07-13T20:17:42Z"),
        ],
    )
    assert (
        codex_sessions.latest_session_for_thread_name("cloud-local-memory-cleanup", codex_home=home)
        == _ID_B
    )


def test_latest_session_for_thread_name_is_none_for_an_unknown_topic(tmp_path):
    """A topic named nowhere in the index is a CLAUDE track — the caller must NOT resume it
    as codex. None is the signal to fall through to the Claude recovery path."""
    home = _index_ts(tmp_path, [(_ID_A, "some-codex-topic", "2026-07-13T10:00:00Z")])
    assert codex_sessions.latest_session_for_thread_name("a-claude-topic", codex_home=home) is None


def test_latest_session_for_thread_name_honours_a_rename(tmp_path):
    """The index is an APPEND log: an id renamed AWAY from the topic (its LAST record names
    something else) no longer matches, and an id renamed TO the topic does — last record wins,
    shared with `read_thread_names` via `_read_index_final`."""
    home = _index_ts(
        tmp_path,
        [
            (_ID_A, "the-topic", "2026-07-13T09:00:00Z"),  # A started as the topic...
            (_ID_A, "renamed-away", "2026-07-13T09:30:00Z"),  # ...then was renamed away
            (_ID_B, "was-other", "2026-07-13T10:00:00Z"),  # B started as something else...
            (_ID_B, "the-topic", "2026-07-13T10:30:00Z"),  # ...then was renamed TO the topic
        ],
    )
    assert codex_sessions.latest_session_for_thread_name("the-topic", codex_home=home) == _ID_B


def test_latest_session_for_thread_name_missing_index_is_none(tmp_path):
    assert codex_sessions.latest_session_for_thread_name("t", codex_home=tmp_path / "nope") is None


def test_rollout_exists_finds_a_nested_rollout(tmp_path):
    home = tmp_path / "codex"
    home.mkdir()
    _write_rollout(home, _ID_A)
    assert codex_sessions.rollout_exists(_ID_A, codex_home=home) is True


def test_rollout_exists_is_false_when_the_rollout_is_gone(tmp_path):
    """Option (b): the index still names the session, but its rollout was pruned — codex
    resume cannot reattach, so recovery must skip+surface rather than resume."""
    home = tmp_path / "codex"
    home.mkdir()
    _write_rollout(home, _ID_A)  # a DIFFERENT session's rollout is present
    assert codex_sessions.rollout_exists(_ID_B, codex_home=home) is False


def test_rollout_exists_is_false_when_the_sessions_dir_is_absent(tmp_path):
    home = tmp_path / "codex"
    home.mkdir()  # no sessions/ subtree at all
    assert codex_sessions.rollout_exists(_ID_A, codex_home=home) is False


# --------------------------------------------------------------------------- #
# The rollout-id parse (filename ONLY — never the body; see the secrets caution).
# --------------------------------------------------------------------------- #


def test_rollout_id_is_read_from_the_filename(tmp_path):
    assert codex_sessions.rollout_id(_rollout(_ID_A)) == _ID_A


def test_non_rollout_paths_yield_no_id():
    for path in (
        "/dev/null",
        "/home/u/.codex/logs_2.sqlite",
        "/home/u/.codex/sessions/2026/07/16/notes.txt",
        "/home/u/.codex/sessions/rollout-no-uuid-here.jsonl",
        "",
    ):
        assert codex_sessions.rollout_id(path) is None


def test_open_rollout_id_picks_the_rollout_out_of_unrelated_fds():
    fds = ["/dev/urandom", "/home/u/.codex/logs_2.sqlite-wal", _rollout(_ID_B), "socket:[1]"]
    assert codex_sessions.open_rollout_id(1, fd_targets_of=lambda _p: fds) == _ID_B


def test_open_rollout_id_is_none_when_no_rollout_is_held():
    assert codex_sessions.open_rollout_id(1, fd_targets_of=lambda _p: ["/dev/null"]) is None


# --------------------------------------------------------------------------- #
# map_codex_sessions — the twin of claude_sessions.map_named_sessions, emitting the
# SAME (tmux_session, name, cwd) triple so `adopt` can consume either runtime through
# one code path instead of growing a parallel Codex branch.
# --------------------------------------------------------------------------- #


def test_map_codex_sessions_emits_the_same_triple_as_the_claude_twin(tmp_path):
    home = _index(tmp_path, [(_ID_A, "topic-a")])
    host = _host(
        comms={4242: "codex"},
        cwds={4242: "/data/projects/livespec"},
        fds={4242: [_rollout(_ID_A)]},
    )
    mapped = codex_sessions.map_codex_sessions(
        codex_home=home,
        pane_pid_to_session={9000: "livespec3"},
        ppid_of={4242: 9000}.get,  # the codex pid's parent IS the pane pid
        **host,
    )
    assert mapped == [("livespec3", "topic-a", "/data/projects/livespec")]


def test_map_codex_sessions_omits_a_session_not_inside_tmux(tmp_path):
    """Mirrors the Claude twin: a codex session running outside tmux (a bare SSH shell)
    has no pane to drive, so it is omitted rather than mapped to nothing."""
    home = _index(tmp_path, [(_ID_A, "topic-a")])
    host = _host(
        comms={4242: "codex"}, cwds={4242: "/data/projects/livespec"}, fds={4242: [_rollout(_ID_A)]}
    )
    mapped = codex_sessions.map_codex_sessions(
        codex_home=home,
        pane_pid_to_session={},  # no tmux panes at all
        ppid_of=lambda _p: None,
        **host,
    )
    assert mapped == []


def test_map_codex_sessions_is_deterministic_across_sessions(tmp_path):
    home = _index(tmp_path, [(_ID_A, "topic-a"), (_ID_B, "topic-b")])
    host = _host(
        comms={20: "codex", 10: "codex"},
        cwds={10: "/data/projects/one", 20: "/data/projects/two"},
        fds={10: [_rollout(_ID_A)], 20: [_rollout(_ID_B)]},
    )
    mapped = codex_sessions.map_codex_sessions(
        codex_home=home,
        pane_pid_to_session={101: "s-one", 202: "s-two"},
        ppid_of={10: 101, 20: 202}.get,
        **host,
    )
    assert mapped == [  # pid order, like the Claude twin's sorted-registry order
        ("s-one", "topic-a", "/data/projects/one"),
        ("s-two", "topic-b", "/data/projects/two"),
    ]


# --------------------------------------------------------------------------- #
# codex_by_tmux_session — the twin of claude_sessions.status_by_tmux_session, and the
# LAST primitive the supervisor wiring needs. It is what lets a Codex track be
# identified EXACTLY rather than by pane-command string-matching: tmux reports a codex
# pane's command as `bun` (the launcher; the vendored codex binary is its child), and
# `bun` is generic — any bun app would match. Keying identity off a live session map
# instead is exact, self-correcting, and needs no stored `runtime` field.
# --------------------------------------------------------------------------- #


def test_codex_by_tmux_session_keys_live_sessions_by_tmux_session_and_name(tmp_path):
    home = _index(tmp_path, [(_ID_A, "topic-a"), (_ID_B, "topic-b")])
    host = _host(
        comms={10: "codex", 20: "codex"},
        cwds={10: "/data/projects/one", 20: "/data/projects/two"},
        fds={10: [_rollout(_ID_A)], 20: [_rollout(_ID_B)]},
    )
    by = codex_sessions.codex_by_tmux_session(
        {101: "s-one", 202: "s-two"}, codex_home=home, ppid_of={10: 101, 20: 202}.get, **host
    )
    assert set(by) == {("s-one", "topic-a"), ("s-two", "topic-b")}
    assert by[("s-one", "topic-a")].pid == 10
    assert by[("s-two", "topic-b")].pid == 20


def test_codex_by_tmux_session_keeps_both_when_two_share_one_tmux_session(tmp_path):
    """#4: two codex sessions in ONE tmux session, each named for its own plan topic, must
    BOTH survive — keyed by (tmux, name) so neither shadows the other. A single value per
    tmux session would drop the second, silently losing its ctx reading, wrap-up, and
    restart (invisible in the table). The codex analogue of the set-valued
    `names_by_tmux_session` (R2 SF5)."""
    home = _index(tmp_path, [(_ID_A, "topic-a"), (_ID_B, "topic-b")])
    host = _host(
        comms={10: "codex", 20: "codex"},
        cwds={10: "/data/projects/one", 20: "/data/projects/one"},
        fds={10: [_rollout(_ID_A)], 20: [_rollout(_ID_B)]},
    )
    # Both codex pids resolve (via their pane pids) to the SAME tmux session "shared".
    by = codex_sessions.codex_by_tmux_session(
        {101: "shared", 202: "shared"}, codex_home=home, ppid_of={10: 101, 20: 202}.get, **host
    )
    assert set(by) == {("shared", "topic-a"), ("shared", "topic-b")}
    assert by[("shared", "topic-a")].pid == 10
    assert by[("shared", "topic-a")].session_id == _ID_A
    assert by[("shared", "topic-b")].pid == 20
    assert by[("shared", "topic-b")].session_id == _ID_B


def test_codex_by_tmux_session_is_empty_with_no_codex_running(tmp_path):
    """The overwhelmingly common case — a fleet of Claude sessions and no codex at all.
    Must be an empty map, never an error, so `evaluate` can key off it unconditionally."""
    home = _index(tmp_path, [])
    by = codex_sessions.codex_by_tmux_session({}, codex_home=home, **_host())
    assert by == {}


def test_codex_by_tmux_session_omits_sessions_outside_tmux(tmp_path):
    home = _index(tmp_path, [(_ID_A, "topic-a")])
    host = _host(comms={10: "codex"}, cwds={10: "/x"}, fds={10: [_rollout(_ID_A)]})
    by = codex_sessions.codex_by_tmux_session({}, codex_home=home, ppid_of=lambda _p: None, **host)
    assert by == {}


def test_codex_by_tmux_session_keeps_the_first_on_a_same_tmux_same_name_collision(tmp_path):
    """Only a GENUINE collision — two codex processes for the SAME topic in the SAME tmux
    session — drops one, and the drop is deterministic: the first by pid order wins, so a
    stray duplicate can never flap the supervisor's view of that track between ticks."""
    home = _index(tmp_path, [(_ID_A, "topic-a"), (_ID_B, "topic-a")])  # SAME thread_name
    host = _host(
        comms={10: "codex", 20: "codex"},
        cwds={10: "/data/projects/one", 20: "/data/projects/one"},
        fds={10: [_rollout(_ID_A)], 20: [_rollout(_ID_B)]},
    )
    by = codex_sessions.codex_by_tmux_session(
        {101: "shared", 202: "shared"}, codex_home=home, ppid_of={10: 101, 20: 202}.get, **host
    )
    assert set(by) == {("shared", "topic-a")}
    assert by[("shared", "topic-a")].pid == 10  # the FIRST by pid order, not the last
    assert by[("shared", "topic-a")].session_id == _ID_A


def test_rollout_exists_is_false_when_the_sessions_tree_cannot_be_walked(monkeypatch):
    """Fail-soft to False: an unwalkable sessions tree must read as "no rollout" — recovery
    then falls back to skip+surface (option b) instead of raising mid-tick. Stubbed rather
    than chmod'ed because `Path.rglob` swallows the ordinary EACCES case itself."""

    class _UnwalkableTree:
        def __truediv__(self, _other):
            return self

        def rglob(self, _pattern):
            raise OSError(5, "Input/output error")

    monkeypatch.setattr(codex_sessions, "Path", lambda _path: _UnwalkableTree())
    assert codex_sessions.rollout_exists(_ID_A, codex_home="/somewhere") is False


# --------------------------------------------------------------------------- #
# The REAL /proc readers + the real `~/.codex` default. These are the host
# couplings every test above injects around, so nothing else in the suite runs
# them. They are driven here against a FAKE /proc tree (real dirs + real
# symlinks under tmp_path) with the module's hardcoded `/proc` prefix redirected
# at it, and against a HOME pointed at tmp_path — no live process, no real
# `~/.codex`.
# --------------------------------------------------------------------------- #


def _fake_proc(tmp_path, monkeypatch, *, present=True):
    """Point the module's hardcoded ``/proc`` reads at a tmp tree (absent if not ``present``)."""
    root = tmp_path / "proc"
    if present:
        root.mkdir(exist_ok=True)

    def _redirect(arg):
        text = str(arg)
        if text == "/proc":
            return root
        if text.startswith("/proc/"):
            return root / text[len("/proc/") :]
        return Path(text)

    monkeypatch.setattr(codex_sessions, "Path", _redirect)
    return root


def test_default_codex_home_is_dot_codex_under_the_users_home(tmp_path, monkeypatch):
    """The default that the injectable `codex_home` seam overrides everywhere else."""
    monkeypatch.setenv("HOME", str(tmp_path))
    assert codex_sessions.default_codex_home() == tmp_path / ".codex"


def test_proc_fd_targets_reads_the_open_fd_symlinks(tmp_path, monkeypatch):
    """The fd table IS the pid→session link: a real codex process holds its rollout open,
    so reading the fd targets and running the join over them recovers the session id."""
    root = _fake_proc(tmp_path, monkeypatch)
    fds = root / "4242" / "fd"
    fds.mkdir(parents=True)
    (fds / "0").symlink_to("/dev/null")
    (fds / "3").symlink_to(_rollout(_ID_A))

    assert sorted(codex_sessions.proc_fd_targets(4242)) == ["/dev/null", _rollout(_ID_A)]
    joined = codex_sessions.open_rollout_id(4242, fd_targets_of=codex_sessions.proc_fd_targets)
    assert joined == _ID_A


def test_proc_fd_targets_skips_an_entry_that_cannot_be_readlinked(tmp_path, monkeypatch):
    """An fd that closed underneath the scan (here: an entry that is not a symlink at all)
    is skipped per-ENTRY — the surviving fds still come back, so one racing close never
    blanks the whole fd read."""
    root = _fake_proc(tmp_path, monkeypatch)
    fds = root / "7" / "fd"
    fds.mkdir(parents=True)
    (fds / "0").symlink_to("/dev/null")
    (fds / "1").write_text("", encoding="utf-8")  # not a symlink → EINVAL on readlink
    assert codex_sessions.proc_fd_targets(7) == ["/dev/null"]


def test_proc_fd_targets_is_empty_for_a_pid_that_is_gone(tmp_path, monkeypatch):
    _fake_proc(tmp_path, monkeypatch)
    assert codex_sessions.proc_fd_targets(999999) == []


def test_proc_cwd_reads_the_cwd_symlink_and_is_none_when_the_pid_is_gone(tmp_path, monkeypatch):
    root = _fake_proc(tmp_path, monkeypatch)
    (root / "4242").mkdir()
    (root / "4242" / "cwd").symlink_to("/data/projects/livespec")
    assert codex_sessions.proc_cwd(4242) == "/data/projects/livespec"
    assert codex_sessions.proc_cwd(999999) is None


def test_proc_pids_of_comm_scans_proc_for_matching_processes(tmp_path, monkeypatch):
    """The scan keeps only NUMERIC `/proc` entries (so `self` / `cpuinfo` are skipped),
    keeps only pids whose comm matches exactly, and returns them sorted."""
    root = _fake_proc(tmp_path, monkeypatch)
    for name in ("20", "10", "30", "self", "cpuinfo"):
        (root / name).mkdir()
    monkeypatch.setattr(codex_sessions, "proc_comm", {10: "codex", 20: "bun", 30: "codex"}.get)

    assert codex_sessions.proc_pids_of_comm("codex") == [10, 30]
    assert codex_sessions.proc_pids_of_comm("bun") == [20]  # the launcher is NOT codex
    assert codex_sessions.proc_pids_of_comm("node") == []


def test_proc_pids_of_comm_is_empty_when_proc_cannot_be_scanned(tmp_path, monkeypatch):
    """Fail-soft to []: no scannable `/proc` means "no codex running", never a raise."""
    _fake_proc(tmp_path, monkeypatch, present=False)
    assert codex_sessions.proc_pids_of_comm("codex") == []
