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
        self.pane_pids = {}  # {pane_pid: session} for the registry→tmux adopt join
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
    blocked = signals.blocked_marker_path(str(repo), topic)
    blocked.parent.mkdir(parents=True, exist_ok=True)  # <repo>/tmp/overseer/<topic>/
    blocked.write_text("waiting on schema call\n")
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
    fake.serve(session, repo, capture=_idle_capture(ctx=40))  # below default threshold 45
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


def _wrapup_count(fake):
    return len([t for t in fake.paste_texts() if "Wrap up for a clean session restart" in t])


def test_escalates_one_paste_per_band_as_ctx_drops(tmp_path):
    """Part 2: warn ONCE at the threshold, then once more each time remaining
    crosses a lower 10%-band (40, 30, 20, 10) — each band at most once. Feeding
    ctx exactly at each band yields exactly one NEW wrap-up paste per band; a
    re-tick at the same low ctx (all bands already notified) adds none."""
    repo, topic = _make_plan(tmp_path)
    session = registry.tmux_id(str(repo), topic)
    fake = FakeTmux()
    fake.serve(session, repo)
    sup = _sup(tmp_path, fake)  # warn_percent default 45
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
    sup = _sup(tmp_path, fake)
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
    sup = _sup(tmp_path, fake)
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
    assert view.status == "idle"
    assert not fake.has("paste")
    # Drop to the daemon-wide threshold → warns.
    fake.panes[session] = _idle_capture(ctx=30)
    view = sup.evaluate(track, act=True)
    assert view.status == "warned"
    assert fake.has("paste")


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


def _arm_ready_marker(repo, topic, *, mtime=1001.0):
    """Write a valid ready marker at its TEMP path (mkdir the parent first).

    The marker now lives at ``<repo>/tmp/overseer/<topic>/.overseer-ready`` — its
    parent dir does not exist yet, so create it. Certification is presence +
    freshness only, so the contents need not be a hash of anything.
    """
    marker = signals.ready_marker_path(str(repo), topic)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("ready\n")
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


def _write_session(sessions_dir, pid, *, name, cwd, proc_start="pt"):
    payload = {"pid": pid, "name": name, "cwd": str(cwd), "procStart": proc_start, "status": "idle"}
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


def test_wrapup_message_has_required_placeholders_filled():
    # New signature: remaining=/repo=/topic= (threshold + handoff dropped). The
    # message quotes the CURRENT remaining-% and the TEMP marker dir under
    # <repo>/tmp/overseer/<topic>/ — never a path under plan/.
    msg = supervisor.wrapup_message(remaining=40, repo="/r", topic="t")
    assert "% of your context remaining" in msg
    assert "40% of your context remaining" in msg
    assert "/r/tmp/overseer/t/.overseer-ready" in msg
    assert "/r/tmp/overseer/t/.overseer-blocked" in msg
    # The markers moved OUT of plan/: the old plan-based marker path is absent.
    assert "/r/plan/t/.overseer-ready" not in msg


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
    assert not fake.has("paste")  # never injected despite ctx 40 <= 45


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
