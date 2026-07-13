"""supervisor.py — the overseer daemon: poll loop, state machine, table, CLI.

Stdlib-only, host-only (see ``registry.py`` header — the whole skill folder is
outside the livespec product gates). This module *acts and renders*; it holds
NO semantic judgment. Every "am I done / blocked?" decision is made by the
tracked session's own LLM and expressed out-of-band on the filesystem
(``.overseer-ready`` / ``.overseer-blocked`` marker files); this daemon only
pattern-matches deterministic tmux signals and those markers.

It builds on the already-merged pure-logic core:
  - ``registry.py`` — discovery ⋈ mapping, the JSONL store, injection stamps.
  - ``signals.py``  — pane parsing (busy / gate / idle / ctx%) + marker
    certification (``ready_marker_valid`` / ``blocked_marker``).
  - ``tmuxio.py``   — the single tmux subprocess boundary (injectable, faked in
    tests).

Per-tick state machine (precedence, top to bottom — working / blocked:human are
detected FIRST so injection is suppressed there):

    working        is_busy                              → leave alone
    blocked:human  is_structured_gate OR .overseer-blocked → surface; suppress inject
    restarting     ready_marker_valid AND idle-input     → respawn + resume + delete marker
    warned/danger  ctx ≤ threshold AND idle-input        → stamp-then-paste wrap-up (danger surfaces)
    idle           ctx > threshold                       → leave alone
    settling       pane present but not verified idle     → wait

``restarting`` is checked BEFORE ``warned`` on purpose: a valid ready marker
means the session already certified it is done, so it supersedes any re-warn.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import os
import shlex
import sys
import time
import traceback
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import IO

import registry
import signals
import tmuxio

__all__ = [
    "DANGER_CTX_REMAINING",
    "LOOP_INTERVAL_SECONDS",
    "WRAPUP_TEMPLATE",
    "RowView",
    "Supervisor",
    "default_resume",
    "main",
    "wrapup_message",
]

# ~10s fast loop (design). Configurable via the daemon CLI ``--interval``.
LOOP_INTERVAL_SECONDS = 10

# The "danger" line, expressed in REMAINING-context percent: ~20% left ≈ 80%
# used. At/below this with no valid ready marker the daemon SURFACES the stall
# to the human — it NEVER force-kills a session mid-work (design).
DANGER_CTX_REMAINING = 20

# Bounded wait for a respawned pane to become a live Claude TUI before pasting
# the resume line (poll #{pane_current_command} → node/claude; never scrape ❯).
_RESTART_POLL_MAX = 30
_RESTART_POLL_INTERVAL = 0.5

# Delay between the two captures of the settled-check. The live Claude TUI shows
# NO persistent busy spinner while streaming tokens (verified 2026-07-13), so a
# single capture cannot tell active streaming from idle. Before acting on an
# apparently-idle track, the daemon captures twice this far apart; if the pane
# changed, it is actively working and is skipped (treated as `working`).
_SETTLE_DELAY = 0.6

# Submit verification: a single Enter after a bracketed paste can be DROPPED by a
# freshly-respawned session still drawing its welcome screen (verified live
# 2026-07-13), leaving the resume line un-submitted. `_submit_prompt` re-sends
# Enter up to this many times, polling `_SUBMIT_POLL` between, until the input box
# clears. Extra Enters on an empty prompt are harmless no-ops.
_SUBMIT_MAX_ENTERS = 8
_SUBMIT_POLL = 0.5


# --------------------------------------------------------------------------- #
# The wrap-up message + resume line. Single-sourced here so Build C's
# convention doc and tracked-session handoffs reference the SAME text.
# --------------------------------------------------------------------------- #

WRAPUP_TEMPLATE = """\
Your context is now under {n}%. Wrap up for a clean session restart:
 1. Update {handoff} so a FRESH session can resume from it alone
    (read-first chain present, concrete next action, resume command printed).
 2. Stop every background sub-agent and subprocess you started.
 3. ONLY when genuinely at a clean stopping point with the handoff ready,
    WRITE the ready marker (do not merely print it), then stop:
        sha256sum {handoff} | cut -d' ' -f1 > {repo}/plan/{topic}/.overseer-ready
 If instead you are blocked on a human decision, write:
        echo "<one-line summary>" > {repo}/plan/{topic}/.overseer-blocked"""


def wrapup_message(*, threshold: int, handoff: str, repo: str, topic: str) -> str:
    """The exact wrap-up text injected when a track crosses its ctx threshold.

    ``threshold`` fills ``{N}`` (the "under N%"); ``handoff`` is the absolute
    handoff path; ``repo``/``topic`` build the marker paths the session writes.
    """
    return WRAPUP_TEMPLATE.format(n=threshold, handoff=handoff, repo=repo, topic=topic)


def default_handoff(repo: str, topic: str) -> str:
    """``<repo>/plan/<topic>/handoff.md`` — the discovery-convention handoff path."""
    return str(Path(repo) / "plan" / topic / "handoff.md")


def default_resume(repo: str, topic: str) -> str:
    """The first prompt pasted into a (re)started session: read the handoff."""
    return f"read {default_handoff(repo, topic)} and follow it"


def _key(repo: str, topic: str) -> tuple[str, str]:
    """The normalized (repo, topic) in-memory state key (mirrors registry joins)."""
    return (os.path.normpath(repo), topic)


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# View + per-track internal state.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, kw_only=True)
class RowView:
    """One rendered table row: the outward projection of a track this tick."""

    topic: str
    repo: str
    tmux: str | None
    ctx: int | None
    status: str
    note: str | None = None


@dataclass
class _InjectState:
    """Per-track wrap-up bookkeeping (in-memory; reset on restart/recovery).

    ``count`` caps injections at 2 (first + one re-send). ``ctx_at_last`` is the
    remaining-% at the last injection, so a re-send fires only if ctx kept
    dropping. ``last_ctx`` is the last KNOWN remaining-% (used when a tick reads
    ctx as unknown — design: keep last known, unknown never triggers).
    """

    count: int = 0
    ctx_at_last: int | None = None
    last_ctx: int | None = None


# --------------------------------------------------------------------------- #
# The daemon.
# --------------------------------------------------------------------------- #


@dataclass
class Supervisor:
    """The deterministic multi-track supervisor.

    All external state is injectable so tests drive it with a fake ``tmux`` and
    ``tmp_path`` stores — no real tmux, no touching ``~``. ``watch_repos`` may
    be given explicitly (tests) or computed from a fleet manifest (daemon CLI).
    """

    tmux: object = field(default_factory=tmuxio.TmuxIO)
    store_path: str | os.PathLike[str] | None = None
    stamp_path: str | os.PathLike[str] | None = None
    watch_repos: list[str] | None = None
    manifest_path: str | os.PathLike[str] | None = None
    extra_repos: list[str] = field(default_factory=list)
    out: object = None  # writable stream for the table (default: sys.stdout)
    now: Callable[[], float] = time.time
    sleep: Callable[[float], None] = time.sleep
    _inject: dict[tuple[str, str], _InjectState] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.out is None:
            self.out = sys.stdout

    # ----------------------------------------------------------------- #
    # Diagnostics.
    # ----------------------------------------------------------------- #

    def _log(self, message: str) -> None:
        print(f"overseer: {message}", file=sys.stderr)

    def _surface(self, message: str) -> None:
        """Surface a gate / stall to the operator (stderr; the bottom pane reads it)."""
        print(f"overseer[SURFACE]: {message}", file=sys.stderr)

    # ----------------------------------------------------------------- #
    # Watch-set + discovery ⋈ mapping.
    # ----------------------------------------------------------------- #

    def _resolve_watch(self) -> list[str]:
        if self.watch_repos is not None:
            return [os.path.normpath(r) for r in self.watch_repos]
        if self.manifest_path is not None:
            return registry.watch_set(self.manifest_path, self.extra_repos)
        return [os.path.normpath(r) for r in self.extra_repos]

    def archive_gc(self) -> int:
        """Drop mapping rows whose ``<repo>/plan/<topic>/`` is archived or gone."""

        def keep(row: dict[str, object]) -> bool:
            repo = row.get("repo")
            topic = row.get("topic")
            if not isinstance(repo, str) or not isinstance(topic, str):
                return True  # fail-soft: never drop a row we can't evaluate
            if not registry.repo_root_present(repo):
                # Repo root itself unreachable (unmounted / mid-move) — KEEP the row
                # and surface, so a transient outage does not permanently drop it and
                # lose its custom overrides on the auto-link re-add (B6).
                self._surface(f"repo root missing for {repo}::{topic}; keeping mapping row")
                return True
            if registry.archived_or_gone(repo, topic):
                self._log(f"archive-GC dropping mapping row {repo}::{topic}")
                return False
            return True

        return registry.rewrite_mapping(keep, self.store_path)

    def auto_link(self, track: registry.Track) -> registry.Track | None:
        """Link a live session to an unassigned discovered plan — safely.

        A link is created ONLY when a session named ``<repo-slug>--<topic>``
        exists AND its ``#{pane_current_path}`` resolves inside the row's repo.
        Never by topic name alone (blocker #8): two repos sharing a topic must
        not cross-link. Returns the new mapped Track, or None if not linked.
        """
        session = registry.tmux_id(track.repo, track.topic)
        if not self.tmux.session_exists(session):
            return None
        path = self.tmux.pane_current_path(session)
        if not signals.path_in_repo(path, track.repo):
            return None
        linked = registry.Track(
            topic=track.topic,
            repo=track.repo,
            tmux=session,
            handoff=track.handoff or default_handoff(track.repo, track.topic),
            resume=default_resume(track.repo, track.topic),
        )
        registry.append_mapping(linked, self.store_path, added_at=_iso_now())
        self._log(f"auto-linked live session {session} → {track.repo}::{track.topic}")
        return linked

    def build_rows(self, *, act: bool = True) -> list[registry.Track]:
        """Discovery ⋈ mapping (the tick's row set).

        When ``act`` (the daemon loop) this runs archive-GC + auto-link, both of
        which MUTATE the store. When NOT ``act`` (the ``list`` command, advertised
        read-only) it does NEITHER — it just joins discovery against the current
        mapping, so `list` cannot silently rewrite / GC / re-link the store out
        from under a running daemon (adversarial code review 2026-07-13, blocker
        B6).
        """
        watch = self._resolve_watch()
        discovered = registry.discover_plans(watch)
        if not act:
            return registry.join(discovered, registry.read_mapping(self.store_path))
        self.archive_gc()
        rows = registry.join(discovered, registry.read_mapping(self.store_path))
        linked_any = False
        for row in rows:
            if row.is_unassigned and self.auto_link(row) is not None:
                linked_any = True
        if linked_any:
            rows = registry.join(discovered, registry.read_mapping(self.store_path))
        return rows

    # ----------------------------------------------------------------- #
    # Per-track evaluation (the state machine).
    # ----------------------------------------------------------------- #

    def _session_of(self, track: registry.Track) -> str:
        return track.tmux or registry.tmux_id(track.repo, track.topic)

    def _effective_ctx(self, key: tuple[str, str], current: int | None) -> int | None:
        """Current remaining-%, or the last known if this tick read unknown.

        Design: unknown ⇒ keep last known, and unknown NEVER counts as a
        threshold crossing (so a never-known track stays None and cannot warn).
        """
        state = self._inject.setdefault(key, _InjectState())
        if current is not None:
            state.last_ctx = current
            return current
        return state.last_ctx

    def _pane_settled(self, session: str) -> bool:
        """True if two captures ~``_SETTLE_DELAY`` apart are identical.

        A single capture cannot distinguish active token-streaming from idle —
        the live Claude TUI renders no persistent busy spinner while streaming
        (verified 2026-07-13). Before the daemon INJECTS or RESTARTS an
        apparently-idle track, it confirms the pane is not actively changing. A
        changing pane is treated as busy (`working`) and skipped this tick —
        over-firing busy is the safe direction.
        """
        first = signals.strip_ansi(self.tmux.capture_pane(session))
        self.sleep(_SETTLE_DELAY)
        second = signals.strip_ansi(self.tmux.capture_pane(session))
        return first == second

    def _pane_is_managed_claude(self, session: str, repo: str) -> bool:
        """True iff ``session``'s pane is a live Claude TUI whose cwd is inside ``repo``.

        The identity gate for EVERY act (inject / restart). ``pane_is_claude`` and
        ``path_in_repo`` exist and are tested, but the shipped daemon wired them
        only into auto-link and the restart poll, NOT the act path — so a tracked
        Claude that had exited to a shell (the pane retains the dead TUI's idle-box
        frame) would get the wrap-up pasted INTO THE SHELL, where the
        ``sha256sum … > .overseer-ready`` line executes and FORGES a hash-valid
        marker (adversarial code review 2026-07-13, blocker B3 = Codex #1). Gating
        every act on process identity + cwd closes that, and hardens B1's residual
        (a name that resolved to the wrong session would fail the cwd check).
        """
        if not signals.pane_is_claude(self.tmux.pane_current_command(session)):
            return False
        return signals.path_in_repo(self.tmux.pane_current_path(session), repo)

    def _void_ready_marker(self, track: registry.Track) -> None:
        """Delete a track's ready marker AND clear its injection stamp (round closed).

        Used both after a successful restart and when a track that had a valid ready
        marker is next seen BUSY or BLOCKED — i.e. the session began NEW work, or a
        human resumed the pane, AFTER certifying. Voiding the certification on the
        FILESYSTEM (not merely in memory) makes it durable across a daemon restart,
        so a freshly-started daemon cannot respawn-kill a session a human has since
        taken over (adversarial code review 2026-07-13, blocker B4).
        """
        try:
            signals.ready_marker_path(track.repo, track.topic).unlink(missing_ok=True)
        except OSError as exc:
            self._log(f"could not delete ready marker for {track.repo}::{track.topic}: {exc}")
        registry.clear_injection_stamp(track.repo, track.topic, self.stamp_path)

    def evaluate(self, track: registry.Track, *, act: bool) -> RowView:
        """Derive a track's status and (when ``act``) perform its side effects.

        ``act=False`` is the read-only path used by the ``list`` command: it
        captures the pane and reads markers but performs NO paste / respawn /
        stamp write. The daemon loop calls with ``act=True``.
        """
        if track.is_unassigned:
            return RowView(
                topic=track.topic, repo=track.repo, tmux=None, ctx=None, status="unassigned"
            )

        repo, topic = track.repo, track.topic
        session = self._session_of(track)
        key = _key(repo, topic)

        if not self.tmux.session_exists(session):
            return RowView(topic=topic, repo=repo, tmux=session, ctx=None, status="session-gone")

        # Identity gate (B3): the mapped session exists, but before reading its pane
        # for any ACT we confirm it is really OUR Claude in OUR repo — never
        # keystroke into a shell / wrong session / human split-pane.
        if not self._pane_is_managed_claude(session, repo):
            return RowView(topic=topic, repo=repo, tmux=session, ctx=None, status="not-claude")

        capture = self.tmux.capture_pane(session)
        busy = signals.is_busy(capture)
        gate = signals.is_structured_gate(capture)
        idle = signals.is_idle_input(capture)
        blocked = signals.blocked_marker(repo, topic)
        current_ctx = signals.parse_ctx_remaining(capture)
        eff_ctx = self._effective_ctx(key, current_ctx)

        handoff = track.handoff or default_handoff(repo, topic)
        stamp = registry.read_injection_stamp(repo, topic, self.stamp_path)
        ready = signals.ready_marker_valid(repo, topic, handoff, stamp)

        threshold = track.ctx_threshold

        # Precedence, top to bottom. Single-capture `busy` and the human gates
        # are checked first. For an apparently-idle track that would ACT
        # (restart / inject), the daemon first confirms the pane is SETTLED
        # (`_pane_settled`) — a single frame can't see active token-streaming, so
        # a changing pane is treated as `working` and skipped this tick.
        if busy:
            status = "working"
            if act and ready:
                # The session started NEW work after certifying done — void the
                # now-contradicted certification durably (B4).
                self._void_ready_marker(track)
                ready = False
                self._log(f"voided ready marker for {repo}::{topic} (busy after certifying)")
        elif gate or blocked is not None:
            status = "blocked:human"
            if act:
                if ready:
                    self._void_ready_marker(track)
                    ready = False
                detail = blocked if blocked else "structured gate on pane"
                self._surface(f"{repo}::{topic} blocked on human: {detail}")
        elif not idle:
            # Pane present but not a verified idle-input state and not busy —
            # a transient/settling capture. Wait; never act.
            status = "settling"
        elif act and not self._pane_settled(session):
            # One frame looks idle, but the pane is actively changing (streaming).
            status = "working"
        elif ready:
            status = "restarting"
            if act:
                self._do_restart(track, session)
        elif eff_ctx is not None and eff_ctx <= threshold:
            if act:
                self._maybe_inject(track, session, eff_ctx, handoff)
            if eff_ctx <= DANGER_CTX_REMAINING and not ready:
                status = "danger"
                if act:
                    self._surface(
                        f"{repo}::{topic} won't wrap up (ctx {eff_ctx}% left, no ready marker)"
                    )
            else:
                status = "warned"
        else:
            status = "idle"

        return RowView(
            topic=topic,
            repo=repo,
            tmux=session,
            ctx=eff_ctx,
            status=status,
            note=blocked if blocked else None,
        )

    def _maybe_inject(
        self, track: registry.Track, session: str, eff_ctx: int, handoff: str
    ) -> None:
        """Inject the wrap-up once per round; re-send once if ctx keeps dropping.

        The injection stamp is written BEFORE the paste (design) so any ready
        marker the session subsequently writes has ``mtime > stamp`` and thus
        certifies. On the re-send the stamp is NOT rewritten — that would
        invalidate a marker already written in response to the first injection.
        """
        key = _key(track.repo, track.topic)
        state = self._inject.setdefault(key, _InjectState())
        message = wrapup_message(
            threshold=track.ctx_threshold, handoff=handoff, repo=track.repo, topic=track.topic
        )
        if state.count == 0:
            # Stamp BEFORE the paste (design) so a marker the session writes has
            # mtime > stamp. If the paste/submit FAILS, clear the stamp and do NOT
            # advance count — the round never opened, so the next tick retries
            # instead of the wrap-up being accounted as sent (B5).
            registry.write_injection_stamp(track.repo, track.topic, self.now(), self.stamp_path)
            if self._submit_prompt(session, message):
                state.count = 1
                state.ctx_at_last = eff_ctx
                self._log(f"injected wrap-up into {track.repo}::{track.topic} (ctx {eff_ctx}%)")
            else:
                registry.clear_injection_stamp(track.repo, track.topic, self.stamp_path)
                self._surface(f"{track.repo}::{track.topic} wrap-up injection failed; will retry")
        elif state.count == 1 and state.ctx_at_last is not None and eff_ctx < state.ctx_at_last:
            if self._submit_prompt(session, message):  # stamp preserved from the first inject
                state.count = 2
                state.ctx_at_last = eff_ctx
                self._log(f"re-sent wrap-up into {track.repo}::{track.topic} (ctx {eff_ctx}%)")
            else:
                self._surface(f"{track.repo}::{track.topic} wrap-up re-send failed")

    def _do_restart(self, track: registry.Track, session: str) -> None:
        """Atomic restart interlock: respawn → wait Claude → resume → close the round.

        Every tmux step is a HARD GATE (B5). If ``respawn-pane`` fails, or the
        pane never becomes a live Claude, the daemon SURFACES the failure and
        RETURNS WITHOUT deleting the ready marker — so the session's certification
        is preserved and the restart is retried, never silently destroyed. The
        marker is voided (and the injection stamp cleared — B4) only once the
        respawn is confirmed; the resume-submit result is surfaced but does not
        block voiding, because the fresh Claude IS up (a stale marker would else
        re-restart and kill it, and B3's identity gate already blocks re-acting on
        a non-Claude pane).
        """
        if not self.tmux.respawn_pane(session, track.repo, self._launch_command(track)):
            self._surface(
                f"{track.repo}::{track.topic} restart respawn FAILED; keeping ready marker"
            )
            return
        if not self._await_claude(session):
            self._surface(
                f"{track.repo}::{track.topic} respawned pane never became Claude; keeping ready marker"
            )
            return
        resume = track.resume or default_resume(track.repo, track.topic)
        if not self._submit_prompt(session, resume):
            self._surface(f"{track.repo}::{track.topic} resume line not submitted after restart")
        self._void_ready_marker(track)
        self._inject.pop(_key(track.repo, track.topic), None)
        self._log(f"restarted {track.repo}::{track.topic} (session {session})")

    @staticmethod
    def _launch_command(track: registry.Track) -> str:
        """``claude -n <topic>`` with the topic shell-quoted (defensive, B-nit)."""
        return f"claude -n {shlex.quote(track.topic)}"

    def _await_claude(self, session: str) -> bool:
        """Poll ``#{pane_current_command}`` until it is a live Claude TUI, bounded.

        Never scrape the ``❯`` prompt glyph (ambiguous shell/Claude); wait on the
        process identity (design). Returns False if it never became Claude.
        """
        for _ in range(_RESTART_POLL_MAX):
            if signals.pane_is_claude(self.tmux.pane_current_command(session)):
                return True
            self.sleep(_RESTART_POLL_INTERVAL)
        return False

    def _submit_prompt(self, session: str, text: str) -> bool:
        """Bracketed-paste a payload, then submit it — re-sending Enter until the
        input box clears. Returns True iff the paste LANDED and the box CLEARED.

        The paste is atomic (never fragments — blocker #2). A SINGLE Enter is
        enough on a steady idle session, but a freshly-`respawn`-ed session is
        often still drawing its welcome/news screen when the Enter arrives, and
        that first Enter is dropped — leaving the resume line un-submitted and the
        auto-restart stalled (verified live 2026-07-13). So we verify: after each
        Enter, confirm the empty `❯` box is back (`signals.input_box_ready`,
        which does NOT require not-busy, so a now-working pane also reads
        submitted); re-send up to `_SUBMIT_MAX_ENTERS` times. An extra Enter on an
        already-empty prompt is a harmless no-op (Claude never submits an empty
        message).

        Returning a bool (B5): callers must know whether the payload actually
        went in. A failed ``bracketed_paste`` is a hard False — WITHOUT it the box
        would still read empty and a never-delivered wrap-up/resume would be
        counted as sent (the paste-failure false-success the maintainer flagged).
        """
        if not self.tmux.bracketed_paste(session, text):
            self._log(f"bracketed paste FAILED for session {session}")
            return False
        self.sleep(_RESTART_POLL_INTERVAL)
        for _ in range(_SUBMIT_MAX_ENTERS):
            self.tmux.send_keys(session, "Enter")
            self.sleep(_SUBMIT_POLL)
            if signals.input_box_ready(self.tmux.capture_pane(session)):
                return True
        return False

    # ----------------------------------------------------------------- #
    # Reboot recovery (startup-only, never per-tick).
    # ----------------------------------------------------------------- #

    def recover_missing_sessions(self) -> list[str]:
        """Recreate any mapped session that is not currently live (design).

        Run ONCE at daemon startup: a fresh overseer reads the mapping, and for
        each row whose ``<repo-slug>--<topic>`` session is gone, creates the
        session, launches ``claude -n <topic>`` in the repo, and pastes the
        resume line. Not a per-tick action (a session the user deliberately
        kills should not be revived every 10s). Returns the recovered names.
        """
        recovered: list[str] = []
        for track in registry.read_mapping(self.store_path):
            session = self._session_of(track)
            if self.tmux.session_exists(session):
                continue
            self.tmux.new_session(session, track.repo)
            if self._do_launch(track, session):
                recovered.append(session)
                self._log(f"reboot-recovery recreated {session} for {track.repo}::{track.topic}")
            else:
                self._surface(
                    f"reboot-recovery FAILED to launch {session} for {track.repo}::{track.topic}"
                )
        return recovered

    def _do_launch(self, track: registry.Track, session: str) -> bool:
        """Launch ``claude -n <topic>`` into ``session`` and paste the resume line.

        Returns True iff respawn succeeded, the pane became a live Claude, and the
        resume line submitted — so callers (`recover`, `start`) can surface a
        failure rather than silently claim a launch happened (B5).
        """
        if not self.tmux.respawn_pane(session, track.repo, self._launch_command(track)):
            return False
        if not self._await_claude(session):
            return False
        resume = track.resume or default_resume(track.repo, track.topic)
        return self._submit_prompt(session, resume)

    # ----------------------------------------------------------------- #
    # Table rendering.
    # ----------------------------------------------------------------- #

    def render(self, rows: Iterable[RowView]) -> None:
        """Clear the screen and print the live ``Topic · Repo · tmux · Ctx% · Status`` table.

        Re-rendered from live captures every tick, and stamped with the current
        wall-clock time, so a ``/clear``-orphaned pane can never freeze on a
        stale "all idle" snapshot (the second historical failure mode).
        """
        rows = list(rows)
        lines: list[str] = []
        lines.append(f"overseer — {_iso_now()} — {len(rows)} track(s)")
        header = ("Topic", "Repo", "tmux", "Ctx%", "Status")
        table = [header]
        for row in rows:
            table.append(
                (
                    row.topic,
                    registry.repo_slug(row.repo),
                    row.tmux or "—",
                    "—" if row.ctx is None else f"{row.ctx}%",
                    row.status if not row.note else f"{row.status} ({row.note})",
                )
            )
        widths = [max(len(r[i]) for r in table) for i in range(len(header))]
        for i, cells in enumerate(table):
            lines.append("  ".join(cell.ljust(widths[j]) for j, cell in enumerate(cells)))
            if i == 0:
                lines.append("  ".join("-" * widths[j] for j in range(len(header))))
        # Clear scrollback + screen + home, then the table.
        self.out.write("\x1b[3J\x1b[2J\x1b[H" + "\n".join(lines) + "\n")
        self.out.flush()

    # ----------------------------------------------------------------- #
    # Tick + loop.
    # ----------------------------------------------------------------- #

    def tick(self, *, act: bool = True) -> list[RowView]:
        """One loop iteration: build rows, evaluate each, render the table."""
        views = [self.evaluate(track, act=act) for track in self.build_rows(act=act)]
        self.render(views)
        return views

    # ----------------------------------------------------------------- #
    # Singleton daemon lock (per store).
    # ----------------------------------------------------------------- #

    def _singleton_lock_path(self) -> Path:
        store = (
            Path(self.store_path) if self.store_path is not None else registry.DEFAULT_STORE_PATH
        )
        return Path(str(store) + ".daemon.lock")

    def _acquire_singleton_lock(self) -> IO[str] | None:
        """Non-blocking flock on a per-store lockfile; None if another daemon holds it.

        Two overseer daemons on the same store double-inject and double-restart —
        B's ``respawn-pane -k`` can kill the fresh session A just resumed
        (adversarial code review 2026-07-13, blocker B6 = Codex #3). Keyed to the
        store path so a scratch-store live-exercise run never contends with the
        real daemon. Fail-soft: on any OSError, return None (treat as contended).
        """
        path = self._singleton_lock_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            handle = path.open("w", encoding="utf-8")
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return None
        return handle

    @staticmethod
    def _release_singleton_lock(handle: IO[str] | None) -> None:
        if handle is not None:
            with contextlib.suppress(OSError):
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()

    def run(
        self, *, interval: float = LOOP_INTERVAL_SECONDS, once: bool = False, recover: bool = False
    ) -> None:
        """Run the poll loop. ``once`` runs a single tick (live-exercise/testing).

        Holds a per-store singleton lock for its whole lifetime (B6) and wraps each
        tick in a broad except so one bad input (an unreadable ``plan/`` dir, a
        malformed store) is logged and the loop CONTINUES supervising the other
        tracks rather than dying (B7). ``KeyboardInterrupt``/``SystemExit`` still
        propagate (they are BaseException, not caught here).
        """
        lock = self._acquire_singleton_lock()
        if lock is None:
            self._surface(
                f"another overseer daemon holds {self._singleton_lock_path()}; refusing to start"
            )
            return
        try:
            if recover:
                self.recover_missing_sessions()
            while True:
                try:
                    self.tick(act=True)
                except KeyboardInterrupt:
                    self._log("interrupted; exiting")
                    return
                except Exception:
                    self._log("tick error (continuing):\n" + traceback.format_exc())
                if once:
                    return
                self.sleep(interval)
        finally:
            self._release_singleton_lock(lock)


# --------------------------------------------------------------------------- #
# CLI. The daemon NEVER calls `start` — launching a session is surface-only.
# --------------------------------------------------------------------------- #


def _default_manifest() -> Path:
    """``<core-repo>/.livespec-fleet-manifest.jsonc`` relative to this script."""
    return Path(__file__).resolve().parents[3] / ".livespec-fleet-manifest.jsonc"


def _supervisor_from_args(args: argparse.Namespace) -> Supervisor:
    extra = [r for r in (args.repos.split(",") if getattr(args, "repos", None) else []) if r]
    watch = extra if getattr(args, "repos_only", False) else None
    return Supervisor(
        store_path=getattr(args, "store", None),
        stamp_path=getattr(args, "stamp", None),
        watch_repos=watch,
        manifest_path=(None if watch is not None else getattr(args, "manifest", None)),
        extra_repos=extra,
    )


def _upsert(store_path: object, track: registry.Track) -> None:
    """Replace any existing (repo, topic) mapping row, then append (one row each)."""
    registry.remove_mapping(track.repo, track.topic, store_path)
    registry.append_mapping(track, store_path, added_at=_iso_now())


def _cmd_daemon(args: argparse.Namespace) -> int:
    sup = _supervisor_from_args(args)
    sup.run(interval=args.interval, once=args.once, recover=args.recover)
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    sup = _supervisor_from_args(args)
    sup.tick(act=False)  # read-only render: no injection/restart
    return 0


def _cmd_add(args: argparse.Namespace) -> int:
    repo = os.path.normpath(args.repo)
    track = registry.Track(
        topic=args.topic,
        repo=repo,
        tmux=registry.tmux_id(repo, args.topic),
        handoff=default_handoff(repo, args.topic),
        resume=default_resume(repo, args.topic),
    )
    _upsert(getattr(args, "store", None), track)
    print(f"added mapping {repo}::{args.topic} (tmux {track.tmux})")
    return 0


def _cmd_remove(args: argparse.Namespace) -> int:
    removed = registry.remove_mapping(
        os.path.normpath(args.repo), args.topic, getattr(args, "store", None)
    )
    print(f"removed {removed} mapping row(s) for {args.repo}::{args.topic}")
    return 0


def _cmd_start(args: argparse.Namespace) -> int:
    """Surface-only, user-initiated launch. The daemon never invokes this.

    Guarded (B8): if the session already runs a LIVE Claude, ``start`` does NOT
    ``respawn-pane -k`` it (that would kill a mid-work session with no interlock —
    the exact "never force-kill mid-work" violation the whole design exists to
    prevent, reachable via a repeated bottom-pane ``start``). It just upserts the
    mapping and reports. ``--force`` is required to actually respawn a live one.
    """
    repo = os.path.normpath(args.repo)
    topic = args.topic
    session = registry.tmux_id(repo, topic)
    force = getattr(args, "force", False)
    io = tmuxio.TmuxIO()
    sup = Supervisor(tmux=io, store_path=getattr(args, "store", None), stamp_path=None)
    track = registry.Track(
        topic=topic,
        repo=repo,
        tmux=session,
        handoff=default_handoff(repo, topic),
        resume=default_resume(repo, topic),
    )
    if (
        io.session_exists(session)
        and signals.pane_is_claude(io.pane_current_command(session))
        and not force
    ):
        _upsert(getattr(args, "store", None), track)
        print(
            f"{repo}::{topic}: session {session} already runs a live Claude — mapping upserted, "
            f"NOT respawned. Pass --force to respawn (kills the running session)."
        )
        return 0
    if not io.session_exists(session):
        io.new_session(session, repo)
    if not sup._do_launch(track, session):
        print(f"start FAILED to launch {repo}::{topic} in tmux session {session}", file=sys.stderr)
        return 1
    _upsert(getattr(args, "store", None), track)
    print(f"started {repo}::{topic} in tmux session {session}")
    return 0


def _add_store_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--store", default=None, help="mapping store path (default: ~/.livespec-overseer.jsonl)"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="overseer", description="livespec overseer supervisor daemon"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def _watch_args(p: argparse.ArgumentParser) -> None:
        _add_store_args(p)
        p.add_argument("--stamp", default=None, help="injection-stamp sidecar path")
        p.add_argument("--manifest", default=str(_default_manifest()), help="fleet manifest path")
        p.add_argument("--repos", default=None, help="comma-separated extra repo paths")
        p.add_argument(
            "--repos-only",
            action="store_true",
            help="watch ONLY --repos (ignore the manifest)",
        )

    p_daemon = sub.add_parser("daemon", help="run the poll loop + live table")
    _watch_args(p_daemon)
    p_daemon.add_argument("--interval", type=float, default=LOOP_INTERVAL_SECONDS)
    p_daemon.add_argument("--once", action="store_true", help="run a single tick and exit")
    p_daemon.add_argument(
        "--recover", action="store_true", help="recreate missing sessions at startup"
    )
    p_daemon.set_defaults(func=_cmd_daemon)

    p_list = sub.add_parser("list", help="print the current joined table once (read-only)")
    _watch_args(p_list)
    p_list.set_defaults(func=_cmd_list)

    p_add = sub.add_parser("add", help="add a (repo, topic) mapping row")
    _add_store_args(p_add)
    p_add.add_argument("repo")
    p_add.add_argument("topic")
    p_add.set_defaults(func=_cmd_add)

    p_remove = sub.add_parser("remove", help="remove a (repo, topic) mapping row")
    _add_store_args(p_remove)
    p_remove.add_argument("repo")
    p_remove.add_argument("topic")
    p_remove.set_defaults(func=_cmd_remove)

    # unassign is a synonym for remove: drop the mapping so the plan reverts to
    # `unassigned` (never force-kills the session — surface-only).
    p_unassign = sub.add_parser("unassign", help="detach a plan's mapping (revert to unassigned)")
    _add_store_args(p_unassign)
    p_unassign.add_argument("repo")
    p_unassign.add_argument("topic")
    p_unassign.set_defaults(func=_cmd_remove)

    p_start = sub.add_parser("start", help="surface-only: launch a session for a plan and map it")
    _add_store_args(p_start)
    p_start.add_argument("repo")
    p_start.add_argument("topic")
    p_start.add_argument(
        "--force",
        action="store_true",
        help="respawn even if the session already runs a live Claude (kills it)",
    )
    p_start.set_defaults(func=_cmd_start)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
