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
        self.cmds[session] = "node"  # a fresh Claude TUI is now live
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
    return supervisor.Supervisor(
        tmux=fake,
        store_path=str(tmp_path / "map.jsonl"),
        stamp_path=str(tmp_path / "stamps.json"),
        now=lambda: 1000.0,
        sleep=lambda _s: None,
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


def test_foreign_pane_still_names_the_mismapped_tmux_session(tmp_path):
    """The counter-case that keeps the rule honest: `not-claude` means the mapping
    points at a live FOREIGN pane, and that pane is exactly what the operator must go
    inspect — so it MUST still be named (and stay jumpable). The rule is "do not name a
    session that isn't there", not "blank the column whenever something is wrong"."""
    repo, topic = _make_plan(tmp_path)
    other = tmp_path / "elsewhere"
    other.mkdir()
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, other, capture=_idle_capture(ctx=40))  # live claude, wrong repo
    sup = _sup(tmp_path, fake)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "not-claude"
    assert view.tmux == session


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


def test_claude_pane_in_wrong_repo_is_not_claude(tmp_path):
    """The mapped session is a live Claude but its cwd is a DIFFERENT repo → the
    identity gate's path check fails → `not-claude`, no act (B3 + B1 residual)."""
    repo, topic = _make_plan(tmp_path)
    other = tmp_path / "elsewhere"
    other.mkdir()
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, other, capture=_idle_capture(ctx=40))  # claude, but cwd=other repo
    sup = _sup(tmp_path, fake)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "not-claude"
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
    assert view.status == "not-claude"
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


def test_idle_above_threshold_nudges_once_to_keep_going(tmp_path):
    """A session idle at an empty prompt with context ABOVE the threshold and no
    declaration is nudged ONCE this episode to keep going (the inverse of the wrap-up)
    and marked `idle-with-context-left`; a second idle tick does NOT re-nudge."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))  # well above threshold
    sup = _sup(tmp_path, fake)
    sup._claude_status = {session: "idle"}
    track = _mapped_track(repo, topic, session)

    view = sup.evaluate(track, act=True)
    assert view.status == "idle-with-context-left"
    assert _nudge_count(fake) == 1  # nudged once
    assert _wrapup_count(fake) == 0  # a keep-going nudge, NOT a wind-down wrap-up
    # The daemon wrote its own marker to the single state file.
    state = signals.read_state(str(repo), topic)
    assert state is not None and state.token == signals.STATE_IDLE_WITH_CONTEXT_LEFT

    # Still idle with the marker present → single prompt: NOT re-nudged.
    view = sup.evaluate(track, act=True)
    assert view.status == "idle-with-context-left"
    assert _nudge_count(fake) == 1


def test_nudge_re_arms_after_the_session_takes_a_turn(tmp_path):
    """Single prompt per EPISODE: after a nudge, the session going non-idle (busy) clears
    the marker, so idling with context left AGAIN re-nudges."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))
    sup = _sup(tmp_path, fake)
    sup._claude_status = {session: "idle"}
    track = _mapped_track(repo, topic, session)

    assert sup.evaluate(track, act=True).status == "idle-with-context-left"
    assert _nudge_count(fake) == 1

    # The session takes a turn (Claude busy) → the marker is cleared (re-arm on non-idle).
    sup._claude_status = {session: "busy"}
    assert sup.evaluate(track, act=True).status == "working"
    assert signals.read_state(str(repo), topic) is None  # marker gone

    # Idle again with context left → a FRESH nudge (a new episode).
    sup._claude_status = {session: "idle"}
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


def test_adopt_sessions_links_by_registry_name(tmp_path):
    """adopt maps each LIVE Claude session (from ~/.claude/sessions) to a plan when
    its registry `cwd` is in a fleet repo AND its `name` is an active plan topic,
    joined to the tmux session by PID. Registry membership proves it is a claude
    process, so there is no worker-command guard. Non-matches, a session outside
    tmux, a dead PID, and an already-mapped (repo, topic) contribute nothing."""
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
    live(500, "gamma", repo_a, "sesG")  # skip: (repo_a, gamma) already mapped below
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
    assert rows[(os.path.normpath(str(repo_a)), "gamma")] == "gamma-existing"  # untouched
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
    for status in ("session-gone", "not-claude"):
        sup = _sup(tmp_path, FakeTmux(), out=_TtyOut())
        view = supervisor.RowView(topic="br", repo="/r", tmux="s", ctx=None, status=status)
        line = _row_line(_render_of(sup, [view]), "br")
        assert line.startswith(_RED), status


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
    sup = _sup(tmp_path, fake, own_pane="%7", manifest_path=None, watch_repos=[str(repo)])
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
    sup = _sup(tmp_path, fake, own_pane="%7", manifest_path=None, watch_repos=[str(repo)])
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
    sup = _sup(tmp_path, fake, own_pane="%7", manifest_path=None, watch_repos=[str(repo)])
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
    sup = _sup(tmp_path, fake, own_pane="%7", manifest_path=None, watch_repos=[str(repo)])
    registry.append_mapping(_mapped_track(repo, topic, session), sup.store_path, added_at="t")

    with contextlib.redirect_stderr(_io.StringIO()):
        sup.tick(act=False)
    assert fake.renames() == []
    assert fake.window_name is None
