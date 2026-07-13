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

import hashlib
import io as _io
import os

import pytest
import registry
import signals
import supervisor


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


class FakeTmux:
    """Injectable stand-in for tmuxio.TmuxIO — canned reads, recorded writes."""

    def __init__(self):
        self.sessions = set()
        self.panes = {}
        self.cmds = {}
        self.paths = {}
        self.calls = []
        self.on_paste = None  # callback(session, text) for stamp-before-paste checks
        self.paste_ok = True  # set False to model a failed bracketed paste (B5)
        self.respawn_ok = True  # set False to model a failed respawn (B5)
        self.new_session_ok = True  # set False to model a failed new-session (Codex #3)
        self._cap_idx = {}
        self._cmd_idx = {}

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

    # test helpers ---------------------------------------------------- #
    def paste_texts(self):
        return [c[2] for c in self.calls if c[0] == "paste"]

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
    return supervisor.Supervisor(
        tmux=fake,
        store_path=str(tmp_path / "map.jsonl"),
        stamp_path=str(tmp_path / "stamps.json"),
        out=_io.StringIO(),
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
    signals.blocked_marker_path(str(repo), topic).write_text("waiting on schema call\n")
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


def test_shell_pane_is_not_claude_never_pastes(tmp_path):
    """A tracked session that dropped to a shell (pane_current_command != claude)
    must read `not-claude` and get NO paste — even at low ctx with an idle-looking
    old box in scrollback (B3: else the wrap-up executes in the shell and forges a
    marker)."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    # Old idle box still on screen + a shell prompt; pane command is now zsh.
    fake.serve(session, repo, capture=_idle_capture(ctx=40), cmd="zsh")
    sup = _sup(tmp_path, fake)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "not-claude"
    assert not fake.has("paste")
    assert not fake.has("respawn")


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
    fake.serve(session, repo, capture=_idle_capture(ctx=40))  # below default threshold 50
    stamp_path = str(tmp_path / "stamps.json")
    seen = []
    fake.on_paste = lambda _s, _t: seen.append(
        registry.read_injection_stamp(str(repo), topic, stamp_path)
    )
    sup = _sup(tmp_path, fake)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "warned"
    assert fake.paste_texts() and "Wrap up for a clean session restart" in fake.paste_texts()[0]
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


def test_idle_above_threshold_does_nothing(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=73))  # well above threshold
    sup = _sup(tmp_path, fake)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "idle"
    assert not fake.has("paste")


def test_resend_once_when_ctx_keeps_dropping(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo)
    sup = _sup(tmp_path, fake)
    track = _mapped_track(repo, topic, session)
    fake.panes[session] = _idle_capture(ctx=40)
    sup.evaluate(track, act=True)  # first inject
    fake.panes[session] = _idle_capture(ctx=30)
    sup.evaluate(track, act=True)  # re-send (ctx dropped)
    fake.panes[session] = _idle_capture(ctx=28)
    sup.evaluate(track, act=True)  # capped: no third inject
    wrapups = [t for t in fake.paste_texts() if "Wrap up for a clean session restart" in t]
    assert len(wrapups) == 2


def test_danger_surfaces_below_danger_line(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=15))  # <= DANGER, no ready marker
    sup = _sup(tmp_path, fake)
    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status == "danger"


# --------------------------------------------------------------------------- #
# Restart interlock: fires ONLY on marker-valid + not-busy + idle; deletes marker.
# --------------------------------------------------------------------------- #


def _arm_ready_marker(repo, topic, *, mtime=1001.0):
    handoff = repo / "plan" / topic / "handoff.md"
    digest = hashlib.sha256(handoff.read_bytes()).hexdigest()
    marker = signals.ready_marker_path(str(repo), topic)
    marker.write_text(digest + "\n")
    os.utime(marker, (mtime, mtime))
    return marker


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
    assert ("respawn", session, str(repo), f"claude -n {topic}") in fake.calls
    resume = supervisor.default_resume(str(repo), topic)
    assert resume in fake.paste_texts()
    # the ready marker was deleted AND the injection stamp cleared (round closed, B4)
    assert not marker.exists()
    assert registry.read_injection_stamp(str(repo), topic, sup.stamp_path) is None


def test_no_restart_when_marker_hash_mismatch(tmp_path):
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo, capture=_idle_capture(ctx=30))
    sup = _sup(tmp_path, fake)
    registry.write_injection_stamp(str(repo), topic, 1000.0, sup.stamp_path)
    marker = signals.ready_marker_path(str(repo), topic)
    marker.write_text("deadbeef\n")  # wrong contents → invalid
    os.utime(marker, (1001.0, 1001.0))

    view = sup.evaluate(_mapped_track(repo, topic, session), act=True)
    assert view.status != "restarting"
    assert not fake.has("respawn")


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
    """RB2: after a void, the in-memory inject state is popped, so the NEXT
    threshold crossing opens a fresh count==0 round that writes a new stamp — else
    the cleared stamp + stuck count==1 would wedge the track (never re-certifies)."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    sup = _sup(tmp_path, fake)
    track = _mapped_track(repo, topic, session)
    # Round 1: inject (count=1, stamp written) on an idle low-ctx pane.
    fake.serve(session, repo, capture=_idle_capture(ctx=40))
    sup.evaluate(track, act=True)
    assert sup._inject[_key_for(repo, topic)].count == 1
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
    assert by_topic["mapped"].status == "idle"
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
    assert ("respawn", session, str(repo), f"claude -n {topic}") in fake.calls
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
    """The de-gold-plated CLI (2026-07-13): the removed --store/--stamp/--repos/
    --repos-only/--manifest flags and the old positional repo/topic are all
    rejected; --repo/--topic are required keyword flags."""
    _isolate_store(tmp_path, monkeypatch)
    repo = str(tmp_path / "repo")
    # Removed watch-set / store / stamp knobs are unrecognized now.
    removed = (
        ["add", "--store", str(tmp_path / "x"), "--repo", repo, "--topic", "t"],
        ["add", "--repo", repo, "--topic", "t", "--stamp", str(tmp_path / "x")],
        ["daemon", "--repos", repo],
        ["daemon", "--repos-only"],
        ["daemon", "--manifest", str(tmp_path / "m.jsonc")],
        ["list", "--store", str(tmp_path / "x")],
    )
    for argv in removed:
        with pytest.raises(SystemExit):
            supervisor.main(argv)
    # The old positional form is gone; --repo and --topic are required.
    for argv in (["add", repo, "t"], ["add", "--repo", repo], ["start", "--topic", "t"]):
        with pytest.raises(SystemExit):
            supervisor.main(argv)


def test_daemon_takes_no_required_args(monkeypatch):
    """`daemon` runs argless: no watch-set/store/stamp flags, defaults applied."""
    seen: dict[str, object] = {}

    class _RunOnlySup:
        def run(self, *, interval, once, recover):
            seen["args"] = (interval, once, recover)

    monkeypatch.setattr(supervisor, "_build_supervisor", lambda: _RunOnlySup())
    assert supervisor.main(["daemon"]) == 0
    assert seen["args"] == (supervisor.LOOP_INTERVAL_SECONDS, False, False)


def test_wrapup_message_has_required_placeholders_filled():
    msg = supervisor.wrapup_message(
        threshold=50, handoff="/r/plan/t/handoff.md", repo="/r", topic="t"
    )
    assert "under 50%" in msg
    assert "/r/plan/t/handoff.md" in msg
    assert "/r/plan/t/.overseer-ready" in msg
    assert "/r/plan/t/.overseer-blocked" in msg


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
    assert not fake.has("paste")  # never injected despite ctx 40 <= 50


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
