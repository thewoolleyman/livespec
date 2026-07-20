"""Tests for supervisor.py — the daemon state machine, injection, restart, GC.

Run: ``uv run pytest .claude/skills/overseer/ -q``. A FAKE tmux object supplies
canned pane captures / process-identity / session existence; NO real tmux runs.
The adversarial-critical behaviors are covered: state precedence (busy/gate/
blocked suppress injection), stamp-before-paste, the restart interlock firing
ONLY on marker-valid + not-busy + idle, auto-link refusing a cross-repo session,
archive-GC dropping an archived row, ctx-unknown never injecting — PLUS the
2026-07-13 adversarial code-review blocker fixes (B1..B8): the identity gate,
failure propagation, marker/round lifecycle, read-only list, and the start guard.
"""

import contextlib
import datetime
import importlib.machinery
import importlib.util
import io as _io
import json
import os
from pathlib import Path

import codex_sessions
import pytest
import registry
import signals
import supervisor


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


# A pid that cannot exist, so the real ``claude_sessions.proc_children`` reader
# fails soft to ``[]`` → no descendant, no subshell. FakeTmux.pane_pid returns
# this by default so bg-shell detection is inert unless a test opts in.
_NO_SUBSHELL_PID = 2**30


class FakeTmux:
    """Injectable stand-in for tmuxio.TmuxIO — canned reads, recorded writes."""

    def __init__(self):
        self.sessions = set()
        self.panes = {}
        self.cmds = {}
        self.paths = {}
        self.calls = []
        self.window_name = None  # last name written by the attention badge
        self.on_paste = None  # callback(session, text) for stamp-before-paste checks
        self.paste_ok = True  # set False to model a failed bracketed paste (B5)
        self.respawn_ok = True  # set False to model a failed respawn (B5)
        # set False to model a codex respawn whose pane never becomes a live codex TUI
        # (so `_await_pane(pane_is_codex)` fails) — the Codex-restart await-fail leg.
        self.respawn_yields_codex = True
        self.new_session_ok = True  # set False to model a failed new-session (Codex #3)
        self.pane_pids = {}  # {pane_pid: session} for the registry→tmux adopt join
        # Per-session pane PID (the login shell) fed to has_active_subshell. Defaults
        # to a NONEXISTENT pid so the real /proc reader returns [] → NO subshell,
        # keeping every legacy test's bg_shell False unless it opts in by setting a
        # pane pid here AND injecting fake children_of/comm_of on the Supervisor.
        self.pane_pid_map = {}
        self._cap_idx = {}
        self._cmd_idx = {}

    def pane_pid_sessions(self):
        return dict(self.pane_pids)

    def serve(self, session, repo, capture=None, cmd="node"):
        """Register ``session`` as a live Claude TUI whose cwd is inside ``repo``.

        The identity gate (B3) requires `pane_current_command` to look like Claude
        AND `pane_current_path` to resolve inside the row's repo before any act, so
        a valid tracked session must report both. ``cmd="zsh"`` models a pane that
        dropped to a shell (identity-gate `not-claude`).
        """
        self.sessions.add(session)
        self.cmds[session] = cmd
        self.paths[session] = str(repo)
        if capture is not None:
            self.panes[session] = capture

    def session_exists(self, session):
        self.calls.append(("exists", session))
        return session in self.sessions

    def pane_id(self, session):
        # Model pane-id resolution (RB3): return the session name itself as the
        # "pane id" for a live session (so target == name and the canned dicts,
        # keyed by name, still resolve), or None if the session is gone.
        self.calls.append(("pane_id", session))
        return session if session in self.sessions else None

    def pane_pid(self, session):
        # The pane's login-shell PID. Default is a nonexistent pid (real
        # proc_children → []), so bg_shell is False unless a test sets a pid here
        # and injects a fake process tree via the Supervisor's children_of/comm_of.
        self.calls.append(("pane_pid", session))
        return self.pane_pid_map.get(session, _NO_SUBSHELL_PID)

    def capture_pane(self, session):
        self.calls.append(("capture", session))
        val = self.panes.get(session, "")
        # A list value is a sequence of successive frames (for the settled-delta
        # check): each capture returns the next frame, repeating the last once
        # exhausted. A plain string returns the same frame every call (a settled
        # pane). The daemon's `_pane_settled` captures twice; a 2-frame list with
        # different content makes those two captures differ → "streaming".
        if isinstance(val, list):
            i = min(self._cap_idx.get(session, 0), len(val) - 1) if val else 0
            self._cap_idx[session] = i + 1
            return val[i] if val else ""
        return val

    def pane_current_command(self, session):
        self.calls.append(("cmd", session))
        val = self.cmds.get(session)
        # A list models a CHANGING command across successive calls (e.g. the
        # identity re-check sees the pane after it exited to a shell — Codex #1).
        if isinstance(val, list):
            i = min(self._cmd_idx.get(session, 0), len(val) - 1) if val else 0
            self._cmd_idx[session] = i + 1
            return val[i] if val else None
        return val

    def pane_current_path(self, session):
        self.calls.append(("path", session))
        return self.paths.get(session)

    def list_sessions(self):
        return sorted(self.sessions)

    def send_keys(self, session, keys):
        self.calls.append(("keys", session, keys))
        return True

    def bracketed_paste(self, session, text):
        self.calls.append(("paste", session, text))
        if self.on_paste is not None:
            self.on_paste(session, text)
        return self.paste_ok

    def respawn_pane(self, session, cwd, command):
        self.calls.append(("respawn", session, cwd, command))
        if not self.respawn_ok:
            return False
        # Model the runtime the command launches so the post-respawn identity await
        # (`_await_pane`) matches: a `codex resume …` respawn yields a codex pane (`bun`,
        # the launcher), any other command a fresh Claude TUI (`node`). A codex respawn
        # with `respawn_yields_codex=False` comes up non-codex (`node`), modeling the
        # await-fail leg.
        if "codex resume" in command and self.respawn_yields_codex:
            self.cmds[session] = "bun"
        else:
            self.cmds[session] = "node"
        self.paths[session] = cwd
        self.sessions.add(session)
        return True

    def new_session(self, name, cwd):
        self.calls.append(("new", name, cwd))
        if not self.new_session_ok:
            return False  # model a failed new-session (session NOT created)
        self.sessions.add(name)
        return True

    def rename_window(self, pane, name):
        # The attention badge on the tmux WINDOW name (`overseer` → `overseer(2!)`) —
        # the only overseer surface visible from a session the operator is attached to.
        self.calls.append(("rename_window", pane, name))
        self.window_name = name
        return True

    # test helpers ---------------------------------------------------- #
    def paste_texts(self):
        return [c[2] for c in self.calls if c[0] == "paste"]

    def renames(self):
        return [c[2] for c in self.calls if c[0] == "rename_window"]

    def has(self, method):
        return any(c[0] == method for c in self.calls)


# The REAL live Claude TUI idle shape (verified 2026-07-13): an empty `❯` prompt
# between two horizontal rule lines, the statusline as the SECOND-to-last row,
# and a footer hint as the LAST row (NOT a `╭─╮` box + `? for shortcuts`).
_RULE = "─" * 40
_HINT = "  ⏵⏵ bypass permissions on (shift+tab to cycle) · ← for agents"
# The real active-generation spinner (a token counter / dot-elapsed / hook phase);
# the lingering completed-turn summary "✻ Brewed for 25s" is deliberately NOT busy.
_SPINNER = "✻ Galloping… (running stop hooks… 1/3 · 24s · ↓ 1.4k tokens)"


def _idle_capture(ctx=None, body="", *, topic=None):
    """The idle box. ``topic`` renders the `-n <topic>` TITLED top border (B2)."""
    status = "  Opus 4.8 (1M context) | /x/repo"
    if ctx is not None:
        status += f" | Ctx: {ctx}% left"
    head = f"● {body}\n" if body else "● prior response\n"
    top = _RULE if topic is None else ("─" * 30) + f" {topic} ──"
    return f"{head}{top}\n❯ \n{_RULE}\n{status}\n{_HINT}\n"


def _busy_capture(ctx=None):
    """An actively-generating pane: the real spinner above the (idle-shaped) box."""
    return f"● response\n{_SPINNER}\n" + _idle_capture(ctx)


# The REAL live idle Codex TUI shape (verified 2026-07-17, codex-cli 0.144.5): a `›`
# input line above the Codex statusline `model · cwd · Context N% left · <name>` — NOT
# Claude's empty-`❯`-between-rules box. An UNNAMED session shows its UUID where a named
# one shows the thread_name; here we render the topic (a named session).
def _codex_idle_capture(ctx=None, *, topic="topic"):
    status = "  gpt-5.5 high · /x/repo"
    if ctx is not None:
        status += f" · Context {ctx}% left"
    status += f" · {topic}"
    return f"● prior response\n› Write tests for @filename\n{status}\n"


def _codex_busy_capture(ctx=None):
    """An actively-generating Codex pane: `esc to interrupt` (what `is_busy` matches) —
    the signal `_submit_prompt(expect_codex=True)` confirms a Codex submit by."""
    status = "  gpt-5.5 high · /x/repo"
    if ctx is not None:
        status += f" · Context {ctx}% left"
    return f"● response\n◦ Working (1s • esc to interrupt)\n› Write tests for @filename\n{status}\n"


# Legacy alias kept for readability in tests that predate the real-shape fixtures.
IDLE_BOX = _idle_capture()


def _make_plan(tmp_path, repo_name="repo", topic="topic", handoff=b"HANDOFF v1\n"):
    repo = tmp_path / repo_name
    plan = repo / "plan" / topic
    plan.mkdir(parents=True)
    (plan / "handoff.md").write_bytes(handoff)
    return repo, topic


def _mapped_track(repo, topic, session):
    return registry.Track(
        topic=topic,
        repo=str(repo),
        tmux=session,
        handoff=supervisor.default_handoff(str(repo), topic),
        resume=supervisor.default_resume(str(repo), topic),
    )


def _key_for(repo, topic):
    """The normalized in-memory inject-state key the supervisor uses."""
    return supervisor._key(str(repo), topic)


def _sup(tmp_path, fake, **kwargs):
    kwargs.setdefault("out", _io.StringIO())
    kwargs.setdefault("now", lambda: 1000.0)  # overridable: pass now=lambda: clock["t"]
    kwargs.setdefault("sleep", lambda _s: None)
    # Hermetic Codex discovery by default (#6): an empty `/proc` scan + a non-existent
    # `~/.codex` so adopt/refresh touch NO real host state, and the suite stays green with
    # a live codex on the host. With `pids_of_comm` returning [], the fd/cwd readers are
    # never reached, so they need no fake. A codex-behavior test overrides these to inject
    # a simulated session (see test_refresh_and_adopt_route_codex_through_injected_seams).
    kwargs.setdefault("codex_home", str(tmp_path / "codex-home-none"))
    kwargs.setdefault("codex_pids_of_comm", lambda _comm: [])
    # Hermetic host preconditions: present them as SUPPORTED so no test depends on the
    # RUNNER having tmux (or a /proc). Without these defaults the `run()` startup gate
    # would fail every existing run() test on a container without tmux installed — the
    # same host-coupling hazard the codex seams above already close. A
    # precondition-behavior test overrides them to simulate an unsupported host.
    kwargs.setdefault("proc_root", str(tmp_path))  # any existing dir reads as "has /proc"
    kwargs.setdefault("which", lambda _name: "/usr/bin/tmux")
    return supervisor.Supervisor(
        tmux=fake,
        store_path=str(tmp_path / "map.jsonl"),
        stamp_path=str(tmp_path / "stamps.json"),
        **kwargs,
    )


# --------------------------------------------------------------------------- #
# State precedence: busy / gate / blocked SUPPRESS injection.
# --------------------------------------------------------------------------- #


def test_busy_suppresses_injection(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture="running... esc to interrupt\n  Ctx: 40% left\n")
    sup = _sup(tmp_path, fake)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"
    assert not fake.has("paste")  # busy must suppress the wrap-up injection


def test_structured_gate_suppresses_injection(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(
        session, repo, capture="Do you want to proceed?\n❯ 1. Yes\n  2. No\n  Ctx: 40% left\n"
    )
    sup = _sup(tmp_path, fake)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "blocked:human"
    assert not fake.has("paste")


def test_blocked_marker_suppresses_injection(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    _declare(repo, topic, "blocked: waiting on schema call")
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=40))  # idle+low ctx but blocked marker
    sup = _sup(tmp_path, fake)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "blocked:human"
    assert view.note == "waiting on schema call"
    assert not fake.has("paste")


# --------------------------------------------------------------------------- #
# B3 identity gate: NEVER keystroke into a shell / wrong-repo pane.
# --------------------------------------------------------------------------- #


def test_shell_pane_never_pastes(tmp_path):
    """A tracked session that dropped to a shell (pane_current_command != claude)
    must get NO paste — even at low ctx with an idle-looking old box in scrollback
    (B3: else the wrap-up executes in the shell and forges a marker).

    This pins the SAFETY half only. The status LABEL such a pane earns is asserted
    by the `exited to a shell` tests below (it is `session-gone`, not `not-claude`).
    """
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    # Old idle box still on screen + a shell prompt; pane command is now zsh.
    fake.serve(session, repo, capture=_idle_capture(ctx=40), cmd="zsh")
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()  # isolated + empty: no live Claude anywhere
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {})
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status != "working"  # never mistaken for a live session
    assert not fake.has("paste")
    assert not fake.has("respawn")


# --------------------------------------------------------------------------- #
# A pane that EXITED to a shell is a track whose session ENDED — `session-gone`,
# not the alarming `not-claude` (which means the mapping points at a FOREIGN
# pane). The shipped daemon conflated the two: `not-claude` was designed as the
# identity GATE for acts (correct, and unchanged) but was reused as the row
# STATUS, so an ordinary finished track sat red in NEEDS YOU claiming a live tmux
# mapping. Found live 2026-07-16 (fabro-ci-image-factoring → livespec1, a bare
# zsh, no live Claude anywhere).
# --------------------------------------------------------------------------- #


def test_pane_exited_to_shell_is_session_gone(tmp_path):
    """The mapped tmux session is ALIVE but its Claude EXITED, leaving a bare shell,
    and no Claude for the topic is live anywhere → the track's session is GONE."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=40), cmd="zsh")
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()  # no live Claude for the topic
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {})
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "session-gone"
    assert not fake.has("paste")
    assert not fake.has("respawn")


def test_no_managed_pane_row_never_names_a_tmux_session(tmp_path):
    """The `tmux` cell means "the tmux session holding this track" — so a track with
    NO session there must not name one (maintainer-declared 2026-07-16: "it shouldn't
    display the session name; the session doesn't exist in that panel anymore").

    A leftover MAPPING to a tmux session that now holds a bare shell is not a session:
    rendering `livespec1` there asserted a live session that did not exist. The cell
    goes empty (like `unassigned`); `session-gone` alone carries "this WAS mapped and
    is now dead", and `_alert` degrades to "no live tmux session" with no jump command
    (there is nowhere to jump).
    """
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=40), cmd="zsh")
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {})
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "session-gone"
    assert view.tmux is None


def test_missing_tmux_session_also_never_names_a_tmux_session(tmp_path):
    """Same rule via the other route into the helper — the mapped tmux session is gone
    outright, so there is even less of a session to name."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()  # session never added → session_exists False
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {})
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "session-gone"
    assert view.tmux is None


def test_a_foreign_pane_is_session_gone_not_a_status_of_its_own(tmp_path):
    """A live Claude in a DIFFERENT repo is not "not-claude" — from this plan's point of
    view the fact is identical to a bare shell: its session is NOT IN THIS TMUX. The plan
    was assigned to something once, so it is `session-gone`.

    The mapping ROW is kept — it is the memory of having seen the session, which is what
    separates `session-gone` from `unassigned` (maintainer-declared 2026-07-17: "KEEP
    session-gone if you've ever seen the session, only use unassigned if you've never
    seen it"). And no dead terminal is named: tmux is None.
    """
    repo, topic = _make_plan(tmp_path)
    other = tmp_path / "elsewhere"
    other.mkdir()
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, other, capture=_idle_capture(ctx=40))  # live claude, wrong repo
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {})
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "session-gone"
    assert view.tmux is None  # never name the pane it is wrongly pointed at
    assert not fake.has("paste")  # the identity gate still guards every act


def test_pane_exited_to_shell_with_live_claude_outside_tmux_is_live_outside_tmux(tmp_path):
    """The pane dropped to a shell BUT the topic's Claude is alive OUTSIDE tmux.

    The live-outside-tmux fallback was wired ONLY into the missing-tmux-session
    branch, so this case reported `not-claude` and hid a live session behind an
    alarm. Both no-managed-pane paths must consult it.
    """
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=40), cmd="zsh")
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    # Live registry session for the topic whose pid walks up to NO tmux pane.
    _write_session(sessions_dir, 100, name=topic, cwd=str(repo), status="busy")
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {100: "pt"})
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "live-outside-tmux"
    assert view.note is not None and "OUTSIDE tmux" in view.note
    assert not fake.has("paste")


def test_identity_rechecked_before_acting_catches_shell(tmp_path):
    """Codex re-review #1: identity passes the TOP gate but the pane exits to a
    shell during the capture+settle window — the re-check immediately before
    acting must catch it (not-claude, no paste). The fake returns `node` at the
    top gate then `zsh` at the re-check."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=40))  # idle, low ctx → would inject
    fake.cmds[session] = ["node", "zsh"]  # claude at top gate, shell at the re-check
    sup = _sup(tmp_path, fake)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    # `settling`: the pane changed UNDER US mid-tick — wait and re-read. The next tick's
    # top gate classifies the settled truth. The SAFETY property (no paste into the
    # shell) is what this test exists for and is unchanged.
    assert view.status == "settling"
    assert not fake.has("paste")  # never pasted into the shell


# --------------------------------------------------------------------------- #
# warned: stamp is written BEFORE the paste; ctx-unknown never injects.
# --------------------------------------------------------------------------- #


def test_warned_writes_stamp_before_pasting(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(
        session, repo, capture=_idle_capture(ctx=40)
    )  # below the default warn threshold (50)
    stamp_path = str(tmp_path / "stamps.json")
    seen = []
    fake.on_paste = lambda _s, _t: seen.append(
        registry.read_injection_stamp(str(repo), topic, stamp_path)
    )
    sup = _sup(tmp_path, fake)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "warned"
    assert fake.paste_texts() and _WRAPUP_SENTINEL in fake.paste_texts()[0]
    assert seen == [1000.0]  # stamp written BEFORE the paste, at now()==1000.0
    assert ("keys", session, "Enter") in fake.calls


def test_failed_paste_clears_stamp_and_does_not_advance(tmp_path):
    """B5: if the wrap-up paste fails, the injection stamp is CLEARED and count is
    NOT advanced, so the next tick retries rather than the round being counted as
    open with an un-delivered wrap-up."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=40))
    fake.paste_ok = False  # the bracketed paste fails
    sup = _sup(tmp_path, fake)
    sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) is None
    # Next tick retries (writes the stamp again + attempts paste again).
    sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert len([c for c in fake.calls if c[0] == "paste"]) == 2


def test_ctx_unknown_never_injects(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=None))  # idle but NO Ctx line → unknown
    sup = _sup(tmp_path, fake)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "idle"
    assert view.ctx is None
    assert not fake.has("paste")


def test_idle_above_threshold_nudges_to_keep_going_only_after_an_hour(tmp_path):
    """A session idle at an empty prompt with context ABOVE the threshold and no declaration
    is nudged ONCE to keep going — but ONLY after it has been continuously idle for at least
    `_IDLE_NUDGE_AFTER` (maintainer 2026-07-18: nudging a briefly-idle session interrupts
    active work). Below the floor it reads `idle-with-context-left` but is NOT keystroked; a
    tick past the floor nudges once, and a further idle tick does NOT re-nudge."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))  # well above threshold
    clock = {"t": 1000.0}
    sup = _sup(tmp_path, fake, now=lambda: clock["t"])
    sup._claude_status = {session: "idle"}
    track = _mapped_track(repo, topic, session)

    # First idle tick: descriptive status, but NOT yet nudged (idle < 1 hour).
    view = sup.evaluate(track, act=True)
    assert view.status == "idle-with-context-left"
    assert _nudge_count(fake) == 0  # too soon — must be idle ≥ 1 hour first
    assert signals.read_state(str(repo), topic) is None  # no marker written yet

    # Past the 1-hour floor → nudged ONCE, marker written.
    clock["t"] += supervisor._IDLE_NUDGE_AFTER + 1
    view = sup.evaluate(track, act=True)
    assert view.status == "idle-with-context-left"
    assert _nudge_count(fake) == 1  # nudged once
    assert _wrapup_count(fake) == 0  # a keep-going nudge, NOT a wind-down wrap-up
    state = signals.read_state(str(repo), topic)
    assert state is not None and state.token == signals.STATE_IDLE_WITH_CONTEXT_LEFT

    # Still idle with the marker present → single prompt: NOT re-nudged.
    clock["t"] += supervisor._IDLE_NUDGE_AFTER + 1
    view = sup.evaluate(track, act=True)
    assert view.status == "idle-with-context-left"
    assert _nudge_count(fake) == 1


def test_nudge_re_arms_after_the_session_takes_a_turn(tmp_path):
    """Single prompt per EPISODE: after a nudge, the session going non-idle (busy) clears the
    marker AND resets the idle clock, so idling with context left AGAIN re-nudges — but again
    only after a fresh 1-hour idle spell (brief idle after a turn is not nudged)."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))
    clock = {"t": 1000.0}
    sup = _sup(tmp_path, fake, now=lambda: clock["t"])
    sup._claude_status = {session: "idle"}
    track = _mapped_track(repo, topic, session)

    sup.evaluate(track, act=True)  # idle_since stamped
    clock["t"] += supervisor._IDLE_NUDGE_AFTER + 1
    assert sup.evaluate(track, act=True).status == "idle-with-context-left"
    assert _nudge_count(fake) == 1

    # The session takes a turn (Claude busy) → marker cleared AND the idle clock reset.
    sup._claude_status = {session: "busy"}
    assert sup.evaluate(track, act=True).status == "working"
    assert signals.read_state(str(repo), topic) is None  # marker gone

    # Idle again with context left but only BRIEFLY → not yet re-nudged (fresh 1h clock).
    sup._claude_status = {session: "idle"}
    assert sup.evaluate(track, act=True).status == "idle-with-context-left"
    assert _nudge_count(fake) == 1  # the new episode has not reached the floor

    # Past a fresh hour → a SECOND nudge (a new episode).
    clock["t"] += supervisor._IDLE_NUDGE_AFTER + 1
    assert sup.evaluate(track, act=True).status == "idle-with-context-left"
    assert _nudge_count(fake) == 2


def test_claude_waiting_is_not_nudged(tmp_path):
    """A session Claude reports as `waiting` (at a gate/prompt for the human) is NOT nudged
    even above threshold — it is a blocking question for the human, not free to continue."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))
    sup = _sup(tmp_path, fake)
    sup._claude_status = {session: "waiting"}
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "idle"
    assert _nudge_count(fake) == 0


def test_nudge_never_overwrites_a_session_declaration(tmp_path):
    """The daemon writes `idle-with-context-left` ONLY when the file is empty — a session
    that declared `blocked` (the Codex waiting-on-human-in-prose escape) is never nudged
    and its declaration is never clobbered."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))
    sup = _sup(tmp_path, fake)
    sup._claude_status = {session: "idle"}
    _declare(repo, topic, "blocked: waiting on a human decision (asked in prose)")
    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "blocked:human"
    assert _nudge_count(fake) == 0
    state = signals.read_state(str(repo), topic)  # the declaration survived untouched
    assert state is not None and state.token == signals.STATE_BLOCKED


# --------------------------------------------------------------------------- #
# Voiding a stale `blocked:` declaration. A GENERATING session is, by observation,
# not waiting on a human — so a `blocked:` it has outlived is provably false, and a
# dead reason must not ride a `working` row nor fire a false `blocked:human` alert
# when the session next goes idle. Found live 2026-07-16: a fresh overseer-rewrite
# session rendered `working (awaiting maintainer next-step decision — Codex…)` — the
# PREVIOUS session's declaration, inherited because the pane was replaced out-of-band
# (so `_do_restart`'s `_clear_state` never ran).
# --------------------------------------------------------------------------- #


def test_stale_blocked_is_voided_when_the_session_resumes_generating(tmp_path):
    """Past the grace + a real generation spinner ⇒ the declaration is provably dead."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_busy_capture())  # a real spinner: generating
    sup = _sup(tmp_path, fake)
    _declare(repo, topic, "blocked: a reason from a session that has moved on", mtime=800.0)
    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"
    assert view.note is None  # the dead reason no longer rides the row
    assert signals.read_state(str(repo), topic) is None  # voided


def test_fresh_blocked_survives_the_declaring_turns_own_busy_tail(tmp_path):
    """RB1, for `blocked` as for `ready`: the declaring turn's final text keeps streaming
    for 10-60s AFTER the write, so a YOUNG declaration must survive a busy tick — else
    every legitimate declaration is destroyed before the pane ever goes idle."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_busy_capture())
    sup = _sup(tmp_path, fake)
    _declare(repo, topic, "blocked: I need your call", mtime=1001.0)  # younger than the grace
    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"
    state = signals.read_state(str(repo), topic)
    assert state is not None and state.token == signals.STATE_BLOCKED  # survived


def test_blocked_with_only_a_background_shell_is_never_voided(tmp_path):
    """The counter-case that bounds the rule. A session busy ONLY via a live
    `Bash(run_in_background)` command (Claude `shell`) is AT ITS PROMPT — it can be
    genuinely waiting on a human while a build runs, so its declaration is NOT provably
    stale and must survive however old it is. Only GENERATING voids."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))  # no spinner
    sup = _sup(tmp_path, fake)
    sup._claude_status = {session: "shell"}  # busy via a background command only
    _declare(repo, topic, "blocked: need your call", mtime=800.0)  # old, but NOT stale
    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"
    state = signals.read_state(str(repo), topic)
    assert state is not None and state.token == signals.STATE_BLOCKED  # survived


def test_stale_blocked_is_voided_for_an_in_process_sub_agent(tmp_path):
    """Claude `busy` with no spinner (an in-process Task sub-agent) is still GENERATING —
    the session is working, not waiting — so a stale declaration is voided here too."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))  # pane looks idle
    sup = _sup(tmp_path, fake)
    sup._claude_status = {session: "busy"}  # sub-agent running in-process
    _declare(repo, topic, "blocked: stale", mtime=800.0)
    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"
    assert signals.read_state(str(repo), topic) is None  # voided


def test_idle_blocked_session_is_never_voided(tmp_path):
    """The load-bearing case: a session sitting blocked and NOT busy keeps its
    declaration forever and keeps alerting. Voiding is scoped to "resumed generating"."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))
    sup = _sup(tmp_path, fake)
    sup._claude_status = {session: "waiting"}
    _declare(repo, topic, "blocked: still waiting on you", mtime=800.0)
    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "blocked:human"
    state = signals.read_state(str(repo), topic)
    assert state is not None and state.token == signals.STATE_BLOCKED


def test_nudge_marker_is_not_an_attention_status():
    """`idle-with-context-left` is the daemon handling it, not a human hand-off — it must
    NOT appear in the NEEDS YOU block."""
    view = supervisor.RowView(
        topic="t", repo="/r", tmux="s", ctx=73, status="idle-with-context-left"
    )
    assert supervisor.needs_attention(view) is False


# A phrase from the SHARED wrap-up body, so it matches BOTH tones (the gentle
# suggestion at 50/40 and the insistent shutdown demand at 30/20/10).
_WRAPUP_SENTINEL = "Declare your state by writing ONE line"


def _wrapup_count(fake):
    return len([t for t in fake.paste_texts() if _WRAPUP_SENTINEL in t])


# A phrase unique to the idle-with-context-left "keep going" nudge (never in the wrap-up).
_NUDGE_SENTINEL = "do NOT offer to stop"


def _nudge_count(fake):
    return len([t for t in fake.paste_texts() if _NUDGE_SENTINEL in t])


def test_escalates_one_paste_per_band_as_ctx_drops(tmp_path):
    """Part 2: warn ONCE at the threshold, then once more each time remaining
    crosses a lower 10%-band (40, 30, 20, 10) — each band at most once. Feeding
    ctx exactly at each band yields exactly one NEW wrap-up paste per band; a
    re-tick at the same low ctx (all bands already notified) adds none."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo)
    sup = _sup(tmp_path, fake)  # warn_percent = the default (50)
    track = _mapped_track(repo, topic, session)
    counts = []
    for ctx in (45, 40, 30, 20, 10):
        fake.panes[session] = _idle_capture(ctx=ctx)
        sup.evaluate(track, act=True)
        counts.append(_wrapup_count(fake))
    assert counts == [1, 2, 3, 4, 5]  # one new paste per band crossed
    # Same low ctx again: every band already notified → no further paste.
    fake.panes[session] = _idle_capture(ctx=10)
    sup.evaluate(track, act=True)
    assert _wrapup_count(fake) == 5


def test_multi_band_drop_coalesces_to_one_paste_marks_all(tmp_path):
    """Part 2: several bands crossed in ONE tick coalesce into a SINGLE wrap-up
    paste, yet ALL crossed bands are marked notified so none re-fires; a later,
    lower tick fires only the newly-crossed band."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=18))  # crosses 45,40,30,20 at once
    sup = _sup(tmp_path, fake, warn_percent=45)  # explicit threshold: decouple from the default
    track = _mapped_track(repo, topic, session)
    view = sup.evaluate(track, act=True)
    assert _wrapup_count(fake) == 1  # coalesced into ONE message
    assert set(registry.read_notified_bands(str(repo), topic, sup.stamp_path)) == {45, 40, 30, 20}
    assert view.status == "danger"  # 18 <= DANGER_CTX_REMAINING (20)
    # A still-lower tick fires only the new band (10), once.
    fake.panes[session] = _idle_capture(ctx=8)
    sup.evaluate(track, act=True)
    assert _wrapup_count(fake) == 2
    assert set(registry.read_notified_bands(str(repo), topic, sup.stamp_path)) == {
        45,
        40,
        30,
        20,
        10,
    }


def test_bands_are_durable_across_daemon_restart(tmp_path):
    """Part 2 durability: a band recorded in the sidecar is NOT re-injected after a
    daemon RESTART — simulated by a FRESH Supervisor (empty in-memory state) built
    on the SAME stamp_path. Escalation state lives in the durable sidecar."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    stamp_path = str(tmp_path / "stamps.json")
    store_path = str(tmp_path / "map.jsonl")
    track = _mapped_track(repo, topic, session)

    fake1 = FakeTmux()
    fake1.serve(session, repo, capture=_idle_capture(ctx=40))
    sup1 = supervisor.Supervisor(
        tmux=fake1,
        store_path=store_path,
        stamp_path=stamp_path,
        out=_io.StringIO(),
        now=lambda: 1000.0,
        sleep=lambda _s: None,
        warn_percent=45,  # explicit threshold: decouple from the default
    )
    sup1.evaluate(track, act=True)
    assert set(registry.read_notified_bands(str(repo), topic, stamp_path)) == {45, 40}
    assert fake1.has("paste")

    # "Restart": a brand-new Supervisor on the SAME sidecar, same ctx.
    fake2 = FakeTmux()
    fake2.serve(session, repo, capture=_idle_capture(ctx=40))
    sup2 = supervisor.Supervisor(
        tmux=fake2,
        store_path=store_path,
        stamp_path=stamp_path,
        out=_io.StringIO(),
        now=lambda: 2000.0,
        sleep=lambda _s: None,
        warn_percent=45,  # explicit threshold: decouple from the default
    )
    sup2.evaluate(track, act=True)
    assert not fake2.has("paste")  # bands 45+40 already notified → no re-spam


def test_cleared_round_re_warns_all_bands(tmp_path):
    """Part 2: clearing the injection stamp (as a restart does) resets BOTH the
    round timestamp and the notified bands, so a fresh round re-warns from the top
    band again."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=40))
    sup = _sup(tmp_path, fake, warn_percent=45)  # explicit threshold: decouple from the default
    track = _mapped_track(repo, topic, session)
    sup.evaluate(track, act=True)
    assert set(registry.read_notified_bands(str(repo), topic, sup.stamp_path)) == {45, 40}
    # Clear the round (mirrors _void_ready_marker / restart) → bands reset.
    registry.clear_injection_stamp(str(repo), topic, sup.stamp_path)
    assert registry.read_notified_bands(str(repo), topic, sup.stamp_path) == []
    sup.evaluate(track, act=True)  # fresh round → re-warns the crossed bands again
    assert _wrapup_count(fake) == 2  # a second wrap-up in the new round
    assert set(registry.read_notified_bands(str(repo), topic, sup.stamp_path)) == {45, 40}


def test_danger_surfaces_below_danger_line(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=15))  # <= DANGER, no ready marker
    sup = _sup(tmp_path, fake)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "danger"


# --------------------------------------------------------------------------- #
# Part 1: daemon-wide warn_percent vs. per-track ctx_threshold override.
# --------------------------------------------------------------------------- #


def test_warn_percent_default_applies_to_track_without_override(tmp_path):
    """Supervisor(warn_percent=30): a track with ctx_threshold=None inherits the
    daemon-wide default, so it stays idle at ctx 40 (> 30) and warns at ctx 30."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=40))  # 40 > warn_percent 30
    sup = _sup(tmp_path, fake, warn_percent=30)
    track = _mapped_track(repo, topic, session)  # ctx_threshold defaults to None
    assert track.ctx_threshold is None
    view = sup.evaluate(track, act=True)
    # Above the inherited threshold (40 > 30) → a keep-going NUDGE, not a wind-down warn.
    assert view.status == "idle-with-context-left"
    assert _wrapup_count(fake) == 0
    # Drop to the daemon-wide threshold → warns (wind-down wrap-up).
    fake.panes[session] = _idle_capture(ctx=30)
    view = sup.evaluate(track, act=True)
    assert view.status == "warned"
    assert _wrapup_count(fake) == 1


def test_explicit_ctx_threshold_overrides_warn_percent(tmp_path):
    """A per-track ctx_threshold=60 warns at 60 REGARDLESS of the daemon-wide
    warn_percent (30 here): ctx 55 warns even though 55 > 30 would not under the
    daemon default."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=55))
    sup = _sup(tmp_path, fake, warn_percent=30)
    track = registry.Track(
        topic=topic,
        repo=str(repo),
        tmux=session,
        handoff=supervisor.default_handoff(str(repo), topic),
        resume=supervisor.default_resume(str(repo), topic),
        ctx_threshold=60,
    )
    view = sup.evaluate(track, act=True)
    assert view.status == "warned"  # 55 <= 60 override, despite warn_percent 30
    assert fake.has("paste")


# --------------------------------------------------------------------------- #
# Restart interlock: fires ONLY on marker-valid + not-busy + idle; deletes marker.
# --------------------------------------------------------------------------- #


def _declare(repo, topic, value, *, mtime=1001.0):
    """Write the session's ONE state file with ``value`` (e.g. "ready", "blocked: x").

    The single indicator lives at ``<repo>/tmp/overseer/<topic>/.overseer-state`` — its
    parent dir does not exist yet, so create it. One file with a VALUE: there is no way
    to be simultaneously `ready` and `blocked`, which is the whole point.
    """
    path = signals.state_path(str(repo), topic)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{value}\n")
    os.utime(path, (mtime, mtime))
    return path


def _arm_ready_marker(repo, topic, *, mtime=1001.0):
    """The session declares `ready` — the ONLY thing that authorizes a restart."""
    return _declare(repo, topic, signals.STATE_READY, mtime=mtime)


def _assert_no_tmux_scoping(command):
    """The L1 env inversion is REMOVED (plan/tmux-fleet-visibility): a spawn
    command must carry NO tmux socket scoping, so a bare `tmux ls` in the
    spawned agent lists the real fleet. This pins the ABSENCE so the prefix
    cannot silently regress."""
    assert "TMUX_TMPDIR" not in command
    assert "unset TMUX" not in command


def test_claude_launch_command_carries_no_tmux_scoping(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)

    command = supervisor.Supervisor._launch_command(_mapped_track(repo, topic, session))

    _assert_no_tmux_scoping(command)
    assert command == f"claude --dangerously-skip-permissions -n {topic}"


def test_codex_launch_command_carries_no_tmux_scoping():
    command = supervisor.Supervisor._codex_launch_command(
        "019f6a1e-266d-7fc2-8eb2-15ec9d324fb8",
        "read /tmp/repo/plan/topic/handoff.md and follow it",
    )

    _assert_no_tmux_scoping(command)
    assert command.startswith("codex resume --dangerously-bypass-approvals-and-sandbox ")


def test_restart_fires_when_marker_valid_notbusy_idle(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    marker = _arm_ready_marker(repo, topic, mtime=1001.0)

    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "restarting"
    assert (
        "respawn",
        session,
        str(repo),
        f"claude --dangerously-skip-permissions -n {topic}",
    ) in fake.calls
    resume = supervisor.default_resume(str(repo), topic)
    assert resume in fake.paste_texts()
    # the ready marker was deleted AND the injection stamp cleared (round closed, B4)
    assert not marker.exists()
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) is None


def test_no_restart_when_busy_even_with_valid_marker(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture="esc to interrupt\n  Ctx: 30% left\n")  # busy
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _arm_ready_marker(repo, topic, mtime=1001.0)

    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"
    assert not fake.has("respawn")


# --------------------------------------------------------------------------- #
# Background subshell: a live `Bash(run_in_background)` command shell under the
# pane process ⇒ BUSY, suppressing BOTH injection and restart (never respawn -k
# a session with live background work), even when the pane text looks idle.
# --------------------------------------------------------------------------- #


def test_bg_shell_suppresses_restart(tmp_path):
    """Idle-looking pane + VALID ready marker, but a descendant shell in the
    process tree (a live `Bash(run_in_background)` command) ⇒ status `working`
    and NO respawn: the bg-shell makes it busy, so the atomic restart is
    suppressed and the live background work is protected."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))  # empty box → textually idle
    fake.pane_pid_map[session] = 100  # the pane's login-shell PID
    # 100 → 200 (node runtime) → 300 (node MCP server) + 400 (a bg-command shell).
    children = {100: [200], 200: [300, 400]}
    comms = {200: "node", 300: "node", 400: "zsh"}
    sup = _sup(
        tmp_path,
        fake,
        children_of=lambda pid: children.get(pid, []),
        comm_of=comms.get,
    )
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    marker = _arm_ready_marker(repo, topic, mtime=1001.0)  # valid + fresh

    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"  # bg-shell ⇒ busy ⇒ NOT restarted
    assert view.note == "background shell"  # operator sees WHY it isn't idle
    assert not fake.has("respawn")  # the live background work is protected
    assert marker.exists()  # a fresh marker is untouched by the busy void check


def test_no_bg_shell_allows_restart(tmp_path):
    """The counterpart: identical idle pane + valid ready marker, but NO descendant
    shell (only node/MCP) ⇒ the restart proceeds (`restarting`, respawn issued)."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    fake.pane_pid_map[session] = 100
    children = {100: [200], 200: [300]}
    comms = {200: "node", 300: "node"}  # node runtime + MCP server, no shell
    sup = _sup(
        tmp_path,
        fake,
        children_of=lambda pid: children.get(pid, []),
        comm_of=comms.get,
    )
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _arm_ready_marker(repo, topic, mtime=1001.0)

    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "restarting"
    assert (
        "respawn",
        session,
        str(repo),
        f"claude --dangerously-skip-permissions -n {topic}",
    ) in fake.calls


def test_bg_shell_at_danger_is_working_and_never_restarted(tmp_path):
    """A session deep in the danger band whose pane LOOKS idle, but which has a live
    background shell (a `Bash(run_in_background)` build/test still running), reads
    `working` — never `danger`, never restarted. This is the concrete case proving why
    the daemon may not equate "idle + settled" with "safe to kill": the pane text is
    indistinguishable from idle, yet real work is in flight."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=13))  # idle-LOOKING, deep in danger
    fake.pane_pid_map[session] = 100
    children = {100: [200], 200: [300]}
    comms = {200: "node", 300: "bash"}  # a LIVE background shell under the pane process
    sup = _sup(tmp_path, fake, children_of=lambda pid: children.get(pid, []), comm_of=comms.get)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"  # bg shell ⇒ busy; the danger branch is never reached
    assert view.note == "background shell"
    assert not fake.has("respawn")  # the live background work was NOT killed


def test_bg_shell_sets_background_shell_note(tmp_path):
    """When a bg shell is the SOLE reason a pane isn't idle (pane text is idle, no
    blocked marker), the `working` row carries the note `background shell`."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))  # idle, high ctx (no inject)
    fake.pane_pid_map[session] = 100
    children = {100: [200]}
    comms = {200: "bash"}  # a bg-command shell directly under the pane process
    sup = _sup(
        tmp_path,
        fake,
        children_of=lambda pid: children.get(pid, []),
        comm_of=comms.get,
    )
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"
    assert view.note == "background shell"


def test_textually_busy_pane_has_no_background_shell_note(tmp_path):
    """The note is `background shell` ONLY when a bg shell is the SOLE reason. A
    TEXTUALLY busy pane (spinner) is `working` with NO note, even when a descendant
    shell is also present — the note guard is `bg_shell and not is_busy(capture)`."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_busy_capture(ctx=40))  # actively generating
    fake.pane_pid_map[session] = 100
    children = {100: [200]}
    comms = {200: "zsh"}
    sup = _sup(
        tmp_path,
        fake,
        children_of=lambda pid: children.get(pid, []),
        comm_of=comms.get,
    )
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"
    assert view.note is None


def test_fresh_marker_survives_busy_certifying_tail(tmp_path):
    """RB1: a YOUNG ready marker (age < grace) seen busy is the certifying turn's
    OWN tail (final streaming + stop hooks) — it must NOT be voided, else the
    restart never fires. now()=1000, stamp=990, marker mtime=995 → age 5s < grace."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture="esc to interrupt\n  Ctx: 30% left\n")  # busy tail
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 990.0, sup.stamp_path)
    marker = _arm_ready_marker(repo, topic, mtime=995.0)

    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"
    assert marker.exists()  # NOT voided — it is the certifying tail
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) == 990.0


def test_stale_marker_voided_when_busy_past_grace(tmp_path):
    """RB1/B4: an OLD ready marker (age > grace) seen busy means the session
    genuinely resumed work after certifying — void it durably (marker + stamp +
    inject state). now()=1000, stamp=700, marker mtime=800 → age 200s > grace."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture="esc to interrupt\n  Ctx: 30% left\n")  # busy again
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 700.0, sup.stamp_path)
    marker = _arm_ready_marker(repo, topic, mtime=800.0)

    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"
    assert not marker.exists()  # certification voided (stale)
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) is None


def test_void_resets_inject_state_so_round_can_recertify(tmp_path):
    """RB2: after a void, the in-memory inject state is popped AND the durable stamp
    + notified bands are cleared, so the NEXT threshold crossing opens a fresh round
    that writes a new stamp — else the wedged round would never re-certify."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    sup = _sup(tmp_path, fake)
    track = _mapped_track(repo, topic, session)
    # Round 1: inject (stamp written, a band recorded) on an idle low-ctx pane.
    fake.serve(session, repo, capture=_idle_capture(ctx=40))
    sup.evaluate(track, act=True)
    assert _key_for(repo, topic) in sup._inject  # in-memory last_ctx tracked
    assert registry.read_notified_bands(str(repo), topic, sup.stamp_path)  # a band recorded
    # Session resumes work with a STALE marker → void (age > grace) → state popped.
    registry.write_injection_stamp(str(repo), topic, 700.0, sup.stamp_path)
    _arm_ready_marker(repo, topic, mtime=800.0)
    fake.panes[session] = "esc to interrupt\n  Ctx: 30% left\n"  # busy
    sup.evaluate(track, act=True)
    assert _key_for(repo, topic) not in sup._inject  # inject state popped
    # Next idle low-ctx tick opens a FRESH round: new stamp written, re-injected.
    fake.panes[session] = _idle_capture(ctx=35)
    sup.evaluate(track, act=True)
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) == 1000.0


def test_no_restart_when_not_idle(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture="stale scrollback with no prompt box\n")  # not idle, not busy
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _arm_ready_marker(repo, topic, mtime=1001.0)

    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "settling"
    assert not fake.has("respawn")


def test_restart_keeps_marker_when_respawn_fails(tmp_path):
    """B5: a failed respawn must NOT delete the ready marker — the certification
    is preserved so the restart retries, never silently destroyed."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    fake.respawn_ok = False  # respawn fails
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    marker = _arm_ready_marker(repo, topic, mtime=1001.0)

    sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert marker.exists()  # certification preserved
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) == 1000.0
    # and the resume line was NOT pasted (we bailed before submit)
    assert supervisor.default_resume(str(repo), topic) not in fake.paste_texts()


def test_renamed_session_is_idle_and_restarts(tmp_path):
    """B2: a session showing the `-n <topic>` TITLED top border is still detected
    as idle, so injection/restart keep working after the first rename (else every
    daemon-launched session becomes permanently unmanageable)."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30, topic=topic))  # titled border
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _arm_ready_marker(repo, topic, mtime=1001.0)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "restarting"


# --------------------------------------------------------------------------- #
# THE CARDINAL RULE + the ONE tri-state indicator file (maintainer 2026-07-14).
#
# The daemon NEVER restarts a session that has not declared itself `ready`. It never
# infers readiness from a timer or from idleness — "idle + settled" is NOT "safe to
# kill". A session that declares nothing is REPORTED, never killed.
# --------------------------------------------------------------------------- #


def test_idle_at_danger_with_no_declaration_is_never_restarted(tmp_path):
    """THE regression guard for the severe bug. A session idle at 13%, warned, wide past
    any plausible timeout, having declared NOTHING, must be SURFACED and left alone —
    never respawned. A timer cannot know a session is safe to kill."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=13))  # idle, deep in danger, no state
    sup = _sup(tmp_path, fake)
    track = _mapped_track(repo, topic, session)

    for _ in range(20):  # tick and tick and tick — it must NEVER escalate to a kill
        view = sup.evaluate(track, act=True)
    assert view.status == "danger"
    assert not fake.has("respawn")  # the session was NOT killed
    assert not signals.state_path(str(repo), topic).exists()  # daemon wrote nothing


def test_restart_fires_only_on_a_declared_ready(tmp_path):
    """`ready` is the SOLE authorization. Declared → restarted immediately; the state
    file is then cleared so it cannot re-trigger."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    state = _declare(repo, topic, "ready", mtime=1001.0)

    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "restarting"
    assert fake.has("respawn")
    assert supervisor.default_resume(str(repo), topic) in fake.paste_texts()
    assert not state.exists()  # round closed
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) is None


def test_winding_down_ack_suppresses_the_rewarn(tmp_path):
    """A fresh `winding-down` ACK buys patience: the session heard us and is wrapping up,
    so the daemon stops re-warning — it must never keystroke into a session that is
    actively winding down. It is NOT restarted either (only `ready` does that)."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=13))  # would otherwise be `danger`
    sup = _sup(tmp_path, fake)  # now() == 1000.0
    _declare(repo, topic, "winding-down", mtime=1000.0)  # fresh ACK

    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "winding-down"
    assert not fake.has("paste")  # no re-warn pasted into a session that is wrapping up
    assert not fake.has("respawn")  # an ACK is not a restart authorization


def test_stale_winding_down_ack_resumes_escalation_but_still_never_acts(tmp_path):
    """An ACK must not become an infinite stall. Past `_ACK_STALE_AFTER` the daemon
    resumes escalating and reports the track — but it STILL never kills it. The
    escalation is louder words, never a restart."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=13))
    err = _io.StringIO()
    sup = _sup(tmp_path, fake)  # now() == 1000.0
    _declare(repo, topic, "winding-down", mtime=1000.0 - supervisor._ACK_STALE_AFTER - 1)

    with contextlib.redirect_stderr(err):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "danger"  # the stale ACK no longer protects it
    assert fake.has("paste")  # escalation resumed
    assert not fake.has("respawn")  # but STILL never killed
    # The report must NOT conflate "hung mid-wrap-up" with "ignored us" — they need
    # different fixes, and this session DID acknowledge.
    out = err.getvalue()
    assert "ACKNOWLEDGED the wrap-up" in out
    assert "declared NOTHING" not in out


def test_blocked_declaration_is_surfaced_and_never_restarted(tmp_path):
    """`blocked` carries its one-line reason into the row, and the track is never
    keystroked or restarted — a human gate is the one thing the daemon must not touch."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=13))
    sup = _sup(tmp_path, fake)
    _declare(repo, topic, "blocked: waiting on the schema call")

    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "blocked:human"
    assert view.note == "waiting on the schema call"
    assert not fake.has("paste")
    assert not fake.has("respawn")


def test_one_file_cannot_be_both_ready_and_blocked(tmp_path):
    """The reason for ONE file with a VALUE: with two presence-markers, both could exist
    and the precedence was incidental. A single file makes the ambiguity unrepresentable
    — writing `blocked` REPLACES `ready`, so the track is blocked, full stop."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _declare(repo, topic, "ready", mtime=1001.0)
    _declare(repo, topic, "blocked: changed my mind", mtime=1002.0)  # same file, overwritten

    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "blocked:human"
    assert not fake.has("respawn")  # the superseded `ready` cannot restart it


def test_malformed_state_value_is_surfaced_and_never_restarts(tmp_path):
    """A typo'd value must be REPORTED, not silently ignored — and must never be read as
    readiness (fail-closed)."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    err = _io.StringIO()
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _declare(repo, topic, "redy", mtime=1001.0)  # typo

    with contextlib.redirect_stderr(err):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert not fake.has("respawn")  # a typo is NOT a restart authorization
    assert "MALFORMED state file" in err.getvalue()
    assert view.note is not None and "redy" in view.note


def test_every_track_alert_names_the_tmux_session_and_pane(tmp_path):
    """Operator-facing alerts must say WHERE to act: `repo::topic` alone told the
    maintainer WHAT was stuck but not WHERE to go. Every track alert carries the tmux
    session, the pane, and a copy-pasteable jump command."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=13))  # danger, nothing declared
    err = _io.StringIO()
    sup = _sup(tmp_path, fake)

    with contextlib.redirect_stderr(err):
        sup.evaluate(_mapped_track(repo, topic, session), act=True)
    out = err.getvalue()
    assert topic in out
    assert f"tmux session '{session}'" in out
    assert f"pane {session}" in out  # FakeTmux models the pane id as the session name
    assert f"tmux switch-client -t {session}" in out  # the jump command


# --------------------------------------------------------------------------- #
# session-gone (mapped row, session missing).
# --------------------------------------------------------------------------- #


def test_mapped_track_with_missing_session(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()  # session NOT added
    sup = _sup(tmp_path, fake)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "session-gone"
    assert not fake.has("capture")


# --------------------------------------------------------------------------- #
# auto-link: repo-qualified + cwd-verified; refuses a cross-repo session.
# --------------------------------------------------------------------------- #


def test_auto_link_refuses_different_repo(tmp_path):
    repo, topic = _make_plan(tmp_path)
    other_repo = tmp_path / "other-repo"
    other_repo.mkdir()
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.sessions.add(session)
    fake.paths[session] = str(other_repo)  # session cwd is a DIFFERENT repo
    sup = _sup(tmp_path, fake, watch_repos=[str(repo)])

    unassigned = registry.Track.make_unassigned(
        repo=str(repo), topic=topic, handoff=supervisor.default_handoff(str(repo), topic)
    )
    assert sup.auto_link(unassigned) is None
    assert registry.read_mapping(sup.store_path) == []  # nothing linked


def test_auto_link_creates_mapping_when_cwd_in_repo(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.sessions.add(session)
    fake.paths[session] = str(repo / "plan" / topic)  # cwd inside the repo
    sup = _sup(tmp_path, fake, watch_repos=[str(repo)])

    unassigned = registry.Track.make_unassigned(repo=str(repo), topic=topic)
    linked = sup.auto_link(unassigned)
    assert linked is not None
    assert linked.tmux == session
    rows = registry.read_mapping(sup.store_path)
    assert [(r.repo, r.topic) for r in rows] == [(os.path.normpath(str(repo)), topic)]


# --------------------------------------------------------------------------- #
# adopt: pick up live Claude sessions by their registry name (~/.claude/sessions).
# --------------------------------------------------------------------------- #


def _write_session(sessions_dir, pid, *, name, cwd, proc_start="pt", status="idle"):
    payload = {"pid": pid, "name": name, "cwd": str(cwd), "procStart": proc_start, "status": status}
    (sessions_dir / f"{pid}.json").write_text(json.dumps(payload), encoding="utf-8")


def _adopt_sup(tmp_path, fake, sessions_dir, ppid, starttimes, **kwargs):
    return _sup(
        tmp_path,
        fake,
        sessions_dir=str(sessions_dir),
        ppid_of=ppid.get,
        starttime_of=starttimes.get,
        **kwargs,
    )


# --------------------------------------------------------------------------- #
# live-outside-tmux: the mapped tmux session is gone, but a live Claude session
# for the topic is running in a NON-tmux terminal (e.g. a bare SSH shell) — alive
# and working but unmanageable, so NOT the alarming `session-gone`.
# --------------------------------------------------------------------------- #


def test_missing_session_with_live_out_of_tmux_claude_is_live_outside_tmux(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()  # mapped tmux session NOT added → session_exists False; no panes
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    # A live registry session named for the topic, cwd in the repo, whose pid walks up
    # to NO tmux pane (pane_pids empty, ppid chain terminates) → running outside tmux.
    _write_session(sessions_dir, 100, name=topic, cwd=str(repo), status="busy")
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {100: "pt"})
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "live-outside-tmux"
    assert view.note is not None
    assert "OUTSIDE tmux" in view.note
    assert "busy" in view.note  # the session's own self-reported status is surfaced
    assert not fake.has("capture")  # there is no pane to read


def test_missing_session_without_any_live_claude_is_still_session_gone(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    # A live registry session exists, but for a DIFFERENT topic — this track is gone.
    _write_session(sessions_dir, 100, name="some-other-topic", cwd=str(repo), status="busy")
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {100: "pt"})
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "session-gone"


def test_missing_session_with_the_claude_in_a_different_tmux_is_session_gone(tmp_path):
    """A live session for the topic that DOES resolve to a tmux session is a re-mapping
    concern, not out-of-tmux — it stays `session-gone` (this fix is scoped to no-tmux)."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()  # the mapped `session` is gone...
    fake.pane_pids = {4242: "some-other-tmux"}  # ...but the claude pid resolves to a live pane
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    _write_session(sessions_dir, 100, name=topic, cwd=str(repo), status="busy")
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {100: 4242}, {100: "pt"})
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "session-gone"


def test_live_outside_tmux_is_not_an_attention_status():
    """It is informational — the work is fine, just unmanageable — so it must NOT land
    in the NEEDS YOU block."""
    view = supervisor.RowView(
        topic="t",
        repo="/r",
        tmux="s",
        ctx=None,
        status="live-outside-tmux",
        note="live Claude session (pid 100) running OUTSIDE tmux — daemon cannot manage it",
    )
    assert supervisor.needs_attention(view) is False
    assert "live-outside-tmux" not in supervisor.ATTENTION_STATUSES


def test_tty_render_leaves_live_outside_tmux_uncolored(tmp_path):
    """`live-outside-tmux` is informational, not an alarm — it keeps the terminal
    default color (never red like `session-gone`)."""
    sup = _sup(tmp_path, FakeTmux(), out=_TtyOut())
    view = supervisor.RowView(topic="lo", repo="/r", tmux="s", ctx=None, status="live-outside-tmux")
    line = _row_line(_render_of(sup, [view]), "lo")
    assert "\x1b[3" not in line  # no SGR color introducer at all


# --------------------------------------------------------------------------- #
# Claude registry `status` is the AUTHORITATIVE busy signal for an adopted
# Claude session (2026-07-15). Its vocabulary maps cleanly: `busy` (generating /
# in-process sub-agent) and `shell` (live `Bash(run_in_background)`) mean working;
# `idle` / `waiting` (at a prompt) mean not-working. For an adopted session the
# process-tree shell-walk is IGNORED — `status` sees sub-agents the walk missed
# (false-idle) and its `shell` value is a more accurate background-work signal than
# the walk, which false-fired on lingering/transient shells (false-working). The
# walk stays ONLY the runtime-agnostic FALLBACK for a session with no registry
# entry (Codex).
# --------------------------------------------------------------------------- #


def test_registry_busy_marks_working_despite_idle_pane(tmp_path):
    """A session running an in-process sub-agent looks idle — no spinner, no descendant
    shell — but Claude reports itself `busy`. That self-report must mark it `working`."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))  # pane looks idle, high ctx
    sup = _sup(tmp_path, fake)
    sup._claude_status = {session: "busy"}  # Claude's own live self-report
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"
    assert view.note == "sub-agent (Claude busy)"


def test_registry_shell_marks_working_with_background_shell_note(tmp_path):
    """Claude reports `shell` when a live `Bash(run_in_background)` command is running while
    the pane sits at the prompt — the daemon must show `working (background shell)`, so a
    real background dispatch is never mis-read as idle."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))  # pane at the prompt
    sup = _sup(tmp_path, fake)
    sup._claude_status = {session: "shell"}  # Claude: a live background command
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"
    assert view.note == "background shell"


def test_adopted_claude_ignores_the_process_tree_shell_walk(tmp_path):
    """For an adopted Claude session the registry `status` is authoritative and the
    process-tree shell-walk is IGNORED: a lingering `sleep`/poll shell must not mask an
    at-prompt (`waiting`) session as working — the false-positive `working (background
    shell)` bug. (Claude would report `shell`, not `waiting`, if the shell were live work.)"""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))  # idle pane, high ctx
    fake.pane_pid_map[session] = 100
    children = {100: [200]}
    comms = {200: "zsh"}  # a descendant shell the process-walk would flag
    sup = _sup(tmp_path, fake, children_of=lambda pid: children.get(pid, []), comm_of=comms.get)
    sup._claude_status = {session: "waiting"}  # Claude: at a user prompt, not working
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "idle"  # NOT "working" — the process-walk is ignored for Claude
    assert view.note is None


def test_no_registry_status_falls_back_to_process_shell_walk(tmp_path):
    """A session with NO Claude registry entry (Codex / unmapped) falls back to the
    runtime-agnostic process-tree shell-walk — a background shell still marks it working."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))
    fake.pane_pid_map[session] = 100
    children = {100: [200]}
    comms = {200: "bash"}
    sup = _sup(tmp_path, fake, children_of=lambda pid: children.get(pid, []), comm_of=comms.get)
    sup._claude_status = {}  # no registry entry for this session (Codex)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"
    assert view.note == "background shell"


def test_registry_idle_is_idle_even_with_a_stray_descendant_shell(tmp_path):
    """`idle` (nothing pending) is not working; the process-walk is ignored for an adopted
    Claude session, so a stray descendant shell cannot flip it to working."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))
    fake.pane_pid_map[session] = 100
    sup = _sup(
        tmp_path,
        fake,
        children_of=lambda pid: {100: [200]}.get(pid, []),
        comm_of={200: "bash"}.get,
    )
    sup._claude_status = {session: "idle"}
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    # Not "working" — the process-walk is ignored for Claude. (Idle above threshold with
    # no declaration is now nudged to keep going: `idle-with-context-left`, still not busy.)
    assert view.status == "idle-with-context-left"
    assert view.note is None


def test_refresh_claude_status_populates_the_map_from_registry(tmp_path):
    """`build_rows` recomputes `{tmux: status}` from the registry ⋈ tmux each tick, so
    `evaluate` can read a live session's status without a per-track registry read."""
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    _write_session(sessions_dir, 100, name="topic", cwd="/r", status="busy")
    fake = FakeTmux()
    fake.pane_pids[50] = "sA"  # pane PID 50 → tmux session sA
    ppid = {100: 50, 50: 1}  # claude 100 → pane 50
    sup = _adopt_sup(tmp_path, fake, sessions_dir, ppid, {100: "pt"})
    sup._refresh_claude_status()
    assert sup._claude_status == {"sA": "busy"}


def test_adopt_sessions_links_by_registry_name(tmp_path):  # noqa: PLR0915 — see below
    """adopt maps each LIVE Claude session (from ~/.claude/sessions) to a plan when
    its registry `cwd` is in a fleet repo AND its `name` is an active plan topic,
    joined to the tmux session by PID. Registry membership proves it is a claude
    process, so there is no worker-command guard. Non-matches, a session outside
    tmux, a dead PID, and an already-mapped (repo, topic) contribute nothing.

    Over the statement limit (PLR0915) deliberately: the seven session rows below
    are seven DIFFERENT adoption outcomes that must be exercised against a single
    `adopt_sessions()` call, because what is under test is how adoption handles a
    MIXED population in one pass. Splitting them into seven tests would test seven
    homogeneous populations instead, and hoisting the fixture to a module-level
    builder would separate each row from the assertion about it.
    """
    repo_a, _ = _make_plan(tmp_path, repo_name="repo_a", topic="alpha")
    repo_b, _ = _make_plan(tmp_path, repo_name="repo_b", topic="beta")
    (repo_a / "plan" / "gamma").mkdir(parents=True)
    (repo_a / "plan" / "gamma" / "handoff.md").write_bytes(b"h\n")

    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    fake = FakeTmux()
    ppid: dict[int, int] = {}
    starttimes: dict[int, str] = {}

    def live(pid, name, cwd, session, *, in_tmux=True, alive=True):
        _write_session(sessions_dir, pid, name=name, cwd=cwd)
        if alive:
            starttimes[pid] = "pt"  # matches procStart → live
        shell = pid + 1  # the claude PID's parent is its pane's shell
        ppid[pid] = shell
        if in_tmux:
            fake.pane_pids[shell] = session

    live(100, "alpha", repo_a, "sesA")  # ADOPT → repo_a::alpha
    live(200, "beta", repo_b, "sesB")  # ADOPT → repo_b::beta
    live(300, "notaplan", repo_a, "sesN")  # skip: name not an active topic
    live(400, "delta", "/somewhere/else", "sesD")  # skip: cwd not in a fleet repo
    live(500, "gamma", repo_a, "sesG")  # RE-POINT: (repo_a, gamma) mapped but its session MOVED
    live(600, "alpha", repo_a, "sesX", in_tmux=False)  # skip: not inside any tmux pane
    live(700, "gamma", repo_a, "sesDead", alive=False)  # skip: dead PID (starttime mismatch)

    sup = _adopt_sup(
        tmp_path, fake, sessions_dir, ppid, starttimes, watch_repos=[str(repo_a), str(repo_b)]
    )
    registry.append_mapping(
        _mapped_track(repo_a, "gamma", "gamma-existing"), sup.store_path, added_at="pre"
    )

    adopted = sup.adopt_sessions()

    assert sorted((t.repo, t.topic, t.tmux) for t in adopted) == [
        (os.path.normpath(str(repo_a)), "alpha", "sesA"),
        (os.path.normpath(str(repo_b)), "beta", "sesB"),
    ]
    rows = {(r.repo, r.topic): r.tmux for r in registry.read_mapping(sup.store_path)}
    assert rows[(os.path.normpath(str(repo_a)), "alpha")] == "sesA"  # mapped to the SESSION name
    assert rows[(os.path.normpath(str(repo_b)), "beta")] == "sesB"
    # `gamma` was already mapped, but its live named session MOVED (the store recorded
    # `gamma-existing`; the live session now resolves to `sesG`). Adoption RE-POINTS the
    # stale mapping to the current tmux session (R2) rather than freezing it — and it is a
    # re-point, not an adoption, so `gamma` is absent from `adopted` above.
    assert (
        rows[(os.path.normpath(str(repo_a)), "gamma")] == "sesG"
    )  # re-pointed to the live session
    assert (os.path.normpath(str(repo_a)), "notaplan") not in rows  # name not a plan topic
    assert "delta" not in {topic for _repo, topic in rows}  # cwd not in a fleet repo


def test_adopt_sessions_empty_when_no_registry_match(tmp_path):
    """A live registry session in the repo but whose name is NOT an active topic →
    adopt returns [] and writes nothing."""
    repo, _ = _make_plan(tmp_path)  # active topic: "topic"
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    fake = FakeTmux()
    ppid, starttimes = {100: 101}, {100: "pt"}
    fake.pane_pids[101] = "s1"
    _write_session(sessions_dir, 100, name="unrelated-name", cwd=repo)
    sup = _adopt_sup(tmp_path, fake, sessions_dir, ppid, starttimes, watch_repos=[str(repo)])
    assert sup.adopt_sessions() == []
    assert registry.read_mapping(sup.store_path) == []


def test_adopt_is_continuous_across_ticks(tmp_path):
    """adopt runs every tick via build_rows(act=True): a session not yet named as a
    plan topic at one tick is picked up on a LATER tick once its registry name
    matches — the fix for 'the daemon never re-adopted after the prompt cleared'."""
    repo, topic = _make_plan(tmp_path)  # active topic: "topic"
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    fake = FakeTmux()
    ppid, starttimes = {100: 101}, {100: "pt"}
    fake.pane_pids[101] = "s1"

    # Tick 1: session exists (in tmux, in the repo) but is named something else.
    _write_session(sessions_dir, 100, name="scratch", cwd=repo)
    sup = _adopt_sup(tmp_path, fake, sessions_dir, ppid, starttimes, watch_repos=[str(repo)])
    sup.build_rows(act=True)
    assert registry.read_mapping(sup.store_path) == []  # not adopted yet

    # Tick 2: the maintainer renamed it to the plan topic → adopted this tick.
    _write_session(sessions_dir, 100, name=topic, cwd=repo)
    sup.build_rows(act=True)
    rows = {(r.repo, r.topic): r.tmux for r in registry.read_mapping(sup.store_path)}
    assert rows.get((os.path.normpath(str(repo)), topic)) == "s1"


# --------------------------------------------------------------------------- #
# Codex discovery is fully injectable (#6): adopt + refresh route through the
# Supervisor's codex seams, never the real /proc scan or ~/.codex — so the suite
# is hermetic even with a live codex on the host.
# --------------------------------------------------------------------------- #


def test_refresh_and_adopt_route_codex_through_injected_seams(tmp_path):
    """`adopt_sessions` and `_refresh_codex_sessions` must drive Codex discovery through the
    INJECTED seams (`codex_home` / `codex_pids_of_comm` / `codex_fd_targets_of` /
    `codex_cwd_of`), never `codex_sessions`' real `/proc` scan + `~/.codex`. We wire the
    seams to a fully-simulated codex process — pid 9000, holding a rollout whose id the
    injected `~/.codex` index names for our topic — and assert BOTH paths discover it. That
    is impossible unless every reader is the injected one (pid 9000 is not a real process),
    so it proves the threading AND that no real host state is read. Sabotage-verify: drop
    any seam from either supervisor call site and the discovery goes empty."""
    repo, topic = _make_plan(tmp_path, topic="cx")
    fake = FakeTmux()
    fake.pane_pids = {7001: "livespec-cx"}  # the codex pid's pane-pid ancestor → this tmux
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()  # no claude registry files → the claude side contributes nothing
    # An injected ~/.codex whose index names our fake session-id for the topic.
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    (codex_home / "session_index.jsonl").write_text(
        json.dumps({"id": sid, "thread_name": topic}) + "\n", encoding="utf-8"
    )
    # Injected /proc seams describing ONE live codex process (pid 9000) in this repo,
    # each recording its calls so we can assert the injected readers are the ones hit.
    hits = {"pids": [], "fd": [], "cwd": []}

    def _pids(comm):
        hits["pids"].append(comm)
        return [9000] if comm == codex_sessions.CODEX_COMM else []

    def _fd(pid):
        hits["fd"].append(pid)
        return [f"/proc/{pid}/fd/rollout-2026-07-18T00-00-00-{sid}.jsonl"] if pid == 9000 else []

    def _cwd(pid):
        hits["cwd"].append(pid)
        return str(repo) if pid == 9000 else None

    sup = _adopt_sup(
        tmp_path,
        fake,
        sessions_dir,
        {9000: 7001},  # ppid_of: pid 9000's parent is the pane pid 7001 (→ resolves to tmux)
        {},
        watch_repos=[str(repo)],
        codex_home=str(codex_home),
        codex_pids_of_comm=_pids,
        codex_fd_targets_of=_fd,
        codex_cwd_of=_cwd,
    )

    adopted = sup.adopt_sessions()
    assert [(t.topic, t.tmux) for t in adopted] == [(topic, "livespec-cx")]
    assert hits["pids"] and hits["fd"] and hits["cwd"]  # the injected readers were the ones hit

    sup._refresh_codex_sessions()
    live = sup._codex.get(("livespec-cx", topic))
    assert live is not None and live.session_id == sid


# --------------------------------------------------------------------------- #
# archive-GC.
# --------------------------------------------------------------------------- #


def test_archive_gc_drops_archived_row(tmp_path):
    repo = tmp_path / "repo"
    (repo / "plan").mkdir(parents=True)
    fake = FakeTmux()
    sup = _sup(tmp_path, fake)
    registry.append_mapping(
        registry.Track(topic="ghost", repo=str(repo), tmux="repo--ghost"), sup.store_path
    )
    registry.append_mapping(
        registry.Track(topic="live", repo=str(repo), tmux="repo--live"), sup.store_path
    )
    (repo / "plan" / "live").mkdir()  # 'live' still present

    dropped = sup.archive_gc()
    assert dropped == 1
    remaining = {t.topic for t in registry.read_mapping(sup.store_path)}
    assert remaining == {"live"}


def test_archive_gc_keeps_row_when_repo_root_missing(tmp_path):
    """B6: a transiently-unreachable repo ROOT (unmount / mid-move) must NOT drop
    the row and lose its custom overrides — only a plan gone under an EXISTING
    root is a real deletion."""
    missing_repo = tmp_path / "unmounted"  # does not exist
    fake = FakeTmux()
    sup = _sup(tmp_path, fake)
    registry.append_mapping(
        registry.Track(topic="t", repo=str(missing_repo), tmux="unmounted--t", ctx_threshold=30),
        sup.store_path,
    )
    dropped = sup.archive_gc()
    assert dropped == 0
    rows = registry.read_mapping(sup.store_path)
    assert [(r.topic, r.ctx_threshold) for r in rows] == [("t", 30)]  # override preserved


# --------------------------------------------------------------------------- #
# Whole-tick integration: discovery ⋈ mapping renders unassigned + mapped rows.
# --------------------------------------------------------------------------- #


def test_tick_builds_unassigned_and_mapped_rows(tmp_path):
    repo, topic = _make_plan(tmp_path, topic="mapped")
    (repo / "plan" / "unmapped").mkdir(parents=True)
    (repo / "plan" / "unmapped" / "handoff.md").write_text("h\n")
    session = registry.tmux_id(str(repo), "mapped")
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))
    sup = _sup(tmp_path, fake, watch_repos=[str(repo)])
    registry.append_mapping(_mapped_track(repo, "mapped", session), sup.store_path)

    views = sup.tick(act=True)
    by_topic = {v.topic: v for v in views}
    # Idle at 73% (above threshold) with no declaration → nudged to keep going.
    assert by_topic["mapped"].status == "idle-with-context-left"
    assert by_topic["unmapped"].status == "unassigned"
    assert by_topic["unmapped"].tmux is None


def test_list_command_is_read_only(tmp_path):
    """`list` (act=False) must derive status but never inject/restart NOR mutate
    the store (no archive-GC, no auto-link) — B6."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(
        session, repo, capture=_idle_capture(ctx=40)
    )  # below threshold — would warn if acting
    sup = _sup(tmp_path, fake, watch_repos=[str(repo)])
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path)

    views = sup.tick(act=False)
    assert views[0].status == "warned"  # status still derived
    assert not fake.has("paste")  # but NO side effect
    assert not fake.has("respawn")


def test_list_does_not_auto_link_or_gc(tmp_path):
    """B6: a read-only `list` over an unassigned discovered plan must NOT create a
    mapping row (auto-link is a store mutation)."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))
    sup = _sup(tmp_path, fake, watch_repos=[str(repo)])
    # no mapping row appended → discovered plan is unassigned
    sup.tick(act=False)
    assert registry.read_mapping(sup.store_path) == []  # list did NOT auto-link


# --------------------------------------------------------------------------- #
# Reboot recovery (startup-only).
# --------------------------------------------------------------------------- #


def test_recover_recreates_missing_mapped_session(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()  # session absent → must be recreated
    fake.panes[session] = _idle_capture()  # post-launch: empty box so submit confirms
    sup = _sup(tmp_path, fake)
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path)

    recovered = sup.recover_missing_sessions()
    assert recovered == [session]
    assert ("new", session, str(repo)) in fake.calls
    assert (
        "respawn",
        session,
        str(repo),
        f"claude --dangerously-skip-permissions -n {topic}",
    ) in fake.calls
    assert supervisor.default_resume(str(repo), topic) in fake.paste_texts()


def test_recover_skips_when_new_session_fails(tmp_path):
    """Codex re-review #3: if `new-session` fails to create the exact session,
    recovery must NOT proceed to `_do_launch`/`respawn` (which could target a
    prefix-matched live sibling) — it surfaces and skips."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()  # session absent
    fake.new_session_ok = False  # new-session fails to create it
    sup = _sup(tmp_path, fake)
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path)

    recovered = sup.recover_missing_sessions()
    assert recovered == []
    assert not fake.has("respawn")  # never respawned a prefix-matched sibling


# --------------------------------------------------------------------------- #
# Reboot recovery is runtime-dispatched (defect #5): a dead track whose TOPIC names a
# session in the persistent codex index is a CODEX track — resumed via `codex resume <id>`
# (option c) when its rollout survives, else skip+surface (option b), NEVER recreated as
# Claude. A topic absent from the index is a Claude track and recovers as before.
# --------------------------------------------------------------------------- #


def _codex_home_with(tmp_path, topic, session_id, *, rollout=True):
    """A fake ~/.codex naming `session_id` for `topic`, optionally with its rollout on disk."""
    home = tmp_path / "codex-home"
    home.mkdir(exist_ok=True)
    (home / "session_index.jsonl").write_text(
        json.dumps({"id": session_id, "thread_name": topic, "updated_at": "2026-07-18T00:00:00Z"})
        + "\n",
        encoding="utf-8",
    )
    if rollout:
        day = home / "sessions" / "2026" / "07" / "18"
        day.mkdir(parents=True)
        (day / f"rollout-2026-07-18T00-00-00-{session_id}.jsonl").write_text("{}\n")
    return home


def test_recover_resumes_a_codex_track_via_codex_resume(tmp_path):
    """Option (c): a dead track whose topic is in the codex index WITH its rollout on disk is
    resumed by `codex resume <id>` (reattaching the SAME rollout), NEVER the claude command."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    fake = FakeTmux()  # session absent → must be recreated
    sup = _sup(tmp_path, fake, codex_home=str(_codex_home_with(tmp_path, topic, sid)))
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path)

    recovered = sup.recover_missing_sessions()
    assert recovered == [session]
    assert ("new", session, str(repo)) in fake.calls
    expected = supervisor.Supervisor._codex_launch_command(
        sid, supervisor.default_resume(str(repo), topic)
    )
    assert ("respawn", session, str(repo), expected) in fake.calls
    # THE guard: the destructive Claude command is NEVER aimed at a codex track.
    assert not any(c[0] == "respawn" and "claude" in c[3] for c in fake.calls)
    assert not fake.has("paste")  # codex resume auto-submits the kick — no separate paste


def test_recover_skips_and_surfaces_a_codex_track_whose_rollout_is_gone(tmp_path, capsys):
    """Option (b): the topic is in the codex index but its rollout was pruned — codex resume
    cannot reattach, so recovery SKIPS and surfaces it, NEVER recreating it as Claude."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    fake = FakeTmux()
    sup = _sup(
        tmp_path, fake, codex_home=str(_codex_home_with(tmp_path, topic, sid, rollout=False))
    )
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path)

    recovered = sup.recover_missing_sessions()
    assert recovered == []
    assert not fake.has("new")  # never created the session...
    assert not fake.has("respawn")  # ...and never launched anything (no mis-recreate as Claude)
    err = capsys.readouterr().err
    assert topic in err and "rollout is gone" in err and "re-adopt" in err


def test_recover_still_recreates_a_claude_track_as_claude(tmp_path):
    """A topic absent from the codex index (even when OTHER topics are indexed) is a Claude
    track — recovered with the claude command, exactly as before the #5 dispatch."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.panes[session] = _idle_capture()  # post-launch empty box so the resume submit confirms
    # A codex index that names a DIFFERENT topic — the dispatch must not match this track.
    home = _codex_home_with(
        tmp_path, "a-different-codex-topic", "aaaaaaaa-bbbb-cccc-dddd-ffffffffffff"
    )
    sup = _sup(tmp_path, fake, codex_home=str(home))
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path)

    recovered = sup.recover_missing_sessions()
    assert recovered == [session]
    # Build the expected from `_launch_command` (parallel to the codex test's use of
    # `_codex_launch_command`) so this stays correct through any future change to
    # how `_launch_command` shapes the spawn — no hardcoded command string to drift.
    expected = supervisor.Supervisor._launch_command(_mapped_track(repo, topic, session))
    assert ("respawn", session, str(repo), expected) in fake.calls


# --------------------------------------------------------------------------- #
# B7: one bad input must NOT kill the whole loop.
# --------------------------------------------------------------------------- #


def test_run_loop_survives_a_tick_exception(tmp_path):
    """B7: a tick that raises is logged and the loop CONTINUES (here `once=True`
    returns after the single, survived tick rather than propagating)."""
    fake = FakeTmux()
    sup = _sup(tmp_path, fake)

    def boom(*, act):
        raise RuntimeError("bad plan dir")

    sup.tick = boom  # type: ignore[assignment]
    sup.run(once=True)  # must NOT raise


# --------------------------------------------------------------------------- #
# Startup gate: Linux + tmux is a DECLARED REQUIREMENT (D4) — refuse, don't crash.
# --------------------------------------------------------------------------- #


def test_supported_host_yields_no_reasons(tmp_path):
    """The happy path: an existing /proc and a resolvable tmux == zero reasons."""
    sup = _sup(tmp_path, FakeTmux())
    assert sup.unsupported_host_reasons() == []


def test_absent_proc_is_an_unsupported_host(tmp_path):
    """macOS has no /proc AT ALL, and both session readers parse /proc/<pid>/ — so a
    missing proc_root is a declared-precondition failure, named as such."""
    sup = _sup(tmp_path, FakeTmux(), proc_root=str(tmp_path / "no-such-proc"))
    reasons = sup.unsupported_host_reasons()
    assert len(reasons) == 1
    assert "/proc" in reasons[0] and "Linux is required" in reasons[0]


def test_absent_tmux_is_an_unsupported_host(tmp_path):
    """Every acting mechanic shells out to a real tmux, so tmux-off-PATH is fatal."""
    sup = _sup(tmp_path, FakeTmux(), which=lambda _name: None)
    reasons = sup.unsupported_host_reasons()
    assert len(reasons) == 1
    assert "tmux is not on PATH" in reasons[0]


def test_the_gate_asks_about_tmux_by_its_real_name(tmp_path):
    """The gate must ask `which` about the literal 'tmux', NOT a caller's injected
    tmux_bin: it answers 'is this host supported at all?', and the beside-tests' fake
    tmux must never be able to satisfy it."""
    asked: list[str] = []
    sup = _sup(tmp_path, FakeTmux(), which=lambda name: asked.append(name) or "/usr/bin/tmux")
    _ = sup.unsupported_host_reasons()
    assert asked == ["tmux"]


def test_run_refuses_on_an_unsupported_host_before_ticking(tmp_path):
    """The refusal mirrors the gitignore gate: surface an actionable reason and return
    from run() BEFORE any tick — an obscure FileNotFoundError several ticks deep is
    exactly what declaring the precondition exists to prevent."""
    repo, _topic = _make_plan(tmp_path)
    err = _io.StringIO()
    sup = _sup(
        tmp_path,
        FakeTmux(),
        watch_repos=[str(repo)],
        gitignore_check=lambda _r: True,
        which=lambda _name: None,
    )
    ticked: list[bool] = []
    sup.tick = lambda *, act: ticked.append(act)  # type: ignore[assignment]  # spy
    with contextlib.redirect_stderr(err):
        sup.run(once=True)
    assert ticked == []  # NO tick ran
    assert "refusing to start: unsupported host" in err.getvalue()


def test_the_host_gate_precedes_the_gitignore_gate(tmp_path):
    """Ordering matters: an unsupported host is the more fundamental failure, so it is
    reported even when a watched repo ALSO has an ungitignored tmp/overseer/. Reporting
    the gitignore offence first would send the operator to fix the wrong thing."""
    repo, _topic = _make_plan(tmp_path)
    err = _io.StringIO()
    sup = _sup(
        tmp_path,
        FakeTmux(),
        watch_repos=[str(repo)],
        gitignore_check=lambda _r: False,  # ALSO an offender
        which=lambda _name: None,
    )
    with contextlib.redirect_stderr(err):
        sup.run(once=True)
    assert "unsupported host" in err.getvalue()
    assert "NOT gitignored" not in err.getvalue()


# --------------------------------------------------------------------------- #
# Startup gate: tmp/overseer/ MUST be gitignored, else the daemon refuses to start.
# --------------------------------------------------------------------------- #


def test_run_refuses_when_tmp_not_gitignored(tmp_path):
    """New startup gate: if a watched repo's tmp/overseer/ is NOT gitignored, the
    daemon surfaces 'refusing to start' and returns from run() BEFORE ticking — the
    overseer writes markers there and must never dirty a tracked tree."""
    repo, _topic = _make_plan(tmp_path)
    fake = FakeTmux()
    sup = _sup(tmp_path, fake, watch_repos=[str(repo)], gitignore_check=lambda _r: False)
    assert sup.unignored_tmp_repos() == [os.path.normpath(str(repo))]
    ticked: list[bool] = []
    sup.tick = lambda *, act: ticked.append(act)  # type: ignore[assignment]  # spy
    sup.run(once=True)  # refuses before acquiring the lock or ticking
    assert ticked == []  # NO tick ran


def test_run_proceeds_when_tmp_gitignored(tmp_path):
    """Counterpart: when every watched repo's tmp/overseer/ IS gitignored the gate
    passes and run(once=True) performs a single normal act=True tick."""
    repo, _topic = _make_plan(tmp_path)
    fake = FakeTmux()
    sup = _sup(tmp_path, fake, watch_repos=[str(repo)], gitignore_check=lambda _r: True)
    assert sup.unignored_tmp_repos() == []
    ticked: list[bool] = []
    sup.tick = lambda *, act: ticked.append(act)  # type: ignore[assignment]  # spy
    sup.run(once=True)
    assert ticked == [True]  # proceeded to exactly one act=True tick


# --------------------------------------------------------------------------- #
# CLI mapping edits.
# --------------------------------------------------------------------------- #


def _isolate_store(tmp_path, monkeypatch):
    """Redirect the hard-coded mapping store at a tmp file.

    The de-gold-plated CLI (2026-07-13) no longer exposes ``--store``; the path is
    fixed to ``registry.DEFAULT_STORE_PATH``. Tests point that module default at a
    tmp file so a CLI ``main([...])`` never writes into the developer's real
    ``~/.livespec-overseer.jsonl``.
    """
    store = tmp_path / "map.jsonl"
    monkeypatch.setattr(registry, "DEFAULT_STORE_PATH", store)
    # `add`/`start` now consult the real fleet manifest to detect cross-repo topic
    # collisions (for the single-dash prefix). Neutralize that read by default so a
    # CLI test is hermetic and never flakes on the host's actual fleet; a collision
    # test overrides this with its own set.
    monkeypatch.setattr(supervisor, "_cli_colliding", lambda: frozenset())
    return store


def test_cli_add_remove_roundtrip(tmp_path, monkeypatch):
    store = _isolate_store(tmp_path, monkeypatch)
    repo = str(tmp_path / "repo")
    assert supervisor.main(["add", "--repo", repo, "--topic", "alpha"]) == 0
    rows = registry.read_mapping(store)
    assert [(r.topic, r.tmux) for r in rows] == [("alpha", registry.tmux_id(repo, "alpha"))]

    assert supervisor.main(["add", "--repo", repo, "--topic", "alpha"]) == 0
    assert len(registry.read_mapping(store)) == 1

    assert supervisor.main(["remove", "--repo", repo, "--topic", "alpha"]) == 0
    assert registry.read_mapping(store) == []


def test_cli_add_names_a_bare_topic_by_default(tmp_path, monkeypatch):
    # With no cross-repo collision, `add` maps the session to the BARE topic name.
    store = _isolate_store(tmp_path, monkeypatch)
    repo = str(tmp_path / "livespec")
    assert supervisor.main(["add", "--repo", repo, "--topic", "autonomous-mode"]) == 0
    rows = registry.read_mapping(store)
    assert [(r.topic, r.tmux) for r in rows] == [("autonomous-mode", "autonomous-mode")]


def test_cli_add_single_dash_prefixes_a_cross_repo_collision(tmp_path, monkeypatch):
    # When the topic collides across repos, `add` repo-qualifies it as `<slug>-<topic>`
    # with a SINGLE dash (the daemon derives the identical name).
    store = _isolate_store(tmp_path, monkeypatch)
    monkeypatch.setattr(supervisor, "_cli_colliding", lambda: frozenset({"shared"}))
    repo = str(tmp_path / "livespec")
    assert supervisor.main(["add", "--repo", repo, "--topic", "shared"]) == 0
    assert supervisor.main(["add", "--repo", repo, "--topic", "solo"]) == 0
    rows = {r.topic: r.tmux for r in registry.read_mapping(store)}
    assert rows["shared"] == "livespec-shared"  # colliding -> repo-qualified
    assert rows["solo"] == "solo"  # non-colliding -> bare


def test_build_rows_caches_the_cross_repo_collision_set(tmp_path):
    # Two watched repos share topic "shared"; each also carries a unique topic. After a
    # tick's build_rows, the daemon caches exactly the cross-repo topic, and `_session_of`
    # repo-qualifies ONLY that one — per repo, single dash — leaving the unique ones bare.
    r1, _ = _make_plan(tmp_path, repo_name="livespec", topic="shared")
    _make_plan(tmp_path, repo_name="livespec", topic="solo-a")
    r2, _ = _make_plan(tmp_path, repo_name="other", topic="shared")
    _make_plan(tmp_path, repo_name="other", topic="solo-b")
    sessions = tmp_path / "sess"
    sessions.mkdir()
    sup = _sup(
        tmp_path,
        FakeTmux(),
        watch_repos=[str(r1), str(r2)],
        sessions_dir=str(sessions),
    )
    rows = sup.build_rows(act=False)
    assert sup._colliding == frozenset({"shared"})
    derived = {(r.repo, r.topic): sup._session_of(r) for r in rows}
    assert derived[(str(r1), "shared")] == "livespec-shared"
    assert derived[(str(r2), "shared")] == "other-shared"
    assert derived[(str(r1), "solo-a")] == "solo-a"
    assert derived[(str(r2), "solo-b")] == "solo-b"


def test_cli_unassign_is_remove(tmp_path, monkeypatch):
    store = _isolate_store(tmp_path, monkeypatch)
    repo = str(tmp_path / "repo")
    supervisor.main(["add", "--repo", repo, "--topic", "beta"])
    assert supervisor.main(["unassign", "--repo", repo, "--topic", "beta"]) == 0
    assert registry.read_mapping(store) == []


def test_start_refuses_running_claude_without_force(tmp_path, monkeypatch):
    """B8: `start` on a session already running a live Claude must NOT respawn-kill
    it — it upserts the mapping and reports; only --force respawns."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    store = _isolate_store(tmp_path, monkeypatch)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture())

    monkeypatch.setattr(supervisor.tmuxio, "TmuxIO", lambda: fake)
    rc = supervisor.main(["start", "--repo", str(repo), "--topic", topic])
    assert rc == 0
    assert not fake.has("respawn")  # the live session was NOT killed
    # but the mapping was upserted
    assert [(r.topic) for r in registry.read_mapping(store)] == [topic]


def test_start_force_respawns_running_claude(tmp_path, monkeypatch):
    """B8: --force DOES respawn a running session (the explicit escape hatch)."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    _isolate_store(tmp_path, monkeypatch)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture())

    monkeypatch.setattr(supervisor.tmuxio, "TmuxIO", lambda: fake)
    rc = supervisor.main(["start", "--force", "--repo", str(repo), "--topic", topic])
    assert rc == 0
    assert fake.has("respawn")


def test_cli_surface_has_no_config_knobs(tmp_path, monkeypatch):
    """The de-gold-plated track-management CLI: the removed --store/--stamp/--repos/
    --repos-only/--manifest flags and the old positional repo/topic are all
    rejected; --repo/--topic are required keyword flags; and `daemon` is NO LONGER
    a subcommand (it is the dedicated `overseerd` executable)."""
    _isolate_store(tmp_path, monkeypatch)
    repo = str(tmp_path / "repo")
    # Removed store / stamp knobs and the retired `daemon` subcommand are all
    # unrecognized now (argparse exits nonzero).
    rejected = (
        ["add", "--store", str(tmp_path / "x"), "--repo", repo, "--topic", "t"],
        ["add", "--repo", repo, "--topic", "t", "--stamp", str(tmp_path / "x")],
        ["list", "--store", str(tmp_path / "x")],
        ["daemon"],  # retired subcommand: the daemon is now the overseerd executable
        ["daemon", "--repos", repo],
    )
    for argv in rejected:
        with pytest.raises(SystemExit):
            supervisor.main(argv)
    # The old positional form is gone; --repo and --topic are required.
    for argv in (["add", repo, "t"], ["add", "--repo", repo], ["start", "--topic", "t"]):
        with pytest.raises(SystemExit):
            supervisor.main(argv)


def test_run_daemon_uses_fleet_defaults(monkeypatch):
    """`run_daemon()` (the overseerd entrypoint) starts the fleet daemon with the
    fixed defaults: the module loop interval, no single-tick, no startup recovery
    (surface-only — the daemon never auto-spawns/revives at startup)."""
    seen: dict[str, object] = {}

    class _RunOnlySup:
        def run(self, *, interval, once, recover):
            seen["args"] = (interval, once, recover)

    monkeypatch.setattr(supervisor, "_build_supervisor", lambda: _RunOnlySup())
    assert supervisor.run_daemon() == 0
    assert seen["args"] == (supervisor.LOOP_INTERVAL_SECONDS, False, False)


def test_run_daemon_threads_warn_percent(monkeypatch):
    """run_daemon(warn_percent=N) sets the built Supervisor's warn_percent field;
    None falls back to registry.DEFAULT_CTX_THRESHOLD."""
    seen: list[int] = []

    class _Sup:
        warn_percent = registry.DEFAULT_CTX_THRESHOLD

        def run(self, *, interval, once, recover):
            seen.append(self.warn_percent)

    monkeypatch.setattr(supervisor, "_build_supervisor", lambda: _Sup())
    assert supervisor.run_daemon(warn_percent=30) == 0
    assert seen == [30]
    assert supervisor.run_daemon() == 0  # None → the built-in default
    assert seen == [30, registry.DEFAULT_CTX_THRESHOLD]


def _load_overseerd():
    path = Path(supervisor.__file__).resolve().parent / "overseerd"
    loader = importlib.machinery.SourceFileLoader("overseerd_exe", str(path))
    spec = importlib.util.spec_from_loader("overseerd_exe", loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)  # the __main__ guard keeps this side-effect-free
    return mod


def test_overseerd_threads_and_validates_warn_percent(monkeypatch):
    """The overseerd executable parses --warn-percent (int in [1, 99]) and threads
    it into run_daemon; a missing flag passes None; out-of-range / non-int argv is
    rejected by argparse (SystemExit)."""
    mod = _load_overseerd()
    seen: dict[str, object] = {}

    def _fake_run(warn_percent=None):
        seen["wp"] = warn_percent
        return 0

    monkeypatch.setattr(mod.supervisor, "run_daemon", _fake_run)
    assert mod.main(["--warn-percent", "30"]) == 0
    assert seen["wp"] == 30
    assert mod.main([]) == 0
    assert seen["wp"] is None
    for bad in (["--warn-percent", "0"], ["--warn-percent", "100"], ["--warn-percent", "x"]):
        with pytest.raises(SystemExit):
            mod.main(bad)


def test_overseerd_executable_is_the_daemon_entrypoint():
    """The dedicated `overseerd` executable sits beside supervisor.py, is
    executable, carries the uv self-invoking shebang, and delegates to
    `supervisor.run_daemon` — the daemon is a dedicated executable, NOT a
    subcommand."""
    overseerd = Path(supervisor.__file__).resolve().parent / "overseerd"
    assert overseerd.is_file(), "overseerd must sit beside supervisor.py"
    assert os.access(overseerd, os.X_OK), "overseerd must be executable (chmod +x)"
    body = overseerd.read_text(encoding="utf-8")
    assert body.startswith(
        "#!/usr/bin/env -S uv run --script --no-project\n"
    ), "overseerd must carry the uv self-invoking shebang on line 1"
    assert "supervisor.run_daemon(" in body, "overseerd must delegate to run_daemon()"


def test_wrapup_message_names_the_one_state_file_and_all_three_values():
    """The wrap-up must hand the session the SINGLE state file and all three legal
    values, plus the handoff it will be resumed from. Only tmp/ paths — never a state
    file under plan/."""
    msg = supervisor.wrapup_message(remaining=40, repo="/r", topic="t")
    assert "40%" in msg
    assert "/r/tmp/overseer/t/.overseer-state" in msg  # the ONE indicator file
    for token in ("winding-down", "ready", "blocked:"):
        assert token in msg
    assert "/r/plan/t/handoff.md" in msg  # the resume target is named explicitly
    assert "/r/plan/t/.overseer-state" not in msg  # never under plan/
    # The retired two-file protocol is GONE from the message.
    assert ".overseer-ready" not in msg
    assert ".overseer-blocked" not in msg


def test_wrapup_message_says_only_the_session_authorizes_the_restart():
    """The cardinal rule must be in the message the session actually reads: it is
    restarted only when IT says `ready`, and writing nothing gets it reported — not
    killed. (The old text promised an unconditional force-restart; that was the bug.)"""
    msg = supervisor.wrapup_message(remaining=13, repo="/r", topic="t")
    assert "ONLY when YOU say so" in msg
    assert "never kills a session" in msg
    assert "not responding" in msg  # writing nothing ⇒ reported to a human


def test_wrapup_message_tells_the_session_to_commit_the_handoff_via_a_worktree():
    """Writing the handoff to disk is NOT saving it (plan/archive/plan-thread-integrity/, W4).

    The wrap-up used to say only "UPDATE {handoff}", and the word "commit" appeared
    nowhere in this file — the "persisted is durable" conflation, sitting in the one
    instruction every overseer-managed wind-down receives. A handoff was left dirty on
    2026-07-19 and rescued only by luck.

    A bare "commit it" would be worse than useless: the handoff lives in the PRIMARY
    checkout, where the commit-refuse hook rejects commits, and a fresh worktree does
    NOT contain the dirty edits. So the text must name the whole path INCLUDING the
    copy step, or a low-context session strands itself at "my worktree is empty".
    """
    msg = supervisor.wrapup_message(remaining=40, repo="/data/projects/livespec", topic="t")
    assert "COMMIT" in msg
    assert "NOT saving it" in msg
    # The refusal the session would otherwise walk into, and why a worktree is needed.
    assert "commit-refuse hook rejects it" in msg
    # The copy step — the part a "just use a worktree" instruction leaves out.
    assert "worktree add" in msg
    assert 'cp /data/projects/livespec/plan/t/handoff.md "$W/plan/t/handoff.md"' in msg
    # The bypasses it must NOT offer as an escape.
    assert "Never pass --no-verify" in msg
    assert "do not discard the file" in msg


def test_wrapup_escalates_from_suggestion_to_insistence():
    """The maintainer's escalation: a SUGGESTION while there is still room (50/40),
    turning INSISTENT at 30/20/10. Re-sending identical text five times is repetition,
    not escalation — and with no force-restart, this escalation IS the lever."""
    for gentle in (50, 40):
        msg = supervisor.wrapup_message(remaining=gentle, repo="/r", topic="t")
        assert "Please start wrapping up" in msg
        assert "STOP AND WIND DOWN NOW" not in msg
    for insistent in (30, 20, 10):
        msg = supervisor.wrapup_message(remaining=insistent, repo="/r", topic="t")
        assert "STOP AND WIND DOWN NOW" in msg
        assert "Please start wrapping up" not in msg


def test_streaming_pane_is_working_not_idle(tmp_path):
    """LIVE-EXERCISE regression: the real TUI shows NO persistent busy spinner
    while streaming, so a single frame looks idle. The settled-delta must catch
    the change between captures and classify it `working` — never injecting
    despite ctx below threshold."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo)
    fake.panes[session] = [
        _idle_capture(ctx=40, body="line one"),
        _idle_capture(ctx=40, body="line one two"),
        _idle_capture(ctx=40, body="line one two three"),
    ]
    sup = _sup(tmp_path, fake, watch_repos=[str(repo)])
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "working"
    assert not fake.has("paste")  # never injected despite ctx 40 <= the default 50


def test_settled_idle_pane_still_injects(tmp_path):
    """Counterpart: an idle pane NOT changing between the two settled captures
    (same frame every call) is still eligible to inject at/below threshold."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=40))  # identical frames → settled
    sup = _sup(tmp_path, fake, watch_repos=[str(repo)])
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "warned"
    assert fake.has("paste")  # settled idle + low ctx → wrap-up injected


def test_submit_prompt_resends_enter_until_box_clears(tmp_path):
    """LIVE-EXERCISE regression: a freshly-respawned session can DROP the first
    Enter while still drawing its welcome screen. `_submit_prompt` re-sends Enter
    until the empty box returns, and returns True on success."""
    fake = FakeTmux()
    session = "s"
    fake.sessions.add(session)
    not_ready = "❯ read handoff.md and follow it\n" + ("─" * 40) + "\nwelcome screen\n"
    fake.panes[session] = [not_ready, not_ready, _idle_capture()]  # 3rd frame = empty box
    sup = _sup(tmp_path, fake)
    assert sup._submit_prompt(session, "read handoff.md and follow it") is True
    enters = [c for c in fake.calls if c[0] == "keys" and c[2] == "Enter"]
    assert len(enters) == 3  # dropped twice, submitted on the third
    assert fake.paste_texts() == ["read handoff.md and follow it"]  # pasted once


def test_submit_prompt_returns_false_on_failed_paste(tmp_path):
    """B5: a failed bracketed paste is a hard False — never a false 'submitted'."""
    fake = FakeTmux()
    session = "s"
    fake.sessions.add(session)
    fake.panes[session] = _idle_capture()
    fake.paste_ok = False
    sup = _sup(tmp_path, fake)
    assert sup._submit_prompt(session, "hello") is False
    assert not any(c[0] == "keys" for c in fake.calls)  # no Enter sent after a failed paste


def test_submit_prompt_single_enter_when_already_ready(tmp_path):
    """On a steady session (empty box every capture) a single Enter suffices."""
    fake = FakeTmux()
    session = "s"
    fake.sessions.add(session)
    fake.panes[session] = _idle_capture()  # empty box → input_box_ready True at once
    sup = _sup(tmp_path, fake)
    assert sup._submit_prompt(session, "hello") is True
    enters = [c for c in fake.calls if c[0] == "keys" and c[2] == "Enter"]
    assert len(enters) == 1


# --------------------------------------------------------------------------- #
# The `NEEDS YOU` attention block (the daemon owns "what needs attention?").
#
# The bottom pane is an LLM: it prints text ONCE and that text then ages silently,
# so it reported tracks that had been resolved for minutes. Current state therefore
# belongs to the daemon's re-rendered table, which is free and cannot go stale.
# --------------------------------------------------------------------------- #


def _render_of(sup, views):
    """Render VIEWS and return what the daemon printed (the table + attention block)."""
    sup.render(views)
    return sup.out.getvalue()


def test_table_header_column_order(tmp_path):
    """Column order is Status · Topic · tmux · Ctx% · Repo — Status leads, the column the
    operator scans first (maintainer 2026-07-15)."""
    fake = FakeTmux()
    sup = _sup(tmp_path, fake)
    out = _render_of(sup, [])
    header = next(ln for ln in out.splitlines() if "Status" in ln and "Topic" in ln)
    assert header.split() == ["Status", "Topic", "tmux", "Ctx%", "Repo"]


def test_table_row_cells_follow_the_header_order(tmp_path):
    """A rendered row places each value under its (reordered) header."""
    fake = FakeTmux()
    sup = _sup(tmp_path, fake)
    view = supervisor.RowView(
        topic="mytopic", repo="/data/projects/livespec", tmux="sess", ctx=42, status="idle"
    )
    out = _render_of(sup, [view])
    row = next(ln for ln in out.splitlines() if "mytopic" in ln)
    assert row.split() == ["idle", "mytopic", "sess", "42%", "livespec"]


# --------------------------------------------------------------------------- #
# The `tmux` column annotates the session name with its RUNTIME — `livespec
# (claude)` / `livespec1 (codex)` — so the operator can tell at a glance whether a
# track is a Claude or a Codex session (maintainer 2026-07-18). Only a row with a
# LIVE MANAGED pane carries a runtime; the no-managed-pane rows (`unassigned` /
# `session-gone` / `live-outside-tmux`) render a bare `—` with no `(...)`. The
# annotation is part of the CELL, so the column width is computed from it and
# alignment holds.
# --------------------------------------------------------------------------- #


def _cell_row(out, topic):
    """The single rendered DATA line for TOPIC (skipping the header row)."""
    return next(ln for ln in out.splitlines() if topic in ln and "Topic" not in ln)


def test_tmux_column_annotates_a_claude_row_with_its_runtime(tmp_path):
    """A row with a live Claude pane renders its tmux cell as `<tmux> (claude)`."""
    sup = _sup(tmp_path, FakeTmux())
    view = supervisor.RowView(
        topic="wk", repo="/r", tmux="livespec", ctx=50, status="working", runtime="claude"
    )
    line = _cell_row(_render_of(sup, [view]), "wk")
    assert "livespec (claude)" in line


def test_tmux_column_annotates_a_codex_row_with_its_runtime(tmp_path):
    """A row with a live Codex pane renders its tmux cell as `<tmux> (codex)`."""
    sup = _sup(tmp_path, FakeTmux())
    view = supervisor.RowView(
        topic="cx", repo="/r", tmux="livespec1", ctx=70, status="idle", runtime="codex"
    )
    line = _cell_row(_render_of(sup, [view]), "cx")
    assert "livespec1 (codex)" in line


def test_tmux_column_is_a_bare_dash_with_no_runtime_for_no_pane_rows(tmp_path):
    """`unassigned` and `session-gone` have no live session — their tmux cell is a bare
    `—`, never a `(...)` annotation (both carry `tmux=None` and `runtime=None`)."""
    sup = _sup(tmp_path, FakeTmux())
    for topic, status in (("un", "unassigned"), ("sg", "session-gone")):
        view = supervisor.RowView(topic=topic, repo="/r", tmux=None, ctx=None, status=status)
        line = _cell_row(_render_of(sup, [view]), topic)
        assert "—" in line
        assert "(" not in line  # no runtime annotation, and no note to add parens


def test_tmux_runtime_annotation_preserves_column_alignment(tmp_path):
    """Column invariant 1: the tmux column width is computed from the ANNOTATED cell
    (`livespec (claude)`), so a short bare-`—` cell is padded to that same width and the
    following Repo column still lines up."""
    sup = _sup(tmp_path, FakeTmux())
    views = [
        supervisor.RowView(
            topic="alpha",
            repo="/x/repoZZ",
            tmux="livespec",
            ctx=50,
            status="working",
            runtime="claude",
        ),
        supervisor.RowView(topic="beta", repo="/x/repoZZ", tmux=None, ctx=60, status="unassigned"),
    ]
    out = _render_of(sup, views)
    wide = _cell_row(out, "alpha")  # tmux cell "livespec (claude)" sets the column width
    narrow = _cell_row(out, "beta")  # tmux cell "—" padded to that same width
    # Both rows share a repo slug; if the column is aligned it starts at the same index.
    assert wide.index("repoZZ") == narrow.index("repoZZ")


def test_evaluate_derives_claude_runtime_and_annotates_the_tmux_cell(tmp_path):
    """END-TO-END: `evaluate` derives `runtime="claude"` for a live Claude track (no
    `_codex` entry → `is_codex` False), and the rendered tmux cell reads `<session>
    (claude)`. Sabotage target: drop `runtime=runtime` on evaluate's final RowView and
    the cell falls back to the bare session name → this goes red."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=80))  # a live Claude idle pane
    sup = _sup(tmp_path, fake)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=False)
    assert view.runtime == "claude"
    line = _cell_row(_render_of(sup, [view]), topic)
    assert f"{session} (claude)" in line


def test_evaluate_derives_codex_runtime_and_annotates_the_tmux_cell(tmp_path):
    """END-TO-END: `evaluate` derives `runtime="codex"` for a track adopted in `_codex`
    on a `bun` pane, and the rendered tmux cell reads `<session> (codex)`. Sabotage
    target for the Codex arm (route it to `"claude"` and this goes red)."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_codex_idle_capture(ctx=80, topic=topic), cmd="bun")
    sup = _sup(tmp_path, fake)
    # `_codex` is keyed by (tmux_session, name) so two codex sessions can share a tmux
    # session (fix a24e3e13) — key this fixture the same way the other codex tests do.
    sup._codex = {
        (session, topic): codex_sessions.CodexSession(
            pid=4242, name=topic, cwd=str(repo), session_id="019f6a1e-266d-7fc2-8eb2-15ec9d324fb8"
        )
    }
    view = sup.evaluate(_mapped_track(repo, topic, session), act=False)
    assert view.runtime == "codex"
    line = _cell_row(_render_of(sup, [view]), topic)
    assert f"{session} (codex)" in line


def test_evaluate_leaves_runtime_none_for_a_session_gone_row(tmp_path):
    """A track whose mapped tmux session is gone (and no live Claude for the topic) is
    `session-gone`: no pane, so no runtime — the rendered tmux cell is a bare `—`."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()  # the mapped session is NOT served → session_exists False
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()  # empty registry → no live Claude anywhere → session-gone
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {})
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "session-gone"
    assert view.tmux is None
    assert view.runtime is None
    line = _cell_row(_render_of(sup, [view]), topic)
    assert "—" in line
    assert "(claude)" not in line and "(codex)" not in line


def test_evaluate_leaves_runtime_none_for_an_unassigned_row(tmp_path):
    """An unassigned plan (no mapping) never has a pane, so it carries no runtime — the
    `unassigned` branch returns before any runtime is derived."""
    repo, topic = _make_plan(tmp_path)
    sup = _sup(tmp_path, FakeTmux())
    track = registry.Track.make_unassigned(repo=str(repo), topic=topic)
    view = sup.evaluate(track, act=True)
    assert view.status == "unassigned"
    assert view.runtime is None


def test_attention_block_annotates_the_tmux_coordinate_with_the_runtime(tmp_path):
    """The NEEDS YOU block's `tmux:` coordinate is annotated the SAME way the table is,
    so the operator knows whether they are jumping into a Claude or Codex pane. The jump
    command itself stays the bare session name (`tmux switch-client -t` takes no runtime)."""
    fake = FakeTmux()
    sup = _sup(tmp_path, fake)
    view = supervisor.RowView(
        topic="autonomous-mode",
        repo="/data/projects/livespec",
        tmux="livespec-autonomous-mode",
        ctx=41,
        status="blocked:human",
        note="waiting on a decision",
        runtime="codex",
    )
    out = _render_of(sup, [view])
    assert "tmux: livespec-autonomous-mode (codex)" in out
    assert "jump: tmux switch-client -t livespec-autonomous-mode" in out  # bare name


def test_attention_block_lists_a_blocked_track_with_its_jump_command(tmp_path):
    """The block must be a SUFFICIENT handover on its own: what is stuck, and where to go."""
    fake = FakeTmux()
    sup = _sup(tmp_path, fake)
    views = [
        supervisor.RowView(
            topic="autonomous-mode",
            repo="/data/projects/livespec",
            tmux="livespec-autonomous-mode",
            ctx=41,
            status="blocked:human",
            note="waiting on a cost-gate decision",
        )
    ]
    out = _render_of(sup, views)
    assert "NEEDS YOU (1):" in out
    # LABELED coordinates, tmux INCLUDED — the operator must not have to guess which
    # unlabeled token is the topic vs the repo vs the session to jump to.
    assert "topic: autonomous-mode | tmux: livespec-autonomous-mode | repo: livespec" in out
    assert "waiting on a cost-gate decision" in out
    assert "jump: tmux switch-client -t livespec-autonomous-mode" in out


def test_attention_block_says_nothing_when_every_track_is_healthy(tmp_path):
    """An empty block must SAY it is empty — silence is ambiguous with a broken render."""
    fake = FakeTmux()
    sup = _sup(tmp_path, fake)
    views = [
        supervisor.RowView(topic="a", repo="/r", tmux="s1", ctx=80, status="idle"),
        supervisor.RowView(topic="b", repo="/r", tmux="s2", ctx=60, status="working"),
    ]
    out = _render_of(sup, views)
    assert "NEEDS YOU: nothing" in out


def test_attention_block_excludes_unassigned_plans(tmp_path):
    """`unassigned` is startable, not stuck — and there are dozens. Including them would
    bury the rows that genuinely want the operator, which is the bug this block fixes."""
    fake = FakeTmux()
    sup = _sup(tmp_path, fake)
    views = [
        supervisor.RowView(topic=f"plan{i}", repo="/r", tmux=None, ctx=None, status="unassigned")
        for i in range(20)
    ] + [supervisor.RowView(topic="stuck", repo="/r", tmux="s", ctx=9, status="danger")]
    out = _render_of(sup, views)
    assert "NEEDS YOU (1):" in out  # the ONE danger row, not 21
    assert "stuck" in out.split("NEEDS YOU")[1]
    assert "plan0" not in out.split("NEEDS YOU")[1]


def test_attention_block_includes_a_malformed_state_file(tmp_path):
    """A malformed declaration has no status of its own (it rides on the note) and is
    fail-closed — it needs a human, so it must appear in the block."""
    fake = FakeTmux()
    sup = _sup(tmp_path, fake)
    views = [
        supervisor.RowView(
            topic="t", repo="/r", tmux="s", ctx=50, status="idle", note="BAD state file: 'redy'"
        )
    ]
    out = _render_of(sup, views)
    assert "NEEDS YOU (1):" in out
    assert "BAD state file" in out


def test_needs_attention_predicate_covers_every_attention_status():
    """Guards the membership test itself, so a new attention status cannot be added to the
    tuple without the block picking it up."""
    for status in supervisor.ATTENTION_STATUSES:
        row = supervisor.RowView(topic="t", repo="/r", tmux="s", ctx=1, status=status)
        assert supervisor.needs_attention(row) is True
    for status in ("idle", "working", "warned", "winding-down", "settling", "unassigned"):
        row = supervisor.RowView(topic="t", repo="/r", tmux="s", ctx=99, status=status)
        assert supervisor.needs_attention(row) is False


# --------------------------------------------------------------------------- #
# Row color: the operator scans the live table by hue. Green = working, yellow =
# idle/waiting-on-human, red = broken, default (uncolored) = unassigned. Color is
# TTY-only, so it never corrupts piped `list` output or the beside-tests' plain
# StringIO — the render gates on `out.isatty()`.
# --------------------------------------------------------------------------- #

_GREEN = "\x1b[32m"
_YELLOW = "\x1b[33m"
_RED = "\x1b[31m"
_RESET = "\x1b[0m"


class _TtyOut:
    """A StringIO-alike that reports as a TTY, so `render` emits ANSI color (the
    real daemon writes to a tmux pane, which is a TTY). Duck-typed on purpose —
    the overseer only calls `write` / `flush` / `isatty`, and tests read via
    `getvalue`."""

    def __init__(self):
        self._buf = _io.StringIO()

    def write(self, text):
        return self._buf.write(text)

    def flush(self):
        self._buf.flush()

    def isatty(self):
        return True

    def getvalue(self):
        return self._buf.getvalue()


def _row_line(out, topic):
    """The single rendered line for TOPIC (the data row, not the header)."""
    return next(ln for ln in out.splitlines() if topic in ln and "Topic" not in ln)


def test_tty_render_tints_working_rows_green(tmp_path):
    sup = _sup(tmp_path, FakeTmux(), out=_TtyOut())
    view = supervisor.RowView(topic="wk", repo="/r", tmux="s", ctx=50, status="working")
    line = _row_line(_render_of(sup, [view]), "wk")
    assert line.startswith(_GREEN)
    assert line.endswith(_RESET)


def test_tty_render_tints_idle_and_waiting_rows_yellow(tmp_path):
    """Idle and `blocked:human` (waiting on a human decision) both read yellow — a
    human should glance at them (maintainer feature request 2026-07-15)."""
    for status in ("idle", "idle-with-context-left", "blocked:human", "warned", "danger"):
        sup = _sup(tmp_path, FakeTmux(), out=_TtyOut())
        view = supervisor.RowView(topic="yl", repo="/r", tmux="s", ctx=15, status=status)
        line = _row_line(_render_of(sup, [view]), "yl")
        assert line.startswith(_YELLOW), status
        assert line.endswith(_RESET), status


def test_tty_render_tints_broken_rows_red(tmp_path):
    """`session-gone` is still the "broken" red — a plan we have seen running is no
    longer in any tmux. `not-claude` is DELETED and must never come back."""
    sup = _sup(tmp_path, FakeTmux(), out=_TtyOut())
    view = supervisor.RowView(topic="br", repo="/r", tmux=None, ctx=None, status="session-gone")
    line = _row_line(_render_of(sup, [view]), "br")
    assert line.startswith(_RED)


def test_not_claude_is_gone_from_every_surface(tmp_path):
    """One guard so the jargon cannot creep back via the colour map or attention list."""
    assert "not-claude" not in supervisor._STATUS_COLOR
    assert "not-claude" not in supervisor.ATTENTION_STATUSES
    assert "session-gone" in supervisor.ATTENTION_STATUSES  # still attention


def test_tty_render_leaves_unassigned_rows_uncolored(tmp_path):
    """`unassigned` is background noise, not a track that wants attention — it keeps
    the terminal default color, never a tint."""
    sup = _sup(tmp_path, FakeTmux(), out=_TtyOut())
    view = supervisor.RowView(topic="un", repo="/r", tmux=None, ctx=None, status="unassigned")
    line = _row_line(_render_of(sup, [view]), "un")
    assert "\x1b[3" not in line  # no SGR color introducer at all


def test_tty_render_leaves_header_and_separator_uncolored(tmp_path):
    sup = _sup(tmp_path, FakeTmux(), out=_TtyOut())
    view = supervisor.RowView(topic="wk", repo="/r", tmux="s", ctx=50, status="working")
    out = _render_of(sup, [view])
    header = next(ln for ln in out.splitlines() if "Status" in ln and "Topic" in ln)
    assert "\x1b[3" not in header


def test_non_tty_render_is_plain_text(tmp_path):
    """A StringIO (and any piped `list`) is not a TTY, so no color leaks into it —
    this is what keeps every existing `row.split()` assertion valid."""
    sup = _sup(tmp_path, FakeTmux())  # default out is a plain StringIO
    view = supervisor.RowView(topic="wk", repo="/r", tmux="s", ctx=50, status="working")
    line = _row_line(_render_of(sup, [view]), "wk")
    assert "\x1b[3" not in line
    assert line.split() == ["working", "wk", "s", "50%", "r"]


def test_color_wraps_the_whole_line_so_alignment_is_preserved(tmp_path):
    """The ANSI codes wrap the padded line, never a cell — so once stripped, a green
    working row aligns to the same columns as an uncolored one."""
    sup = _sup(tmp_path, FakeTmux(), out=_TtyOut())
    views = [
        supervisor.RowView(topic="alpha", repo="/r", tmux="s1", ctx=50, status="working"),
        supervisor.RowView(topic="beta", repo="/r", tmux="s2", ctx=None, status="unassigned"),
    ]
    out = _render_of(sup, views)
    green = _row_line(out, "alpha")
    plain = _row_line(out, "beta")
    stripped = green[len(_GREEN) : -len(_RESET)]
    # Both data rows share the Topic column start, proving the color did not shift
    # the padded columns.
    assert stripped.index("alpha") == plain.index("beta")


# --------------------------------------------------------------------------- #
# The Status-cell note is elided so a session-authored value (a long `blocked:`
# reason) cannot blow up the column width or break the row (maintainer 2026-07-16).
# --------------------------------------------------------------------------- #


def test_render_elides_an_over_long_note_so_the_table_does_not_blow_up(tmp_path):
    """A `blocked:` reason can be arbitrarily long; the Status cell must flatten + truncate
    it with an ellipsis so it never blows up the column (a 705-byte completion summary
    written to a state file broke the live table)."""
    sup = _sup(tmp_path, FakeTmux())
    huge = "arc COMPLETE " + "x" * 500
    view = supervisor.RowView(topic="el", repo="/r", tmux="s", ctx=50, status="working", note=huge)
    out = _render_of(sup, [view])
    line = _row_line(out, "el")
    assert line.startswith("working (")
    assert "…" in line
    assert "x" * 500 not in out  # the raw blob never reaches the table
    assert max(len(ln) for ln in out.splitlines()) < 160  # no cell blows the line up


def test_render_flattens_a_multiline_note_onto_one_row(tmp_path):
    """A newline in the note must not split the row across lines — it is collapsed to spaces."""
    sup = _sup(tmp_path, FakeTmux())
    view = supervisor.RowView(
        topic="ml", repo="/r", tmux="s", ctx=50, status="working", note="alpha\nbeta\ngamma"
    )
    line = _row_line(_render_of(sup, [view]), "ml")
    assert "working (alpha beta gamma)" in line


def test_render_leaves_a_short_note_intact(tmp_path):
    """Elision only fires past the cap — a normal `working (background shell)` note renders
    verbatim, no ellipsis."""
    sup = _sup(tmp_path, FakeTmux())
    view = supervisor.RowView(
        topic="sh", repo="/r", tmux="s", ctx=50, status="working", note="background shell"
    )
    line = _row_line(_render_of(sup, [view]), "sh")
    assert "working (background shell)" in line
    assert "…" not in line


def test_needs_you_block_elides_an_over_long_reason(tmp_path):
    """The NEEDS YOU block embeds the reason too; a huge `blocked:` reason is capped there
    (the full text is in the pane the jump command points at)."""
    sup = _sup(tmp_path, FakeTmux())
    huge = "blocked reason " + "y" * 400
    view = supervisor.RowView(
        topic="bh", repo="/r", tmux="s", ctx=None, status="blocked:human", note=huge
    )
    needs = _render_of(sup, [view]).split("NEEDS YOU")[1]
    assert "…" in needs
    assert "y" * 400 not in needs
    assert "jump: tmux switch-client -t s" in needs  # the pane pointer is still there


def test_blocked_human_alert_caps_an_over_long_reason(tmp_path, capsys):
    """The edge-triggered `_alert` (daemon.log line) also caps the reason — a 705-byte
    `blocked:` dump must not become a 705-byte log line."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    _declare(repo, topic, "blocked: " + "y" * 400)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=40))
    sup = _sup(tmp_path, fake)
    sup.evaluate(_mapped_track(repo, topic, session), act=True)
    err = capsys.readouterr().err
    assert "blocked on human:" in err
    assert "…" in err
    assert "y" * 400 not in err


# --------------------------------------------------------------------------- #
# The log is an EVENT HISTORY: timestamped, and edge-triggered (not per-tick).
# --------------------------------------------------------------------------- #


def test_alert_is_edge_triggered_not_repeated_every_tick(tmp_path):
    """A track blocked overnight used to log ~3,000 identical lines, burying the history
    the bottom pane reads to answer "what happened?". One line per condition ENTERED."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=50))
    _declare(repo, topic, "blocked: needs a human")
    sup = _sup(tmp_path, fake)
    track = _mapped_track(repo, topic, session)

    err = _io.StringIO()
    with contextlib.redirect_stderr(err):
        for _ in range(5):  # five ticks of the SAME unchanged condition
            assert sup.evaluate(track, act=True).status == "blocked:human"
    surfaced = [ln for ln in err.getvalue().splitlines() if "overseer[SURFACE]" in ln]
    assert len(surfaced) == 1, surfaced


def test_alert_re_arms_after_the_track_recovers(tmp_path):
    """Edge-triggering must not SWALLOW a genuine re-entry: once a track goes healthy, the
    next time it goes bad it reports afresh."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    # 90% remaining: comfortably above the warn threshold, so the recovered tick is
    # healthy — `idle-with-context-left` (idle with room, so nudged to keep going). It is
    # NOT an attention status, so the edge-triggered alert still re-arms.
    fake.serve(session, repo, capture=_idle_capture(ctx=90))
    sup = _sup(tmp_path, fake)
    track = _mapped_track(repo, topic, session)

    err = _io.StringIO()
    with contextlib.redirect_stderr(err):
        state = _declare(repo, topic, "blocked: first")
        assert sup.evaluate(track, act=True).status == "blocked:human"
        state.unlink()  # the human answered → the track is healthy again
        assert sup.evaluate(track, act=True).status == "idle-with-context-left"
        _declare(repo, topic, "blocked: first")  # blocks AGAIN on the same reason
        assert sup.evaluate(track, act=True).status == "blocked:human"
    surfaced = [ln for ln in err.getvalue().splitlines() if "overseer[SURFACE]" in ln]
    assert len(surfaced) == 2, surfaced  # entered, recovered, entered again


def test_alert_reports_again_when_the_reason_changes(tmp_path):
    """Edge-triggering is on the CONDITION, not merely on the status: a track that stays
    blocked for a DIFFERENT reason is a new event and must be reported."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=50))
    sup = _sup(tmp_path, fake)
    track = _mapped_track(repo, topic, session)

    err = _io.StringIO()
    with contextlib.redirect_stderr(err):
        _declare(repo, topic, "blocked: reason one")
        sup.evaluate(track, act=True)
        _declare(repo, topic, "blocked: reason two")
        sup.evaluate(track, act=True)
    surfaced = [ln for ln in err.getvalue().splitlines() if "overseer[SURFACE]" in ln]
    assert len(surfaced) == 2, surfaced
    assert "reason one" in surfaced[0]
    assert "reason two" in surfaced[1]


def test_log_lines_are_timestamped(tmp_path):
    """The bottom pane answers "WHEN did this happen?" from the log, so every line must
    carry its own time — the alert lines used to carry none."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=50))
    _declare(repo, topic, "blocked: x")
    sup = _sup(tmp_path, fake)

    err = _io.StringIO()
    with contextlib.redirect_stderr(err):
        sup.evaluate(_mapped_track(repo, topic, session), act=True)
    line = next(ln for ln in err.getvalue().splitlines() if "overseer[SURFACE]" in ln)
    stamp = line.split(" overseer[SURFACE]")[0]
    # Parses as the ISO-8601 instant the daemon stamps its table with.
    assert datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00"))


# --------------------------------------------------------------------------- #
# The tmux window-name badge (the only surface visible from ANOTHER session).
# --------------------------------------------------------------------------- #


def test_window_name_is_badged_with_the_attention_count(tmp_path):
    """tmux renders the window name in the status bar of whatever session the operator is
    attached to — so a track that wants them is seen without switching panes."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=50))
    _declare(repo, topic, "blocked: needs you")
    sup = _sup(tmp_path, fake, own_pane="%7", watch_set_path=None, watch_repos=[str(repo)])
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path, added_at="t")

    with contextlib.redirect_stderr(_io.StringIO()):
        sup.tick(act=True)
    assert fake.window_name == "overseer(1!)"


def test_window_name_drops_the_badge_when_nothing_needs_attention(tmp_path):
    """The badge must CLEAR, or it becomes another stale indicator — the very bug."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=90))  # healthy
    sup = _sup(tmp_path, fake, own_pane="%7", watch_set_path=None, watch_repos=[str(repo)])
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path, added_at="t")

    with contextlib.redirect_stderr(_io.StringIO()):
        sup.tick(act=True)
    assert fake.window_name == "overseer"


def test_window_name_is_only_rewritten_when_the_count_changes(tmp_path):
    """A tmux call every tick for an unchanged name is pure noise."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=50))
    _declare(repo, topic, "blocked: x")
    sup = _sup(tmp_path, fake, own_pane="%7", watch_set_path=None, watch_repos=[str(repo)])
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path, added_at="t")

    with contextlib.redirect_stderr(_io.StringIO()):
        for _ in range(4):
            sup.tick(act=True)
    assert fake.renames() == ["overseer(1!)"]  # written ONCE, not four times


def test_read_only_list_never_renames_the_window(tmp_path):
    """`list` is advertised read-only, so printing a table must not rename the
    maintainer's window as a side effect."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=50))
    _declare(repo, topic, "blocked: x")
    sup = _sup(tmp_path, fake, own_pane="%7", watch_set_path=None, watch_repos=[str(repo)])
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path, added_at="t")

    with contextlib.redirect_stderr(_io.StringIO()):
        sup.tick(act=False)
    assert fake.renames() == []
    assert fake.window_name is None


def test_never_seen_is_unassigned_but_once_seen_is_session_gone(tmp_path):
    """THE distinction between the two, maintainer-declared 2026-07-17:

        "KEEP session-gone if you've ever seen the session, only use unassigned if
         you've never seen it"

    Both rows mean "no session here right now" — what separates them is whether we have
    EVER seen one. The MAPPING ROW is exactly that memory (adopt writes it when it first
    sees a session), which is why a dead mapping is KEPT, not pruned: pruning it would
    erase the very evidence that distinguishes these two states and silently demote a
    died-on-us track to look like one that never started.

    Neither row names a tmux session: `unassigned` never had one, and `session-gone`
    must not point at the bare terminal its session left behind.
    """
    repo, topic = _make_plan(tmp_path)
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    fake = FakeTmux()  # no tmux sessions exist at all
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {})

    # NEVER seen: a discovered plan with no mapping row.
    never = registry.Track.make_unassigned(repo=str(repo), topic=topic)
    never_view = sup.evaluate(never, act=True)
    assert never_view.status == "unassigned"
    assert never_view.tmux is None

    # SEEN once: a mapping row exists, but the session is not in any tmux now.
    session = registry.tmux_id(str(repo), topic)
    gone_view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert gone_view.status == "session-gone"
    assert gone_view.tmux is None

    # The two are distinguishable ONLY by the mapping row, so it must survive.
    assert never_view.status != gone_view.status


# --------------------------------------------------------------------------- #
# Codex restart safety — a FORWARD guard, deliberately written BEFORE the wiring.
# --------------------------------------------------------------------------- #


def test_an_unadopted_codex_looking_pane_is_never_restarted(tmp_path):
    """An UNADOPTED pane is never restarted, however much it looks like codex.

    A `bun` pane NOT proven to be a live codex session (absent from `_codex`) is
    `session-gone`, and is never restarted or keystroked — even declaring `ready`.

    Any codex ACT (wrap-up, restart) requires the per-tick `_codex` map to prove a real
    codex session for THIS topic in THIS repo resolves to this pane; `bun` alone is far too
    generic to act on (any bun app reports `bun`). With the map empty, `_pane_is_managed`
    rejects the pane and evaluation returns `session-gone` BEFORE any act branch. This
    guards the loose-`pane_is_codex` footgun — the adopted case (a real restart, via the
    codex command) is covered by the two sibling tests below.
    """
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    # A real codex pane: tmux reports `bun` (the launcher), NOT `codex` — the vendored
    # binary is its child. Verified live 2026-07-16 on tmux session `livespec3`.
    fake.serve(session, repo, capture=_codex_idle_capture(ctx=40), cmd="bun")
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {})  # _codex EMPTY: not adopted
    _declare(repo, topic, "ready")
    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "session-gone"  # unadopted `bun` pane is not ours to act on
    assert not fake.has("respawn")  # no restart of a pane we cannot prove is codex
    assert not fake.has("paste")  # and nothing keystroked into it either


def _adopt_codex_ready(tmp_path):
    """A codex track adopted in `_codex`, at a valid `ready`, on an idle Codex pane.

    The shared fixture for the two restart-routing guards below: a `bun` pane showing the
    real idle Codex shape, a live CodexSession in the map (as `_refresh_codex_sessions`
    builds each tick), and a genuinely-valid `ready` (stamp + newer marker) so evaluation
    reaches the restart branch — the branch where a runtime-misrouted restart would fire
    the claude command at a codex pane.
    """
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_codex_idle_capture(ctx=40), cmd="bun")  # a codex pane
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {})
    session_id = "019f6a1e-266d-7fc2-8eb2-15ec9d324fb8"
    sup._codex = {
        (session, topic): codex_sessions.CodexSession(
            pid=4242, name=topic, cwd=str(repo), session_id=session_id
        )
    }
    assert sup._is_codex_track(session, str(repo), topic, session)  # the precondition holds
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _arm_ready_marker(repo, topic, mtime=1001.0)  # the SOLE restart authorization
    return repo, topic, session, session_id, fake, sup


def test_an_adopted_codex_track_declaring_ready_is_restarted_with_the_codex_command(tmp_path):
    """A Codex track is now a FULL CITIZEN (maintainer-declared 2026-07-17): its own `ready`
    IS honoured — but via `codex resume <id>`, NEVER the claude launch command.

    This replaces the former monitor-only refusal. `_do_restart` runtime-dispatches: a Codex
    track routes to `_do_codex_restart`, which respawns `codex resume <session-id> "<kick>"`
    (reattaches the SAME rollout → adoptability survives; the kick auto-submits). The
    destructive bug this daemon can have is aiming `claude -n <topic>` at a codex pane; the
    routing prevents it and its sibling below pins it by sabotage.
    """
    repo, topic, session, session_id, fake, sup = _adopt_codex_ready(tmp_path)
    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "restarting"  # its own `ready` is honoured, not refused
    respawns = [c for c in fake.calls if c[0] == "respawn"]
    assert len(respawns) == 1
    command = respawns[0][3]
    _assert_no_tmux_scoping(command)
    assert "codex resume " in command  # the CODEX command, not claude
    assert session_id in command  # resumes the SAME session by id → adoptability survives
    # Autonomy parity with the Claude path's `--dangerously-skip-permissions`: without this
    # the resumed codex stalls at an interactive approval picker and the restart is not
    # hands-off (maintainer-declared 2026-07-17).
    assert "--dangerously-bypass-approvals-and-sandbox" in command
    assert not fake.has("paste")  # the kick is the resume ARGUMENT — no separate paste
    # THE ROUND IS CLOSED on success — and this is the high-consequence property. The await
    # (`_await_pane(pane_is_codex)`, which needs FakeTmux to model the respawn as a codex
    # pane) must succeed AND `_clear_state` must delete the marker, or a stale `ready` would
    # respawn-KILL the just-resumed codex EVERY tick — a destructive loop. Pin both: the
    # state file is gone, and a SECOND tick issues no second respawn.
    assert signals.read_state(str(repo), topic) is None
    fake.calls.clear()
    with contextlib.redirect_stderr(_io.StringIO()):
        sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert not fake.has("respawn")  # no re-restart of the session we just resumed


def test_two_codex_tracks_sharing_a_tmux_session_each_restart_their_own_session(tmp_path):
    """#4: two codex sessions live in ONE tmux session, each named for its own plan topic.
    Before the (tmux, name) keying, `self._codex` kept ONE CodexSession per tmux session,
    so the SECOND track resolved to the wrong session id (or None) — its restart aimed at
    the wrong rollout and its monitoring was silently lost, invisible in the table. Keyed
    by (tmux, topic), each track's `_do_codex_restart` resolves to ITS OWN session, so each
    respawns `codex resume <its-own-id>`. Sabotage: revert the lookup to `.get(session)`
    and the second track resolves to None → no respawn → this goes red."""
    repo, topic_a = _make_plan(tmp_path, topic="alpha")
    _, topic_b = _make_plan(tmp_path, topic="beta")
    shared = "shared-tmux"
    fake = FakeTmux()
    fake.serve(shared, repo, capture=_codex_idle_capture(ctx=40), cmd="bun")
    sup = _sup(tmp_path, fake)
    id_a = "019f6a1e-266d-7fc2-8eb2-15ec9d324fb8"
    id_b = "019f548d-6071-7893-9c2e-472cce81da02"
    sup._codex = {
        (shared, topic_a): codex_sessions.CodexSession(
            pid=10, name=topic_a, cwd=str(repo), session_id=id_a
        ),
        (shared, topic_b): codex_sessions.CodexSession(
            pid=20, name=topic_b, cwd=str(repo), session_id=id_b
        ),
    }
    target = fake.pane_id(shared)
    with contextlib.redirect_stderr(_io.StringIO()):
        sup._do_codex_restart(_mapped_track(repo, topic_a, shared), target)
        sup._do_codex_restart(_mapped_track(repo, topic_b, shared), target)
    respawn_cmds = [c[3] for c in fake.calls if c[0] == "respawn"]
    assert len(respawn_cmds) == 2  # each track resolved to a live session and respawned
    assert id_a in respawn_cmds[0] and id_b not in respawn_cmds[0]  # track alpha → A's rollout
    assert id_b in respawn_cmds[1] and id_a not in respawn_cmds[1]  # track beta → B's rollout


def test_a_codex_restart_keeps_the_ready_marker_when_the_respawn_fails(tmp_path):
    """B5 for the Codex arm: a failed `respawn-pane` must NOT clear the `ready` marker —
    the certification is preserved so the next tick retries, never silently destroyed
    (the Codex twin of `test_restart_keeps_marker_when_respawn_fails`).
    """
    repo, topic, session, _session_id, fake, sup = _adopt_codex_ready(tmp_path)
    fake.respawn_ok = False  # the atomic respawn fails
    with contextlib.redirect_stderr(_io.StringIO()):
        sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert signals.read_state(str(repo), topic) is not None  # marker KEPT for retry
    assert signals.read_state(str(repo), topic).token == signals.STATE_READY


def test_a_codex_restart_keeps_the_ready_marker_when_the_pane_never_becomes_codex(tmp_path):
    """B5 for the Codex arm: if the respawned pane never becomes a live Codex TUI
    (`_await_pane(pane_is_codex)` fails), the round is NOT closed — the `ready` marker is
    kept so the restart retries. Models the await-fail leg the success test's runtime
    modeling otherwise hides.
    """
    repo, topic, session, _session_id, fake, sup = _adopt_codex_ready(tmp_path)
    fake.respawn_yields_codex = False  # respawn succeeds but the pane comes up non-codex
    with contextlib.redirect_stderr(_io.StringIO()):
        sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert signals.read_state(str(repo), topic) is not None  # marker KEPT for retry
    assert signals.read_state(str(repo), topic).token == signals.STATE_READY


def test_a_codex_ready_restart_never_issues_the_claude_command(tmp_path):
    """THE sabotage-target guard: no respawn for a Codex `ready` track may carry the claude
    launch command. Aimed at a codex pane, `claude --dangerously-skip-permissions -n <topic>`
    REPLACES the codex session with a claude one and destroys it — the one destructive bug
    here.

    Teeth: reroute the restart to the claude command (delete the `is_codex=is_codex` on
    `_do_restart`, or the `if is_codex:` dispatch inside it) and this goes RED, because the
    respawn command becomes `claude …`. The claude launch string must appear in NO respawn.
    """
    repo, topic, session, _session_id, fake, sup = _adopt_codex_ready(tmp_path)
    claude_command = supervisor.Supervisor._launch_command(_mapped_track(repo, topic, session))
    with contextlib.redirect_stderr(_io.StringIO()):
        sup.evaluate(_mapped_track(repo, topic, session), act=True)
    respawn_commands = [c[3] for c in fake.calls if c[0] == "respawn"]
    assert respawn_commands  # it WAS restarted (full citizen)...
    assert claude_command not in respawn_commands  # ...but NEVER with the claude command
    assert not any("claude" in c for c in respawn_commands)  # belt-and-suspenders


def test_a_codex_track_below_threshold_gets_the_escalating_wrapup(tmp_path):
    """A Codex track below its wind-down threshold receives the SAME escalating wrap-up a
    Claude track does — the change that makes Codex a full citizen. Monitor-only left a
    Codex track a passenger that ran to context exhaustion; now the daemon's only lever
    reaches it too.

    The Codex submit is confirmed by the pane going BUSY after Enter (`is_busy`), not by a
    cleared `❯` box (Codex has none). The capture frames model that: idle for the main read
    + the settle pair, then busy after the paste's Enter.
    """
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    # frames: [main, settle-1, settle-2 (== settle-1 → settled), post-Enter (busy → submitted)]
    fake.serve(
        session,
        repo,
        capture=[_codex_idle_capture(ctx=40)] * 3 + [_codex_busy_capture(ctx=40)],
        cmd="bun",
    )
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {})
    sup._codex = {
        (session, topic): codex_sessions.CodexSession(
            pid=4242, name=topic, cwd=str(repo), session_id="019f6a1e-266d-7fc2-8eb2-15ec9d324fb8"
        )
    }
    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "warned"  # below threshold, above danger → warned (not idle)
    assert fake.has("paste")  # the wrap-up reached the Codex track
    assert "wind" in " ".join(fake.paste_texts()).lower()  # it IS the wrap-up text


def test_a_codex_approval_gate_suppresses_the_wrapup(tmp_path):
    """A Codex approval / directory-trust picker (`› 1.`) must SUPPRESS the wrap-up — the
    paste would otherwise type into the `1/2` chooser. The extended gate-cursor regex
    (`[❯›]`) is what catches the `›` cursor Codex uses (Claude uses `❯`).
    """
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    gate = (
        "Do you trust the contents of this directory?\n"
        "› 1. Yes, continue\n"
        "  2. No, quit\n"
        "  Context 40% left · topic\n"
    )
    fake.serve(session, repo, capture=gate, cmd="bun")
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {})
    sup._codex = {
        (session, topic): codex_sessions.CodexSession(
            pid=4242, name=topic, cwd=str(repo), session_id="019f6a1e-266d-7fc2-8eb2-15ec9d324fb8"
        )
    }
    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "blocked:human"  # a gate, not idle
    assert not fake.has("paste")  # nothing keystroked into the picker


def test_a_claude_pane_keeps_its_wrapup_when_codex_shares_its_tmux_session(tmp_path):
    """A live CLAUDE track must NOT be reclassified as codex just because a codex process
    resolves into the same tmux SESSION (adversarial review, 2026-07-17).

    Reachable, not exotic: `resolve_tmux_session` walks pid ancestry, so a `codex resume
    <topic>` launched from INSIDE this Claude session's own Bash tool lands in its tmux
    session — and the naming convention this work establishes is "codex threads named
    after plan topics", so the name matches the track's topic exactly.

    When `_is_codex_track` was session-scoped (while the Claude identity gate is
    pane-scoped) this Claude track went monitor-only and SILENTLY lost its wrap-up, its
    NOT-RESPONDING alert, and its restart — and `idle` kept it out of NEEDS YOU, so
    nothing surfaced. A live Claude track going quiet is the worst failure this daemon
    can have.
    """
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    # A PROVEN live Claude pane (`node`), below its wind-down threshold => must be warned.
    fake.serve(session, repo, capture=_idle_capture(ctx=40))
    sup = _sup(tmp_path, fake)
    # ...while a codex session for the SAME topic sits in the SAME tmux session.
    sup._codex = {
        (session, topic): codex_sessions.CodexSession(
            pid=4242, name=topic, cwd=str(repo), session_id="019f6a1e-266d-7fc2-8eb2-15ec9d324fb8"
        )
    }
    assert not sup._is_codex_track(session, str(repo), topic, fake.pane_id(session))  # pane is node
    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "warned"  # the Claude track is still supervised...
    assert fake.has("paste")  # ...and still gets the wrap-up, the daemon's only lever


# --------------------------------------------------------------------------- #
# R1 — self-healing resume-submit (2026-07-18). A freshly-respawned Claude can
# DROP the resume line's Enter while still drawing its welcome screen (proven live
# 2026-07-17: fabro / autonomous-mode / overseer-rewrite all stranded this way in
# one day). The old code cleared the `ready` marker and logged "restarted" anyway,
# so the daemon never retried and the session sat idle with an un-run handoff. Now
# the daemon KEEPS the round open, marks `resume_pending`, and retries the SUBMIT
# ONLY (re-send Enter, never a re-respawn) until the box clears.
# --------------------------------------------------------------------------- #


def _unsubmitted_resume_capture(ctx=30):
    """A freshly-respawned Claude with the resume line sitting UN-submitted in the box.

    The box holds the pasted `read <handoff> and follow it` text (a `❯ read …` line between
    rules), so it is NOT the empty idle box (`input_box_ready` False) and NOT busy — exactly
    the stranded state a dropped Enter leaves."""
    status = "  Opus 4.8 (1M context) | /x/repo"
    if ctx is not None:
        status += f" | Ctx: {ctx}% left"
    return (
        f"● welcome\n{_RULE}\n❯ read /x/repo/plan/topic/handoff.md and follow it\n"
        f"{_RULE}\n{status}\n{_HINT}\n"
    )


def test_fresh_respawn_dropped_enter_is_retried_next_tick_without_respawn(tmp_path):
    """The load-bearing self-heal: a restart whose resume Enter is DROPPED is retried on a
    later tick — re-sending Enter, NEVER a second respawn — and the round closes only once
    the box actually clears.

    Tick 1 models the dropped Enter (the fresh TUI shows the box holding the un-submitted
    resume for every post-respawn capture), so `_submit_prompt` returns False. Tick 2 the
    box clears on the retry's Enter. Asserts: (a) tick 1 keeps the marker + sets
    `resume_pending` and issues exactly ONE respawn; (b) tick 2 issues NO second respawn,
    re-sends Enter, and closes the round (marker + stamp gone, `resume_pending` cleared)."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    # Tick-1 frames: idle for the main read + the settle pair (reaches the restart branch),
    # then the un-submitted-resume box for every post-respawn capture (the last frame
    # repeats), so `_await_input_box` and every submit Enter see a box that never clears.
    idle = _idle_capture(ctx=30)
    fake.serve(session, repo, capture=[idle, idle, idle, _unsubmitted_resume_capture(ctx=30)])
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    marker = _arm_ready_marker(repo, topic, mtime=1001.0)

    with contextlib.redirect_stderr(_io.StringIO()):
        view1 = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view1.status == "restarting"
    assert len([c for c in fake.calls if c[0] == "respawn"]) == 1  # respawned exactly once
    assert marker.exists()  # the ready marker is KEPT — the round is NOT closed on a failed submit
    assert registry.read_resume_pending(str(repo), topic, sup.stamp_path) is True

    # Tick 2: the box clears on the retry's Enter. Reset the capture frames + index.
    fake.panes[session] = [_unsubmitted_resume_capture(ctx=30), _idle_capture(ctx=95)]
    fake._cap_idx.pop(session, None)
    fake.calls.clear()
    with contextlib.redirect_stderr(_io.StringIO()):
        view2 = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view2.status == "restarting"
    assert not fake.has(
        "respawn"
    )  # NEVER a second respawn — the retry can never escalate to a kill
    assert any(c[0] == "keys" and c[2] == "Enter" for c in fake.calls)  # it re-sent Enter
    assert not marker.exists()  # round closed only after the box cleared
    assert registry.read_resume_pending(str(repo), topic, sup.stamp_path) is False
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) is None


def test_restart_does_not_log_success_when_resume_unsubmitted(tmp_path):
    """A failed resume-submit must NOT log a clean "restarted" success — it marks
    `resume_pending`, alerts, and keeps the marker (the fresh Claude is up but idle with an
    un-run handoff; logging success would hide the stranding the maintainer reported)."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    fake.paste_ok = False  # the paste fails → `_submit_prompt` returns False (a clean submit-fail)
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    marker = _arm_ready_marker(repo, topic, mtime=1001.0)

    log = _io.StringIO()
    with contextlib.redirect_stderr(log):
        sup.evaluate(_mapped_track(repo, topic, session), act=True)
    out = log.getvalue()
    assert f"restarted {repo}::{topic}" not in out  # NO clean success line
    assert "NOT submitted" in out  # the operator IS told the resume did not land
    assert marker.exists()  # marker kept so the next tick retries
    assert registry.read_resume_pending(str(repo), topic, sup.stamp_path) is True


def test_submit_retry_never_kills_the_fresh_session(tmp_path):
    """The loop-safety property the Codex-#2 reasoning was protecting, now under the retry
    path: while a resume stays un-submitted the daemon retries the Enter every tick but
    NEVER respawns — so a still-valid `ready` can never re-fire `respawn-pane -k` and kill
    the live fresh Claude in a loop. The row stays a NEEDS-YOU report until it resumes."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    # A box that NEVER clears (plain string) — the retry can never succeed here.
    fake.serve(session, repo, capture=_unsubmitted_resume_capture(ctx=30))
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _arm_ready_marker(repo, topic, mtime=1001.0)
    registry.set_resume_pending(
        str(repo), topic, sup.stamp_path
    )  # already respawned; resume pending

    for _ in range(3):
        with contextlib.redirect_stderr(_io.StringIO()):
            view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
        assert view.status == "restarting"
        assert view.note == supervisor._RESUME_PENDING_NOTE
        assert supervisor.needs_attention(view)  # a stranded resume is a NEEDS-YOU row
        assert not fake.has("respawn")  # NEVER a respawn on the retry path
        assert registry.read_resume_pending(str(repo), topic, sup.stamp_path) is True
        assert signals.read_state(str(repo), topic).token == signals.STATE_READY  # marker kept


def test_idle_pane_with_resume_pending_closes_the_round_instead_of_respawning(tmp_path):
    """The sharp loop-safety case: with `resume_pending` set and a still-valid `ready`, an
    IDLE (empty-box) pane means the resume ALREADY submitted (a prior Enter, or the human) —
    so the retry branch closes the round rather than re-entering the `elif ready:` restart
    path and respawn-KILLING the fresh session. WITHOUT the retry interception this idle pane
    + valid ready would `_do_restart` → respawn: this is exactly the destructive loop the
    self-heal prevents."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(
        session, repo, capture=_idle_capture(ctx=95)
    )  # empty box → the resume already landed
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _arm_ready_marker(repo, topic, mtime=1001.0)
    registry.set_resume_pending(str(repo), topic, sup.stamp_path)  # respawned; resume outstanding

    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "restarting"
    assert not fake.has("respawn")  # NEVER respawn-kill the fresh session — the round just closes
    assert signals.read_state(str(repo), topic) is None  # round closed (marker gone)
    assert registry.read_resume_pending(str(repo), topic, sup.stamp_path) is False


def test_claude_restart_success_closes_the_round_and_issues_no_second_respawn(tmp_path):
    """Symmetric with the Codex success-leg guard (PR #1308 review): a Claude restart whose
    resume submits cleanly closes the round (marker + stamp gone) AND issues no second
    respawn on the next tick — else a stale `ready` would respawn-KILL the fresh session
    every tick, a destructive loop. Pins both runtimes' restart success legs symmetrically."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))  # empty box → submit lands at once
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _arm_ready_marker(repo, topic, mtime=1001.0)

    with contextlib.redirect_stderr(_io.StringIO()):
        sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert signals.read_state(str(repo), topic) is None  # round closed
    assert registry.read_resume_pending(str(repo), topic, sup.stamp_path) is False
    fake.calls.clear()
    with contextlib.redirect_stderr(_io.StringIO()):
        sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert not fake.has("respawn")  # no re-restart of the session we just resumed


# --------------------------------------------------------------------------- #
# R2 — Claude identity gate `name == topic` parity + stale-mapping re-point
# (2026-07-18). Generic reused tmux windows (livespec1…) are cycled across topics,
# so a window the store maps to topic A but now running topic B's Claude (same repo)
# passed the process+cwd gate and got A's wrap-up injected into B — then a `ready`
# respawn-KILLED B as A. The Codex gate was already pane-scoped (`name == topic`);
# this brings the Claude gate to parity and re-points the stale mapping.
# --------------------------------------------------------------------------- #


def test_claude_act_refuses_pane_whose_live_name_differs_from_topic(tmp_path):
    """A pane running a live Claude for a DIFFERENT topic (same repo) is NOT ours: the gate
    rejects it on the `name != topic` proof, so the track never injects into nor respawns
    it and renders `session-gone` — even with a valid `ready` that WOULD otherwise restart."""
    repo, topic = _make_plan(tmp_path, topic="alpha")
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    # A genuinely-live Claude pane in this tmux session, cwd in the repo — but it is
    # topic BETA's session, not our track's ALPHA. (Process + cwd both pass; only the
    # name betrays it.)
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {})  # empty registry → no live-outside-tmux
    sup._claude_names = {session: {"beta"}}  # the live Claude here belongs to topic `beta`
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _arm_ready_marker(repo, topic, mtime=1001.0)  # would restart if the gate passed

    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "session-gone"  # not ours → routed to session-gone, like a foreign pane
    assert not fake.has("respawn")  # never respawn-kill another topic's live Claude
    assert not fake.has("paste")  # never keystroke into it


def test_claude_gate_allows_pane_whose_live_name_matches_topic(tmp_path):
    """The parity check is POSITIVE-mismatch only: a matching `name == topic` (the normal
    case) still passes the gate and the track acts as before. Pairs with the refusal test so
    the check cannot be read as "reject unless proven" — it rejects only a proven mismatch."""
    repo, topic = _make_plan(tmp_path, topic="alpha")
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    sup = _sup(tmp_path, fake)
    sup._claude_names = {session: {"alpha"}}  # the live Claude here IS our topic
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _arm_ready_marker(repo, topic, mtime=1001.0)

    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "restarting"  # name matches → ours → the `ready` restart fires
    assert fake.has("respawn")


def test_stale_tmux_mapping_is_repointed_when_topic_session_moves(tmp_path):
    """When a topic's live named session resolves to a DIFFERENT tmux session than the store
    records (a generic window reused for another topic; the session moved), adoption
    RE-POINTS the mapping to the current tmux within one tick rather than freezing the stale
    binding. The re-pointed store then drives acts at the RIGHT pane."""
    repo, topic = _make_plan(tmp_path, topic="alpha")
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    fake = FakeTmux()
    ppid: dict[int, int] = {}
    starttimes: dict[int, str] = {}
    # A live named session for `alpha` whose pid walks up to tmux session `new-tmux`.
    _write_session(sessions_dir, 100, name="alpha", cwd=str(repo))
    starttimes[100] = "pt"
    shell = 101
    ppid[100] = shell
    fake.pane_pids[shell] = "new-tmux"
    sup = _adopt_sup(tmp_path, fake, sessions_dir, ppid, starttimes, watch_repos=[str(repo)])
    # The store maps `alpha` to a STALE tmux session (`old-tmux`) — where it used to run.
    registry.append_mapping(_mapped_track(repo, topic, "old-tmux"), sup.store_path, added_at="pre")

    with contextlib.redirect_stderr(_io.StringIO()):
        sup.adopt_sessions()

    rows = {(r.repo, r.topic): r.tmux for r in registry.read_mapping(sup.store_path)}
    assert (
        rows[(os.path.normpath(str(repo)), "alpha")] == "new-tmux"
    )  # re-pointed to the live session


def test_repoint_is_idempotent_when_the_mapping_already_matches(tmp_path):
    """A steady-state tick where the live session's tmux already equals the stored mapping
    must NOT rewrite the store (no churn) and must NOT re-adopt (no duplicate row)."""
    repo, topic = _make_plan(tmp_path, topic="alpha")
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    fake = FakeTmux()
    _write_session(sessions_dir, 100, name="alpha", cwd=str(repo))
    ppid = {100: 101}
    fake.pane_pids[101] = "the-tmux"
    sup = _adopt_sup(tmp_path, fake, sessions_dir, ppid, {100: "pt"}, watch_repos=[str(repo)])
    registry.append_mapping(_mapped_track(repo, topic, "the-tmux"), sup.store_path, added_at="pre")

    assert registry.repoint_tmux(str(repo), topic, "the-tmux", sup.store_path) is False  # no-op
    with contextlib.redirect_stderr(_io.StringIO()):
        adopted = sup.adopt_sessions()
    assert adopted == []  # already mapped, tmux unchanged → neither re-adopted nor re-pointed
    rows = registry.read_mapping(sup.store_path)
    assert len([r for r in rows if r.topic == "alpha"]) == 1  # exactly one row, no duplicate
    assert rows[0].tmux == "the-tmux"


# --------------------------------------------------------------------------- #
# Fable review hardening (2026-07-18): SF1 re-point flip-flop, SF2 gate wiring,
# SF3 busy false-close, SF4 gate keystroke, SF5 helper-Claude flap.
# --------------------------------------------------------------------------- #


def test_claude_name_gate_is_wired_end_to_end_through_the_registry(tmp_path):
    """SF2: the R2 name gate must reject a mismatched pane through the PRODUCTION wiring
    (registry → `_refresh_claude_status` → `_claude_names` → gate), not only when a test
    hand-injects `_claude_names`. A registry session named `beta` in the track's tmux session
    (topic `alpha`) → the wired gate rejects the pane → `session-gone`, no respawn."""
    repo, topic = _make_plan(tmp_path, topic="alpha")
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))  # a live Claude pane
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    _write_session(sessions_dir, 100, name="beta", cwd=str(repo))  # NOT our topic
    ppid = {100: 50}
    fake.pane_pids[50] = session  # 100 → shell 50 → tmux `session`
    sup = _adopt_sup(tmp_path, fake, sessions_dir, ppid, {100: "pt"})
    with contextlib.redirect_stderr(_io.StringIO()):
        sup._refresh_claude_status()  # the WIRING under test
    assert sup._claude_names.get(session) == {"beta"}  # populated from the registry, not by hand
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _arm_ready_marker(repo, topic, mtime=1001.0)  # would restart if the gate passed
    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "session-gone"  # the WIRED name gate rejects the mismatched pane
    assert not fake.has("respawn")


def test_helper_claude_in_the_same_tmux_does_not_flap_the_track(tmp_path):
    """SF5: a HELPER Claude sharing the track's tmux session (a second window/split) must NOT
    shadow the track's own name and flap it to `session-gone`. With `_claude_names` a SET, the
    track's topic being AMONG the live names is enough to keep the pane ours."""
    repo, topic = _make_plan(tmp_path, topic="alpha")
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    sup = _sup(tmp_path, fake)
    sup._claude_names = {session: {"helper", "alpha"}}  # our topic present ALONGSIDE a helper
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _arm_ready_marker(repo, topic, mtime=1001.0)
    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "restarting"  # NOT flapped to session-gone — the track is still ours
    assert fake.has("respawn")


def test_ambiguous_two_sessions_for_one_track_does_not_flip_flop_the_repoint(tmp_path):
    """SF1: when TWO live sessions carry the same (repo, topic) — dual-driving, or an
    R1-stranded pane plus a hand-started replacement — the re-point must NOT flip-flop the
    mapping between their tmux ids every tick (two store rewrites + two log lines forever).
    It skips the re-point while ambiguous and leaves the mapping untouched."""
    repo, topic = _make_plan(tmp_path, topic="alpha")
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    fake = FakeTmux()
    # TWO live sessions named `alpha`, in DIFFERENT tmux sessions `tmux-A` and `tmux-B`.
    _write_session(sessions_dir, 100, name="alpha", cwd=str(repo))
    _write_session(sessions_dir, 200, name="alpha", cwd=str(repo))
    ppid = {100: 50, 200: 60}
    fake.pane_pids = {50: "tmux-A", 60: "tmux-B"}
    starttimes = {100: "pt", 200: "pt"}
    sup = _adopt_sup(tmp_path, fake, sessions_dir, ppid, starttimes, watch_repos=[str(repo)])
    registry.append_mapping(_mapped_track(repo, topic, "tmux-A"), sup.store_path, added_at="pre")

    log = _io.StringIO()
    with contextlib.redirect_stderr(log):
        sup.adopt_sessions()
        sup.adopt_sessions()  # a second tick must not flip it back
    rows = {(r.repo, r.topic): r.tmux for r in registry.read_mapping(sup.store_path)}
    assert rows[(os.path.normpath(str(repo)), "alpha")] == "tmux-A"  # left untouched (ambiguous)
    assert "re-pointed" not in log.getvalue()  # no flip-flop, no log spam


def test_pending_resume_on_a_gate_reports_blocked_human_and_sends_no_enter(tmp_path):
    """SF4: a freshly-restarted pane that comes up on a picker (trust / update / bypass-perms
    confirm) must NOT be keystroked (blocker #6) — the retry reports `blocked:human`, sends no
    Enter, and keeps the round open so it resumes once the human clears the gate."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(
        session, repo, capture="Do you want to proceed?\n❯ 1. Yes\n  2. No\n  Ctx: 90% left\n"
    )
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _arm_ready_marker(repo, topic, mtime=1001.0)
    registry.set_resume_pending(str(repo), topic, sup.stamp_path)
    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "blocked:human"
    assert not any(c[0] == "keys" for c in fake.calls)  # NEVER keystroked the gate
    assert not fake.has("respawn")
    assert signals.read_state(str(repo), topic).token == signals.STATE_READY  # round kept open
    assert registry.read_resume_pending(str(repo), topic, sup.stamp_path) is True


def test_pending_retry_does_not_false_close_on_hook_busy_with_text_in_box(tmp_path):
    """SF3: a freshly-respawned session can be BUSY for reasons unrelated to the resume
    (SessionStart hooks) while the resume still sits UN-submitted in the box. The retry
    branches on the BOX STATE (text present → re-send Enter), never treating `busy` as
    'submitted' — else it would false-close the round and re-strand the session invisibly."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    # The box HOLDS the un-submitted resume text AND a hook spinner makes the pane busy.
    capture = "✻ (running SessionStart hooks… 1/2 · 3s)\n" + _unsubmitted_resume_capture(ctx=90)
    fake.serve(session, repo, capture=capture)
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _arm_ready_marker(repo, topic, mtime=1001.0)
    registry.set_resume_pending(str(repo), topic, sup.stamp_path)
    with contextlib.redirect_stderr(_io.StringIO()):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "restarting"
    assert view.note == supervisor._RESUME_PENDING_NOTE  # still pending, NOT falsely closed
    assert signals.read_state(str(repo), topic).token == signals.STATE_READY  # marker KEPT
    assert registry.read_resume_pending(str(repo), topic, sup.stamp_path) is True
    assert any(c[0] == "keys" and c[2] == "Enter" for c in fake.calls)  # it DID re-send Enter
    assert not fake.has("respawn")


# --------------------------------------------------------------------------- #
# Fail-soft marker I/O. The state file is written by the SESSION and read by the
# daemon, so every marker read/write/delete can fail on a tick (a directory in
# the file's place, an unwritable marker dir). Each failure must be LOGGED and
# the surrounding decision left in its safe default — never raised out of the
# tick, which would strand every other track the daemon is supervising.
# --------------------------------------------------------------------------- #


def _undeletable_state_file(repo, topic):
    """Put a DIRECTORY where the ``.overseer-state`` file belongs.

    ``unlink`` on a directory always fails (``EISDIR``) for every user including
    root, so this models an undeletable marker without a chmod the CI container
    (which runs as root) would ignore.
    """
    path = signals.state_path(str(repo), topic)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.mkdir()
    return path


def test_clear_state_logs_an_undeletable_marker_and_still_closes_the_round(tmp_path):
    """`_clear_state` must not raise when the marker cannot be deleted: it logs the
    failure and still performs the REST of the clear (stamp + in-memory round), so a
    single unlink failure cannot abort the tick mid-restart."""
    repo, topic = _make_plan(tmp_path)
    _undeletable_state_file(repo, topic)
    sup = _sup(tmp_path, FakeTmux())
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    key = _key_for(repo, topic)
    sup._inject[key] = supervisor._InjectState(last_ctx=30)
    err = _io.StringIO()

    with contextlib.redirect_stderr(err):
        sup._clear_state(_mapped_track(repo, topic, "sesA"))

    assert "could not delete state file" in err.getvalue()
    assert topic in err.getvalue()
    # The round still closed: the durable stamp is gone and the in-memory state popped.
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) is None
    assert key not in sup._inject


def test_unreadable_ready_marker_leaves_the_ready_flag_as_is(tmp_path):
    """`_void_if_stale` voids a declaration it can prove is stale. An UNREADABLE marker
    proves nothing, so the flag comes back untouched and nothing is cleared —
    `ready_valid` is the gate that already refused to trust it."""
    repo, topic = _make_plan(tmp_path)
    sup = _sup(tmp_path, FakeTmux())
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    track = _mapped_track(repo, topic, "sesA")

    assert sup._void_if_stale(track, ready=True) is True  # no state file → unreadable
    # and the round was NOT closed behind the daemon's back
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) == 1000.0


def test_void_stale_blocked_keeps_the_reason_when_the_marker_no_longer_declares_one(tmp_path):
    """`_void_stale_blocked` only retires a `blocked:` it can still SEE on disk. An
    unreadable file, or one that now declares something else, leaves the caller's reason
    untouched — voiding on a read it could not make would destroy a live declaration."""
    repo, topic = _make_plan(tmp_path)
    sup = _sup(tmp_path, FakeTmux())
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    track = _mapped_track(repo, topic, "sesA")
    blocked = "blocked: waiting on the schema call"

    # (a) no state file at all → unreadable
    assert sup._void_stale_blocked(track, blocked, generating=True) == blocked
    # (b) the file exists but the session has since declared `ready` — not a block anymore
    _arm_ready_marker(repo, topic, mtime=1.0)  # far past the grace, so only the token gates
    assert sup._void_stale_blocked(track, blocked, generating=True) == blocked
    # Neither path ran `_clear_state`, so the round is intact.
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) == 1000.0


def test_idle_nudge_marker_write_failure_is_logged_not_raised(tmp_path):
    """The daemon-owned `idle-with-context-left` marker lives under a per-topic dir. When
    that dir cannot be created the write is logged and skipped — never raised — and no
    marker is left behind, so the next idle tick simply re-nudges."""
    repo, topic = _make_plan(tmp_path)
    marker_dir = signals.state_path(str(repo), topic).parent
    marker_dir.parent.mkdir(parents=True, exist_ok=True)
    marker_dir.write_text("a FILE where the marker dir belongs\n", encoding="utf-8")
    sup = _sup(tmp_path, FakeTmux())
    err = _io.StringIO()

    with contextlib.redirect_stderr(err):
        sup._write_idle_nudge_state(_mapped_track(repo, topic, "sesA"))

    assert "could not write idle-nudge marker" in err.getvalue()
    assert signals.read_state(str(repo), topic) is None  # nothing was written


def test_failed_nudge_alerts_and_writes_no_marker_so_it_retries(tmp_path):
    """The nudge marker is written only AFTER the paste lands. A failed paste must
    ALERT (naming the tmux coordinate) and leave the episode unmarked, so the next tick
    re-nudges rather than silently recording a keep-going prompt that never arrived."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))  # idle, well above threshold
    fake.paste_ok = False  # the bracketed paste does not land
    clock = {"t": 1000.0}
    sup = _sup(tmp_path, fake, now=lambda: clock["t"])
    sup._claude_status = {session: "idle"}
    track = _mapped_track(repo, topic, session)

    sup.evaluate(track, act=True)  # stamps idle_since
    clock["t"] += supervisor._IDLE_NUDGE_AFTER + 1
    err = _io.StringIO()
    with contextlib.redirect_stderr(err):
        view = sup.evaluate(track, act=True)

    assert view.status == "idle-with-context-left"
    assert "idle-with-context-left nudge FAILED" in err.getvalue()
    assert session in err.getvalue()  # the alert names where to go
    assert signals.read_state(str(repo), topic) is None  # episode NOT marked handled
    # Unmarked means un-given-up-on: the next idle tick tries the nudge again.
    clock["t"] += supervisor._IDLE_NUDGE_AFTER + 1
    with contextlib.redirect_stderr(_io.StringIO()):
        sup.evaluate(track, act=True)
    assert _nudge_count(fake) == 2  # re-attempted, not silently marked handled


# --------------------------------------------------------------------------- #
# Panes that vanish or never come up. Every step of an act is a hard gate: an
# unresolvable pane, a respawn whose pane never becomes the expected runtime, and
# a fresh TUI sitting on a gate all STOP the act with the declaration preserved.
# --------------------------------------------------------------------------- #


def _on_respawn(fake, after):
    """Run ``after(session)`` right after a SUCCESSFUL FakeTmux respawn.

    Models what the pane actually BECOMES once the respawn lands — a bare shell (the
    launch never came up), or a fresh TUI that opened on a trust/update gate.
    """
    inner = fake.respawn_pane

    def respawn(session, cwd, command):
        landed = inner(session, cwd, command)
        if landed:
            after(session)
        return landed

    fake.respawn_pane = respawn


def test_pane_that_vanishes_mid_tick_is_session_gone_and_never_acted_on(tmp_path):
    """RB3: the mapped session passes `session_exists` but dies before its pane id is
    resolved. With no pane id there is nothing safe to target — a bare `-t <name>` could
    fall back to a live SIBLING session and `respawn-pane -k` could kill IT — so the row
    degrades to `session-gone` and no pane op runs, even on a valid `ready`."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()  # no live Claude for the topic outside tmux either
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {})
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    marker = _arm_ready_marker(repo, topic, mtime=1001.0)
    exists = fake.session_exists

    def vanishing_exists(name):
        answer = exists(name)
        fake.sessions.discard(session)  # the pane dies right after we looked
        return answer

    fake.session_exists = vanishing_exists

    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)

    assert view.status == "session-gone"
    assert view.tmux is None  # never name a session that is not there
    assert not fake.has("respawn")  # nothing was targeted...
    assert not fake.has("paste")
    assert marker.exists()  # ...and the declaration survives for a later tick


def test_restart_keeps_the_marker_when_the_respawned_pane_never_becomes_claude(tmp_path):
    """B5: the respawn SUCCEEDS but the pane comes up as a bare shell (the launch died
    immediately). The round must NOT be closed — the daemon alerts and keeps the `ready`
    declaration + stamp so the restart retries, rather than reporting a launch it could
    not verify. The Claude twin of the Codex `never becomes codex` guard."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    _on_respawn(fake, lambda s: fake.cmds.__setitem__(s, "zsh"))  # comes up a shell
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    marker = _arm_ready_marker(repo, topic, mtime=1001.0)
    err = _io.StringIO()

    with contextlib.redirect_stderr(err):
        sup.evaluate(_mapped_track(repo, topic, session), act=True)

    assert "respawned pane never became Claude" in err.getvalue()
    assert session in err.getvalue()  # the alert names where to go
    assert marker.exists()  # declaration preserved for the retry
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) == 1000.0
    assert supervisor.default_resume(str(repo), topic) not in fake.paste_texts()


def test_freshly_restarted_pane_on_a_gate_pends_the_resume_instead_of_keystroking_it(tmp_path):
    """Blocker #6: the fresh Claude came up on a trust/update/permissions PICKER. Pasting
    the resume line + Enter there would auto-accept the picker's default, so the daemon
    keystrokes NOTHING: it records a round-scoped `resume_pending`, alerts, and leaves the
    `ready` marker in place for the next tick to retry once the human clears the gate."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    gate = "Do you want to proceed?\n❯ 1. Yes\n  2. No\n"
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    _on_respawn(fake, lambda s: fake.panes.__setitem__(s, gate))  # fresh TUI opens on a gate
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    marker = _arm_ready_marker(repo, topic, mtime=1001.0)
    err = _io.StringIO()

    with contextlib.redirect_stderr(err):
        sup.evaluate(_mapped_track(repo, topic, session), act=True)

    assert "freshly-restarted pane is on a gate" in err.getvalue()
    assert not fake.has("paste")  # NEVER keystroked the picker
    assert not any(c[0] == "keys" for c in fake.calls)
    assert registry.read_resume_pending(str(repo), topic, sup.stamp_path) is True
    assert marker.exists()  # round left open for the retry


def test_codex_restart_alerts_when_the_codex_session_vanished_before_the_respawn(tmp_path):
    """#4/B5: `_do_codex_restart` resolves the session id from the live per-tick map. If
    the codex process died between the map refresh and the restart, there is no id to
    resume — so it must alert and KEEP the declaration, never respawn a guessed target."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_codex_idle_capture(ctx=40), cmd="bun")
    sup = _sup(tmp_path, fake)  # `_codex` left EMPTY: the session is gone
    marker = _arm_ready_marker(repo, topic, mtime=1001.0)
    err = _io.StringIO()

    with contextlib.redirect_stderr(err):
        sup._do_codex_restart(_mapped_track(repo, topic, session), session)

    assert "codex session vanished before restart" in err.getvalue()
    assert session in err.getvalue()
    assert not fake.has("respawn")  # nothing respawned without a resolved session id
    assert marker.exists()


# --------------------------------------------------------------------------- #
# Watch-set resolution, GC fail-soft, and the post-auto-link re-join.
# --------------------------------------------------------------------------- #


def _fleet_manifest(tmp_path, *repo_names):
    """A tmp `.livespec-fleet-manifest.jsonc` naming ``repo_names`` as fleet members.

    `registry.watch_set` resolves each name against the manifest repo's PARENT, so the
    manifest lives one level down (`<tmp>/core/`) and the repos are its siblings.
    """
    core = tmp_path / "core"
    core.mkdir(exist_ok=True)
    manifest = core / ".livespec-fleet-manifest.jsonc"
    manifest.write_text(
        json.dumps({"fleet": [{"repo": name} for name in repo_names]}), encoding="utf-8"
    )
    return manifest


def test_watch_set_comes_from_the_home_declaration_when_no_repos_are_injected(tmp_path):
    """With no explicit `watch_repos`, the daemon watches what the `$HOME` declaration
    names — but only checkouts that EXIST and carry a `plan/` dir, so a declared repo that
    is not cloned locally is silently absent rather than a phantom watched repo.

    This is the relocation-critical path: the declaration is an ABSOLUTE `$HOME` path, so
    it resolves identically no matter where the overseer package itself lives. The
    superseded manifest seeding walked UP three directories from this file, which broke
    the instant the package moved out of `<core>/.claude/skills/`.
    """
    alpha, _ = _make_plan(tmp_path, repo_name="alpha")
    (tmp_path / "gamma").mkdir()  # cloned, but no plan/ dir
    declaration = tmp_path / "repos.json"
    declaration.write_text(  # beta is declared but not cloned
        json.dumps(
            {
                "repos": [
                    str(tmp_path / "alpha"),
                    str(tmp_path / "beta"),
                    str(tmp_path / "gamma"),
                ]
            }
        ),
        encoding="utf-8",
    )
    sup = _sup(tmp_path, FakeTmux(), watch_set_path=str(declaration))

    assert sup._resolve_watch() == [os.path.normpath(str(alpha))]


def test_archive_gc_keeps_a_row_it_cannot_evaluate(tmp_path):
    """Fail-soft: a malformed mapping row (a non-string repo) cannot be evaluated for
    archival, so the GC KEEPS it rather than dropping data it does not understand."""
    sup = _sup(tmp_path, FakeTmux())
    raw = json.dumps({"repo": 42, "topic": "t", "tmux": "sesA"}) + "\n"
    Path(sup.store_path).write_text(raw, encoding="utf-8")

    assert sup.archive_gc() == 0
    assert Path(sup.store_path).read_text(encoding="utf-8") == raw  # byte-identical


def test_build_rows_rejoins_after_auto_link_so_the_row_is_mapped_this_tick(tmp_path):
    """An auto-link MUTATES the store mid-tick, so `build_rows` must re-join afterwards.
    Without the re-join the tick would evaluate the stale pre-link snapshot and render the
    plan `unassigned` for a full interval despite having just linked its live session."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.sessions.add(session)
    fake.paths[session] = str(repo / "plan" / topic)  # cwd inside the repo → linkable
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()  # empty Claude registry: only auto-link can create the row
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {}, watch_repos=[str(repo)])

    rows = sup.build_rows(act=True)

    assert [(r.topic, r.tmux) for r in rows] == [(topic, session)]
    assert not rows[0].is_unassigned  # the re-joined row, not the stale unassigned one


def test_codex_track_is_rejected_when_its_live_session_runs_outside_the_repo(tmp_path):
    """`_is_codex_track` pins BOTH the (tmux, topic) key AND the repo. A live codex
    session named for this topic but running in a DIFFERENT repo is not this track's
    session, so no codex act (wrap-up, `codex resume` restart) may be aimed at it."""
    repo, topic = _make_plan(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_codex_idle_capture(ctx=40), cmd="bun")
    sup = _sup(tmp_path, fake)
    sup._codex = {
        (session, topic): codex_sessions.CodexSession(
            pid=4242,
            name=topic,
            cwd=str(elsewhere),  # the ONE thing that differs
            session_id="019f6a1e-266d-7fc2-8eb2-15ec9d324fb8",
        )
    }

    assert sup._is_codex_track(session, str(repo), topic, session) is False


# --------------------------------------------------------------------------- #
# Reboot-recovery edges: an already-live session is skipped, and every launch
# failure (Claude or Codex) is SURFACED rather than counted as recovered.
# --------------------------------------------------------------------------- #


def test_recover_skips_a_track_whose_session_is_already_live(tmp_path):
    """Recovery recreates only ABSENT sessions. A live one is skipped outright — the
    `session_exists` gate is what makes startup recovery safe to run at all."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture())  # the session IS live
    sup = _sup(tmp_path, fake)
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path)

    assert sup.recover_missing_sessions() == []
    assert not fake.has("new")  # never re-created a live session...
    assert not fake.has("respawn")  # ...and never respawn-killed it


def test_recover_surfaces_a_claude_track_whose_launch_fails(tmp_path, capsys):
    """B5: `_do_launch` returning False must be SURFACED and the track left out of the
    recovered list — never a silent claim that a session was recreated."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()  # session absent → created, then the respawn fails
    fake.respawn_ok = False
    sup = _sup(tmp_path, fake)
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path)

    assert sup.recover_missing_sessions() == []

    err = capsys.readouterr().err
    assert "reboot-recovery FAILED to launch" in err
    assert session in err and topic in err


def test_recover_codex_skips_when_new_session_does_not_create_the_session(tmp_path, capsys):
    """Codex re-review #3, Codex arm: if `new-session` did not create the EXACT session,
    recovery must not proceed to a respawn that could target a prefix-matched sibling."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    fake = FakeTmux()
    fake.new_session_ok = False
    sup = _sup(tmp_path, fake, codex_home=str(_codex_home_with(tmp_path, topic, sid)))
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path)

    assert sup.recover_missing_sessions() == []
    assert not fake.has("respawn")

    err = capsys.readouterr().err
    assert "new-session did not create" in err and session in err


def test_recover_codex_surfaces_when_the_codex_resume_launch_fails(tmp_path, capsys):
    """B5, Codex arm: the session was created but `codex resume` never landed. The track
    is surfaced and NOT reported as recovered, so the operator relaunches it by hand."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    fake = FakeTmux()
    fake.respawn_ok = False  # the session is created, but the codex respawn fails
    sup = _sup(tmp_path, fake, codex_home=str(_codex_home_with(tmp_path, topic, sid)))
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path)

    assert sup.recover_missing_sessions() == []
    assert fake.has("new")  # it got as far as creating the session...
    assert fake.has("respawn")  # ...and attempting the resume

    err = capsys.readouterr().err
    assert "FAILED to resume codex" in err and session in err


def test_launch_helpers_refuse_a_session_with_no_resolvable_pane(tmp_path):
    """RB3 for BOTH launch arms: with no pane id there is no exact target, so each helper
    returns False WITHOUT respawning — a bare `-t <name>` could hit a live sibling."""
    repo, topic = _make_plan(tmp_path)
    fake = FakeTmux()  # no sessions at all → pane_id is None for anything
    sup = _sup(tmp_path, fake)
    track = _mapped_track(repo, topic, "no-such-session")

    assert sup._do_launch(track, "no-such-session") is False
    assert sup._do_codex_launch(track, "no-such-session", "aaaa-bbbb") is False
    assert not fake.has("respawn")


def test_do_launch_is_false_when_the_pane_never_becomes_claude(tmp_path):
    """B5: a respawn that lands but never yields a live Claude TUI is a FAILED launch —
    False, and the resume line is never pasted into whatever is sitting there instead."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture())
    _on_respawn(fake, lambda s: fake.cmds.__setitem__(s, "zsh"))  # comes up a shell
    sup = _sup(tmp_path, fake)

    assert sup._do_launch(_mapped_track(repo, topic, session), session) is False
    assert fake.has("respawn")  # it did try...
    assert not fake.has("paste")  # ...but never pasted into the un-verified pane


# --------------------------------------------------------------------------- #
# The daemon loop: the per-store singleton lock, startup recovery, the sleep
# between ticks, and a clean exit on Ctrl-C.
# --------------------------------------------------------------------------- #


def test_run_refuses_to_start_when_another_daemon_holds_the_store_lock(tmp_path):
    """B6: two daemons on one store double-inject and double-restart — B's
    `respawn-pane -k` can kill the fresh session A just resumed. The second daemon
    surfaces the contended lock path and returns WITHOUT ticking."""
    holder = _sup(tmp_path, FakeTmux())
    handle = holder._acquire_singleton_lock()
    assert handle is not None
    try:
        sup = _sup(tmp_path, FakeTmux())  # same store path → same lock
        ticked = []
        sup.tick = lambda *, act: ticked.append(act)  # type: ignore[assignment]  # spy
        err = _io.StringIO()
        with contextlib.redirect_stderr(err):
            sup.run(once=True)
        assert ticked == []  # NO tick ran
        assert "refusing to start" in err.getvalue()
        assert str(sup._singleton_lock_path()) in err.getvalue()
    finally:
        supervisor.Supervisor._release_singleton_lock(handle)


def test_singleton_lock_is_treated_as_contended_when_the_lockfile_cannot_be_created(tmp_path):
    """Fail-soft: any OSError acquiring the lock reads as CONTENDED (None), so a broken
    lock path refuses to start a second daemon rather than assuming it is alone."""
    sup = _sup(tmp_path, FakeTmux())
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("a FILE where the store's parent dir belongs\n", encoding="utf-8")
    sup.store_path = str(blocker / "map.jsonl")  # mkdir of the parent must fail

    assert sup._acquire_singleton_lock() is None


def test_run_with_recover_recreates_missing_sessions_before_the_first_tick(tmp_path):
    """`run(recover=True)` performs startup recovery once, BEFORE the loop — so a
    post-reboot daemon has its mapped sessions back by the time the first tick renders."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()  # session absent → recovery recreates it
    fake.panes[session] = _idle_capture()  # post-launch empty box so the resume confirms
    sup = _sup(tmp_path, fake)
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path)
    ticked = []
    sup.tick = lambda *, act: ticked.append(act)  # type: ignore[assignment]  # spy

    with contextlib.redirect_stderr(_io.StringIO()):
        sup.run(once=True, recover=True)

    assert ("new", session, str(repo)) in fake.calls  # recovery ran...
    assert ticked == [True]  # ...and then exactly one tick


def test_run_sleeps_between_ticks_and_exits_cleanly_on_keyboard_interrupt(tmp_path):
    """The loop paces itself with the injected `sleep(interval)` between ticks, and a
    Ctrl-C during a tick exits by RETURNING (logged) rather than propagating — so the
    `finally` releases the singleton lock instead of leaving it held."""
    slept = []
    sup = _sup(tmp_path, FakeTmux(), sleep=slept.append)
    ticks = []

    def tick(*, act):
        ticks.append(act)
        if len(ticks) == 2:  # the operator hits Ctrl-C during the second tick
            raise KeyboardInterrupt

    sup.tick = tick  # type: ignore[assignment]
    err = _io.StringIO()

    with contextlib.redirect_stderr(err):
        sup.run(interval=7.0, once=False)  # must RETURN, not raise

    assert ticks == [True, True]
    assert slept == [7.0]  # slept exactly once, between the two ticks
    assert "interrupted; exiting" in err.getvalue()


# --------------------------------------------------------------------------- #
# The startup gitignore probe. `git check-ignore -q` is the one real subprocess
# in this module; only a ZERO exit may be read as "ignored", and a spawn failure
# fails soft to "not ignored" (which REFUSES to start).
# --------------------------------------------------------------------------- #


def _completed(returncode):
    """A `subprocess.CompletedProcess` reached via the supervisor module, so this
    test file needs no `import subprocess` of its own."""
    return supervisor.subprocess.CompletedProcess(args=[], returncode=returncode)


def test_gitignore_check_is_true_only_on_a_zero_exit(monkeypatch):
    """`git check-ignore -q` exits 0 when ignored, 1 when not, 128 on error — so only a
    0 means ignored. Reading 128 as "ignored" would let the daemon start against a repo
    where its markers dirty the tracked tree."""
    codes = [0, 1, 128]
    argvs = []

    def fake_run(argv, **_kwargs):
        argvs.append(argv)
        return _completed(codes.pop(0))

    monkeypatch.setattr(supervisor.subprocess, "run", fake_run)

    assert supervisor.default_gitignore_check("/x/repo") is True  # 0 → ignored
    assert supervisor.default_gitignore_check("/x/repo") is False  # 1 → NOT ignored
    assert supervisor.default_gitignore_check("/x/repo") is False  # 128 → git errored
    assert argvs[0] == ["git", "-C", "/x/repo", "check-ignore", "-q", "tmp/overseer"]


def test_gitignore_check_fails_soft_to_not_ignored_when_git_cannot_spawn(monkeypatch):
    """A spawn failure (no git on PATH) fails soft to False — "not ignored" — which makes
    the daemon REFUSE to start. Failing soft to True would be the unsafe direction."""

    def boom(argv, **_kwargs):
        raise OSError("no git on PATH")

    monkeypatch.setattr(supervisor.subprocess, "run", boom)

    assert supervisor.default_gitignore_check("/x/repo") is False


# --------------------------------------------------------------------------- #
# CLI wiring: the fixed fleet manifest, the no-knob Supervisor builder, and the
# `list` / `adopt` / failing-`start` subcommand bodies.
# --------------------------------------------------------------------------- #


def test_watch_set_location_does_not_depend_on_where_this_package_lives(tmp_path):
    """The watch-set declaration is an ABSOLUTE `$HOME` path, independent of this module's
    position on disk. This is the property that makes the package relocatable, and it is
    the direct inverse of what the superseded implementation guaranteed.

    That implementation resolved the fleet manifest as `Path(__file__).parents[3]` — "three
    directories up is the repo root" — which is true ONLY while the package sits at
    `<core>/.claude/skills/overseer/`. Moving it anywhere else silently repointed the
    lookup outside the repo, which is why it was the single genuine code blocker on the
    relocation. Asserting the path is under `$HOME` and contains no `..` traversal pins
    that the coupling is gone rather than merely relocated.
    """
    declared = Path(registry.DEFAULT_WATCH_SET_PATH)

    assert declared.is_absolute()
    assert declared.parent == Path.home()
    assert ".." not in declared.parts
    # And it is NOT derived from this module's own location.
    assert Path(supervisor.__file__).resolve().parent not in declared.parents


def test_build_supervisor_has_no_knobs_and_badges_its_own_tmux_pane(monkeypatch):
    """The de-gold-plated builder: the watch-set is the `$HOME` declaration and the store /
    stamp paths are the hard-coded registry defaults (None → the module default), with
    `own_pane` read from `$TMUX_PANE` so the window badge works without a flag.

    Asserting the registry constant rather than a recomputed path is deliberate: the whole
    point of the change is that the daemon no longer DERIVES its watch-set location from
    this file's position on disk.
    """
    monkeypatch.setenv("TMUX_PANE", "%42")
    sup = supervisor._build_supervisor()

    assert sup.watch_set_path == registry.DEFAULT_WATCH_SET_PATH
    assert sup.own_pane == "%42"
    assert sup.watch_repos is None  # no --repos knob
    assert sup.store_path is None and sup.stamp_path is None  # no --store / --stamp knobs

    monkeypatch.delenv("TMUX_PANE")
    assert supervisor._build_supervisor().own_pane is None  # not under tmux → no badge


def test_cli_colliding_reads_the_same_watch_set_the_daemon_does(tmp_path, monkeypatch):
    """A one-shot `add`/`start` must name its session EXACTLY as the daemon would, so it
    computes collisions over the same `$HOME`-declared watch-set: only a topic present in
    TWO repos is repo-qualified; a topic unique to one repo stays bare.

    Patching the registry CONSTANT rather than a supervisor helper is the point — after the
    relocation change there is no path-deriving function left to patch, which is exactly the
    coupling that had to go.
    """
    _make_plan(tmp_path, repo_name="alpha", topic="shared")
    _make_plan(tmp_path, repo_name="alpha", topic="only-alpha")
    _make_plan(tmp_path, repo_name="beta", topic="shared")
    declaration = tmp_path / "repos.json"
    declaration.write_text(
        json.dumps({"repos": [str(tmp_path / "alpha"), str(tmp_path / "beta")]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(registry, "DEFAULT_WATCH_SET_PATH", declaration)

    assert supervisor._cli_colliding() == frozenset({"shared"})


def test_cli_list_renders_exactly_one_read_only_tick(monkeypatch):
    """`overseer list` builds the fleet Supervisor and ticks it ONCE with `act=False` —
    the advertised read-only render: no injection, no restart, no store mutation."""
    ticks = []

    class _TickOnlySup:
        def tick(self, *, act):
            ticks.append(act)
            return []

    monkeypatch.setattr(supervisor, "_build_supervisor", lambda: _TickOnlySup())

    assert supervisor.main(["list"]) == 0
    assert ticks == [False]


def test_cli_adopt_reports_every_adopted_session_and_the_total(monkeypatch, capsys):
    """`overseer adopt` names each newly-adopted session with its (repo, topic) and then
    reports the count — the operator's confirmation that a hand-started session is now
    supervised."""
    adopted = [
        registry.Track(topic="alpha", repo="/x/repo_a", tmux="sesA"),
        registry.Track(topic="beta", repo="/x/repo_b", tmux="sesB"),
    ]

    class _AdoptOnlySup:
        def adopt_sessions(self):
            return adopted

    monkeypatch.setattr(supervisor, "_build_supervisor", lambda: _AdoptOnlySup())

    assert supervisor.main(["adopt"]) == 0

    out = capsys.readouterr().out
    assert "adopted sesA → /x/repo_a::alpha" in out
    assert "adopted sesB → /x/repo_b::beta" in out
    assert "adopted 2 existing session(s)" in out


def test_cli_start_fails_when_the_tmux_session_cannot_be_created(tmp_path, monkeypatch, capsys):
    """Codex re-review #3: `new-session` failing must abort `start` with a nonzero exit —
    proceeding to `_do_launch` would respawn whatever the bare name prefix-matched. And a
    start that never launched must leave NO mapping row claiming it did."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    store = _isolate_store(tmp_path, monkeypatch)
    fake = FakeTmux()  # session absent
    fake.new_session_ok = False
    monkeypatch.setattr(supervisor.tmuxio, "TmuxIO", lambda: fake)

    assert supervisor.main(["start", "--repo", str(repo), "--topic", topic]) == 1
    assert ("new", session, str(repo)) in fake.calls
    assert not fake.has("respawn")  # never respawned a prefix-matched sibling
    assert "could not create tmux session" in capsys.readouterr().err
    assert registry.read_mapping(store) == []  # nothing mapped


def test_cli_start_fails_when_the_launch_does_not_land(tmp_path, monkeypatch, capsys):
    """B5 at the CLI: `_do_launch` returning False exits nonzero and reports, rather than
    printing `started …` for a session that never came up — and again maps nothing."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    store = _isolate_store(tmp_path, monkeypatch)
    fake = FakeTmux()  # session absent → created, then the respawn fails
    fake.respawn_ok = False
    monkeypatch.setattr(supervisor.tmuxio, "TmuxIO", lambda: fake)

    assert supervisor.main(["start", "--repo", str(repo), "--topic", topic]) == 1
    assert ("new", session, str(repo)) in fake.calls
    assert fake.has("respawn")

    err = capsys.readouterr().err
    assert "start FAILED to launch" in err and session in err
    assert registry.read_mapping(store) == []  # nothing mapped


# --------------------------------------------------------------------------- #
# The read-only render (`/overseer list` → `tick(act=False)`) must DERIVE every
# status the daemon would while performing NO side effect: no paste, no respawn,
# no alert, no injection stamp, and no marker written or retired. Each test below
# picks a branch whose act=True twin is already covered and pins the act=False
# side. `list` runs against a LIVE daemon's store, so a side effect leaking into
# it is exactly the bug these close.
# --------------------------------------------------------------------------- #


def test_read_only_list_reports_a_malformed_state_file_without_alerting(tmp_path):
    """A typo'd declaration still shows in the row's note under `list`, but the operator
    ALERT is an event-history line the DAEMON owns — emitting it from the read-only render
    would re-spam the log on every `list`."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    _declare(repo, topic, "redy", mtime=1001.0)  # typo
    err = _io.StringIO()

    with contextlib.redirect_stderr(err):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=False)

    assert view.note is not None and "redy" in view.note  # the operator still sees it
    assert "MALFORMED state file" not in err.getvalue()  # but no alert was emitted
    assert not fake.has("paste")
    assert not fake.has("respawn")


def test_read_only_list_reports_working_without_retiring_a_stale_block(tmp_path):
    """A `blocked:` a generating session has outlived is retired by the DAEMON (it deletes
    the marker). `list` must render the same `working` row carrying that reason and leave
    the marker on disk — retiring it is a filesystem mutation, and the teeth here are that
    the identical act=True tick DOES void it."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture="esc to interrupt\n  Ctx: 40% left\n")  # generating
    sup = _sup(tmp_path, fake)
    _declare(repo, topic, "blocked: waiting on a human", mtime=1.0)  # far past the grace
    track = _mapped_track(repo, topic, session)

    view = sup.evaluate(track, act=False)

    assert view.status == "working"
    assert view.note is not None and "waiting on a human" in view.note  # reason still shown
    state = signals.read_state(str(repo), topic)
    assert state is not None and state.token == signals.STATE_BLOCKED  # marker untouched

    # Teeth: the SAME tick with act=True is the one allowed to retire it.
    with contextlib.redirect_stderr(_io.StringIO()):
        assert sup.evaluate(track, act=True).note is None
    assert signals.read_state(str(repo), topic) is None


def test_read_only_list_reports_restarting_without_respawning(tmp_path):
    """`restarting` is a DERIVED status — the row shows what the daemon would do next. Under
    `list` no respawn may fire and the `ready` declaration + round must survive intact, or a
    read-only render would have consumed the session's one restart authorization."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    marker = _arm_ready_marker(repo, topic, mtime=1001.0)

    view = sup.evaluate(_mapped_track(repo, topic, session), act=False)

    assert view.status == "restarting"
    assert not fake.has("respawn")  # the session was NOT killed by a `list`
    assert not fake.has("paste")
    assert marker.exists()  # the authorization survives for the daemon's own tick
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) == 1000.0


def test_read_only_list_reports_danger_without_injecting_or_alerting(tmp_path):
    """At/below the danger line the daemon injects a wrap-up and alerts that the track is
    NOT RESPONDING. `list` shows the same `danger` row and does neither — and above all
    opens no injection round, which would move the certification anchor a later `ready`
    is compared against."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=15))  # <= DANGER_CTX_REMAINING
    sup = _sup(tmp_path, fake)
    err = _io.StringIO()

    with contextlib.redirect_stderr(err):
        view = sup.evaluate(_mapped_track(repo, topic, session), act=False)

    assert view.status == "danger"
    assert err.getvalue() == ""  # no NOT RESPONDING alert from a read-only render
    assert _wrapup_count(fake) == 0  # and nothing keystroked
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) is None


# --------------------------------------------------------------------------- #
# Remaining single-branch edges: an unreported self-status, a failed paste in an
# ALREADY-open round, a failed window rename, and `start` on a proven-dead pane.
# --------------------------------------------------------------------------- #


def test_live_outside_tmux_note_omits_the_suffix_when_no_status_is_reported(tmp_path):
    """The live-outside-tmux note appends Claude's own self-reported status only when the
    registry actually carries one. With none reported the note stops at the pid — never a
    dangling `self-reported status ` with nothing after it."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()  # mapped tmux session absent → routes to the no-managed-pane row
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    _write_session(sessions_dir, 100, name=topic, cwd=str(repo), status="")  # no self-report
    sup = _adopt_sup(tmp_path, fake, sessions_dir, {}, {100: "pt"})

    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)

    assert view.status == "live-outside-tmux"
    assert view.note == (
        "live Claude session (pid 100) running OUTSIDE tmux — daemon cannot manage it"
    )
    assert "self-reported status" not in view.note


def test_failed_paste_in_an_already_open_round_keeps_the_rounds_stamp(tmp_path):
    """The rollback on a failed wrap-up paste applies ONLY to a round this tick just
    OPENED. A re-warn at a lower band runs inside a round opened earlier, and clearing that
    round's `at` would reset the anchor `ready_valid` compares a declaration against — so
    the stamp is left alone and only the alert fires."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=40))  # a LOWER band than 50
    fake.paste_ok = False  # the re-warn paste does not land
    sup = _sup(tmp_path, fake, warn_percent=50)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)  # round ALREADY open
    registry.add_notified_band(str(repo), topic, 50, sup.stamp_path)  # the 50 band already sent
    err = _io.StringIO()

    with contextlib.redirect_stderr(err):
        sup.evaluate(_mapped_track(repo, topic, session), act=True)

    assert "wrap-up injection FAILED" in err.getvalue()
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) == 1000.0  # kept
    # The undelivered band is NOT marked notified, so the next tick re-tries it.
    assert 40 not in set(registry.read_notified_bands(str(repo), topic, sup.stamp_path))


def test_window_badge_is_retried_when_the_rename_fails(tmp_path):
    """The badge is memoized so an unchanged count costs no tmux call — but only on
    SUCCESS. A rename that fails must not be remembered as written, or the attention count
    would be permanently absent from the window name until the count happened to change."""
    fake = FakeTmux()
    inner = fake.rename_window

    def failing_rename(pane, name):
        _ = inner(pane, name)
        return False  # tmux refused the rename

    fake.rename_window = failing_rename
    sup = _sup(tmp_path, fake, own_pane="%1")

    sup._refresh_window_name(2)
    sup._refresh_window_name(2)

    assert fake.renames() == ["overseer(2!)", "overseer(2!)"]  # retried, not memoized
    assert sup._window_name is None  # nothing recorded as written


def test_releasing_the_singleton_lock_frees_it_and_releasing_none_is_a_no_op(tmp_path):
    """Release must actually free the flock (else a daemon restart could never re-acquire
    its own store's lock), and must tolerate the `None` a contended acquire returns."""
    sup = _sup(tmp_path, FakeTmux())
    handle = sup._acquire_singleton_lock()
    assert handle is not None

    supervisor.Supervisor._release_singleton_lock(handle)

    regained = _sup(tmp_path, FakeTmux())._acquire_singleton_lock()
    assert regained is not None  # the same store's lock is genuinely free again
    supervisor.Supervisor._release_singleton_lock(regained)
    # Releasing a lock that was never acquired is a safe no-op, not a crash.
    assert supervisor.Supervisor._release_singleton_lock(None) is None


def test_cli_start_respawns_a_session_proven_dead_by_its_bare_shell(tmp_path, monkeypatch, capsys):
    """RB4: `start` fails CLOSED, refusing to respawn-kill anything not PROVEN dead. A bare
    SHELL is that proof (a live Claude reports `node`, a live Codex `bun`), so this is the
    one no-`--force` path that may respawn an EXISTING session."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    store = _isolate_store(tmp_path, monkeypatch)
    fake = FakeTmux()
    # The session exists but its pane dropped to a shell — proven dead.
    fake.serve(session, repo, capture=_idle_capture(), cmd="zsh")
    monkeypatch.setattr(supervisor.tmuxio, "TmuxIO", lambda: fake)

    assert supervisor.main(["start", "--repo", str(repo), "--topic", topic]) == 0

    assert fake.has("respawn")  # the dead shell's pane WAS relaunched
    assert not fake.has("new")  # ...in place; the session already existed
    assert supervisor.default_resume(str(repo), topic) in fake.paste_texts()
    assert [(r.topic, r.tmux) for r in registry.read_mapping(store)] == [(topic, session)]
    assert f"started {os.path.normpath(str(repo))}::{topic}" in capsys.readouterr().out
