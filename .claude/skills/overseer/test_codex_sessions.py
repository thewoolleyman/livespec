"""Beside-tests for `codex_sessions` — the Codex twin of `claude_sessions`.

Every /proc + filesystem coupling is injected, so these run with no codex process and
no real `~/.codex`.
"""

from __future__ import annotations

import codex_sessions

# --------------------------------------------------------------------------- #
# Helpers: a fake host (pids, comms, cwds, open fds) + a fake ~/.codex.
# --------------------------------------------------------------------------- #


def _index(tmp_path, records):
    """Write a `session_index.jsonl` with `records` (id, thread_name) pairs, in order."""
    home = tmp_path / "codex"
    home.mkdir(exist_ok=True)
    lines = [
        '{"id": "%s", "thread_name": "%s", "updated_at": "2026-07-16T08:00:00Z"}' % (i, n)
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
        '{"id": "%s", "thread_name": "good"}\n'
        "\n"
        '{"id": 17, "thread_name": "id-not-a-string"}\n'
        '{"thread_name": "no-id"}\n'
        '{"id": "x", "thread_name": ""}\n' % _ID_A
    )
    assert codex_sessions.read_thread_names(home) == {_ID_A: "good"}


def test_missing_index_is_empty_not_an_error(tmp_path):
    assert codex_sessions.read_thread_names(tmp_path / "nonexistent") == {}


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
# Ctx% from the rollout's `token_count` events.
#
# The BUILD-READY design recorded Ctx% as unavailable for Codex ("no `Ctx: N% left`
# statusline → parse_ctx_remaining returns unknown → no wrap-up"). The premise is true
# and the conclusion is wrong: ctx comes from the rollout, not the statusline. That
# matters because the escalating wrap-up is the daemon's ONLY lever now that nothing is
# force-killed — a wrap-up-less Codex track is a passenger that runs to exhaustion.
#
# This reads a number from a file rather than a regex over rendered terminal text, so it
# is strictly MORE reliable than the Claude path.
# --------------------------------------------------------------------------- #


def _token_count(total_tokens, window=258400):
    return (
        '{"timestamp": "2026-07-14T02:02:42.276Z", "type": "event_msg", "payload": '
        '{"type": "token_count", "info": {"total_token_usage": {"total_tokens": 104779470}, '
        '"last_token_usage": {"total_tokens": %d}, "model_context_window": %d}}}'
        % (total_tokens, window)
    )


def _write_rollout(tmp_path, lines, name="rollout-2026-07-16T10-49-49-%s.jsonl" % _ID_A):
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\n")
    return path


def test_ctx_remaining_from_the_last_token_count(tmp_path):
    """The real shape, with the real numbers observed live: 165818/258400 used → ~35% left."""
    path = _write_rollout(tmp_path, ['{"type": "session_meta"}', _token_count(165818)])
    assert codex_sessions.rollout_ctx_remaining(path) == 35


def test_ctx_uses_the_LAST_token_count_not_the_first(tmp_path):
    """Context occupancy changes every turn — only the newest record is current."""
    path = _write_rollout(
        tmp_path,
        [_token_count(25840), _token_count(129200), _token_count(232560)],  # 90% -> 50% -> 10%
    )
    assert codex_sessions.rollout_ctx_remaining(path) == 10


def test_ctx_ignores_total_token_usage(tmp_path):
    """`total_token_usage` is the session's CUMULATIVE spend (104M in the sampled
    session — 400x the window); only `last_token_usage` is the context occupancy. Reading
    the cumulative field would peg every session at 0% and wrap them all up instantly."""
    path = _write_rollout(tmp_path, [_token_count(25840)])  # cumulative is 104779470
    assert codex_sessions.rollout_ctx_remaining(path) == 90


def test_ctx_is_none_when_no_token_count_exists(tmp_path):
    """Fail-closed: unknown ctx means no wrap-up and no band crossing — never a guess."""
    path = _write_rollout(tmp_path, ['{"type": "session_meta"}', '{"type": "event_msg"}'])
    assert codex_sessions.rollout_ctx_remaining(path) is None


def test_ctx_is_none_for_a_missing_or_unreadable_file(tmp_path):
    assert codex_sessions.rollout_ctx_remaining(tmp_path / "nope.jsonl") is None


def test_ctx_is_none_when_the_window_is_absent_or_zero(tmp_path):
    """Never divide by zero, never invent a denominator."""
    for window in (0, -1):
        path = _write_rollout(
            tmp_path, [_token_count(1000, window=window)], name=f"r{window}.jsonl"
        )
        assert codex_sessions.rollout_ctx_remaining(path) is None
    path = _write_rollout(
        tmp_path,
        [
            '{"type": "event_msg", "payload": {"type": "token_count", "info": '
            '{"last_token_usage": {"total_tokens": 10}}}}'
        ],
        name="nowindow.jsonl",
    )
    assert codex_sessions.rollout_ctx_remaining(path) is None


def test_ctx_clamps_to_zero_when_usage_exceeds_the_window(tmp_path):
    """Post-compaction / overflow must read 0% left, never a negative."""
    path = _write_rollout(tmp_path, [_token_count(300000)])
    assert codex_sessions.rollout_ctx_remaining(path) == 0


def test_ctx_reads_only_the_tail_of_a_huge_rollout(tmp_path):
    """Rollouts reach 16 MB on this host and the daemon reads them EVERY TICK, so the
    whole file is never loaded. `token_count` events are frequent (773 in the sampled
    session), so the newest is always far inside the tail window."""
    filler = '{"type": "response_item", "payload": {"type": "message", "text": "%s"}}' % ("x" * 500)
    lines = [_token_count(999999)] + [filler] * 4000 + [_token_count(129200)]
    path = _write_rollout(tmp_path, lines)
    assert path.stat().st_size > 2_000_000  # comfortably bigger than the tail window
    assert codex_sessions.rollout_ctx_remaining(path) == 50  # found the LAST one


def test_ctx_survives_a_partial_first_line_from_the_tail_seek(tmp_path):
    """Seeking to a byte offset lands mid-record; the truncated leading line must be
    skipped as unparsable rather than crashing the read."""
    filler = '{"type": "response_item", "payload": {"text": "%s"}}' % ("y" * 900)
    path = _write_rollout(tmp_path, [filler] * 3000 + [_token_count(129200)])
    assert codex_sessions.rollout_ctx_remaining(path, tail_bytes=1234) == 50


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


def test_codex_by_tmux_session_keys_live_sessions_by_their_tmux_session(tmp_path):
    home = _index(tmp_path, [(_ID_A, "topic-a"), (_ID_B, "topic-b")])
    host = _host(
        comms={10: "codex", 20: "codex"},
        cwds={10: "/data/projects/one", 20: "/data/projects/two"},
        fds={10: [_rollout(_ID_A)], 20: [_rollout(_ID_B)]},
    )
    by = codex_sessions.codex_by_tmux_session(
        {101: "s-one", 202: "s-two"}, codex_home=home, ppid_of={10: 101, 20: 202}.get, **host
    )
    assert set(by) == {"s-one", "s-two"}
    assert by["s-one"].name == "topic-a"
    assert by["s-one"].pid == 10
    assert by["s-two"].name == "topic-b"


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
