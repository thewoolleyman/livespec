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
    restarting     idle-stall past grace (danger, no marker) → FORCE respawn + resume
    warned/danger  ctx ≤ threshold AND idle-input        → stamp-then-paste wrap-up (danger surfaces)
    idle           ctx > threshold                       → leave alone
    settling       pane present but not verified idle     → wait

``restarting`` is checked BEFORE ``warned`` on purpose: a valid ready marker
means the session already certified it is done, so it supersedes any re-warn.

The auto-restart is NON-NEGOTIABLE (maintainer 2026-07-14): a warned session that
STALLS idle at/below the danger line WITHOUT ever writing ``.overseer-ready`` (it
refused, crashed, ran out of context, or autocompacted) is FORCE-restarted after
a short idle-stall grace — the daemon's whole job is to keep the track moving, so
a missing certification can never wedge a track forever. This is NOT the "never
force-kill mid-work" case: the machine reaches the force-restart ONLY on a
verified idle+settled pane (never busy), so files/worktrees are at a stopping
point and survive ``respawn-pane -k``.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import os
import shlex
import subprocess
import sys
import time
import traceback
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import IO

import claude_sessions
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
# used. At/below this with no valid ready marker the daemon SURFACES the stall to
# the human AND — once the pane has been continuously idle-stalled here for
# ``_STALL_RESTART_GRACE`` — FORCE-RESTARTS it (the non-negotiable auto-restart,
# maintainer 2026-07-14). It still never force-kills a session mid-WORK: the
# force-restart is reached only on a VERIFIED idle+settled pane, never a busy one.
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

# Grace window before a ready marker is voided on a busy/blocked observation. The
# wrap-up protocol makes the session write `.overseer-ready` as the LAST tool
# action of its turn, then the turn's TAIL keeps the pane busy for a while (final
# text streaming + stop hooks, e.g. `(running stop hooks… 1/3 · 24s …)`). Voiding
# on ANY busy would destroy that legitimate certification before the pane ever
# goes idle, breaking the restart in the common case (adversarial code re-review
# 2026-07-13, blocker RB1). So a marker is voided on busy/blocked ONLY once it is
# OLDER than this grace — old enough that the busy cannot be the certifying turn's
# own tail, i.e. the session genuinely resumed work (or a human took over). The
# restart path itself needs no grace: the tail is busy → not idle → restart simply
# waits, then fires when the pane settles idle. Residual (documented): a human who
# takes over AND goes idle WITHIN the grace of a fresh marker could still be
# restarted; a longer takeover is protected.
_MARKER_VOID_GRACE = 120.0

# Idle-stall force-restart grace. The auto-restart is NON-NEGOTIABLE (maintainer
# 2026-07-14): a session warned to wrap up that then STALLS idle at/below the
# danger line WITHOUT ever writing ``.overseer-ready`` (it refused, crashed, ran
# out of context, or autocompacted) MUST still be restarted — the whole point of
# the overseer is to keep the track moving, and a missing certification can never
# be allowed to wedge a track forever. The daemon force-restarts such a track once
# it has been CONTINUOUSLY idle+settled at/below danger for this long. The grace
# (≈9 loop ticks) both lets a late ``.overseer-ready`` still win the clean marker
# path first and gives the human a beat to intervene; it is measured from when the
# idle-danger stall BEGAN (``danger_idle_since``, reset the instant the session
# resumes work), so it counts only a genuine stall, never a brief idle dip between
# wrap-up steps. This is NOT the "never force-kill mid-work" case: the state
# machine reaches the force-restart ONLY on a VERIFIED idle+settled pane (never
# busy — a busy pane is `working` and skipped), so files/worktrees are at a
# stopping point and survive ``respawn-pane -k``.
_STALL_RESTART_GRACE = 90.0


# --------------------------------------------------------------------------- #
# The wrap-up message + resume line. Single-sourced here so Build C's
# convention doc and tracked-session handoffs reference the SAME text.
# --------------------------------------------------------------------------- #

WRAPUP_TEMPLATE = """\
You only have {n}% of your context remaining. Wrap up for a clean session restart.

You WILL be restarted. That is automatic and NOT conditional on your cooperation.
When you stop, this pane is respawned into a fresh session handed exactly ONE prompt:
    read {handoff} and follow it
So {handoff} is the ONLY thing the next session inherits. Do NOT leave your resume
state anywhere else (a scratchpad file, this transcript) — it will be LOST. If your
real pending work has drifted from what that file says, REWRITE that file to
describe the actual next step.

 1. Bring your OWN work to a clean, resumable stopping point, and UPDATE {handoff}
    to match. Your session owns its handoff and everything under plan/; the overseer
    never reads or writes those.
 2. Stop every background sub-agent and subprocess you started.
 3. Then WRITE the ready marker (do not merely print it) and stop:
        mkdir -p {marker_dir} && : > {marker_dir}/.overseer-ready
    It certifies you are done, and restarts you IMMEDIATELY.
 If instead you are blocked on a HUMAN decision you cannot make yourself, write this
 one instead and stop — a blocked track is surfaced to the human, never auto-restarted:
        mkdir -p {marker_dir} && echo "<one-line summary>" > {marker_dir}/.overseer-blocked

Write ONE of the two markers. Declining to write either does NOT prevent the restart —
it only means you get force-restarted later, from a handoff you never refreshed."""


def wrapup_message(*, remaining: int, repo: str, topic: str) -> str:
    """The exact wrap-up text injected when a track crosses a ctx warn band.

    ``remaining`` fills ``{n}`` (the CURRENT remaining-context percent, so an
    escalating re-warn reflects the live value); ``repo``/``topic`` build the
    TEMP marker dir (``<repo>/tmp/overseer/<topic>/``) the session writes into —
    never anything under ``plan/`` — and the ``plan/<topic>/handoff.md`` path the
    restart will resume FROM.

    The message states plainly that the restart is NOT conditional on the session's
    cooperation (invariant 7) and that the handoff is the only inherited artifact.
    A tracked session once REFUSED to certify — reasoning that the resume line
    pointed at a handoff which no longer matched its real pending work, which it had
    stashed in a scratchpad — and thereby wedged its track idle at 13% forever. The
    correct response to that drift is to REWRITE the handoff, not to withhold the
    marker; naming the handoff path here makes that unambiguous. Constructing the
    path is pure string work (``default_handoff``): the overseer POINTS at the
    handoff, exactly as the resume line does, and never opens it.
    """
    marker_dir = str(signals.marker_dir(repo, topic))
    return WRAPUP_TEMPLATE.format(
        n=remaining, marker_dir=marker_dir, handoff=default_handoff(repo, topic)
    )


def default_handoff(repo: str, topic: str) -> str:
    """``<repo>/plan/<topic>/handoff.md`` — the discovery-convention handoff path."""
    return str(Path(repo) / "plan" / topic / "handoff.md")


def default_resume(repo: str, topic: str) -> str:
    """The first prompt pasted into a (re)started session: read the handoff."""
    return f"read {default_handoff(repo, topic)} and follow it"


def default_gitignore_check(repo: str) -> bool:
    """True iff ``<repo>/tmp/overseer/`` is gitignored in ``repo``.

    ``git -C <repo> check-ignore -q tmp/overseer`` exits 0 when the path is
    ignored, 1 when it is not, 128 on error — so only a 0 means "ignored". The
    daemon refuses to start unless every watched repo passes, because the overseer
    writes its markers there and must never dirty a tracked tree. Fail-soft to
    False (treated as "not ignored" → refuse) on any spawn error.
    """
    try:
        completed = subprocess.run(  # noqa: S603 (fixed argv, no shell)
            ["git", "-C", repo, "check-ignore", "-q", "tmp/overseer"],
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    return completed.returncode == 0


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

    ``last_ctx`` is the last KNOWN remaining-% (used by
    :meth:`Supervisor._effective_ctx` when a tick reads ctx as unknown — design:
    keep last known, and unknown never triggers a crossing). ``danger_idle_since``
    tracks when the current CONTINUOUS idle-stall at/below the danger line began,
    driving the NON-NEGOTIABLE force-restart (``_STALL_RESTART_GRACE``); it is reset
    to None the moment the session is not idle-stalled (resumed work / certified /
    recovered context). The injection-round timestamp and the set of
    already-notified escalation bands are DURABLE, in the injection-stamp sidecar
    (``registry.read_injection_stamp`` / ``read_notified_bands`` /
    ``add_notified_band``), so a daemon restart never re-spams a band it already
    sent — they are not in-memory here.
    """

    last_ctx: int | None = None
    danger_idle_since: float | None = None


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
    # Daemon-wide default warn threshold (remaining-% at which the FIRST wrap-up
    # fires) for any track WITHOUT a per-track ``ctx_threshold`` override. Set from
    # ``overseerd --warn-percent`` via ``run_daemon``; a track's own override wins.
    warn_percent: int = registry.DEFAULT_CTX_THRESHOLD
    out: object = None  # writable stream for the table (default: sys.stdout)
    now: Callable[[], float] = time.time
    sleep: Callable[[float], None] = time.sleep
    # Claude session-registry adoption seams (default: real ~/.claude/sessions + /proc;
    # the beside-tests inject a tmp registry dir + fake /proc readers).
    sessions_dir: str | os.PathLike[str] | None = None
    ppid_of: Callable[[int], int | None] = claude_sessions.proc_ppid
    starttime_of: Callable[[int], str | None] = claude_sessions.proc_starttime
    # Background-subshell detection seams (default: real /proc; the beside-tests
    # inject fake process-tree readers). A tracked session sitting at an empty
    # prompt but with a `Bash(run_in_background)` command still running has a
    # DESCENDANT shell under its pane process — that means active background work,
    # so the session is BUSY, not idle (never respawn-pane -k a session with live
    # background work).
    children_of: Callable[[int], list[int]] = claude_sessions.proc_children
    comm_of: Callable[[int], str | None] = claude_sessions.proc_comm
    # Startup gate: `<repo>/tmp/overseer/` MUST be gitignored (the overseer only
    # writes temp files, never tracked ones). Injectable so tests fake the check.
    gitignore_check: Callable[[str], bool] = default_gitignore_check
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

    def adopt_sessions(self) -> list[registry.Track]:
        """Adopt live Claude sessions whose registry name matches an active plan topic.

        Run at `/overseer` startup AND every daemon tick (so a session that is
        renamed, un-blocks a prompt, or is launched later is picked up within one
        interval — not only at bootstrap). It reads Claude Code's own session
        registry (:mod:`claude_sessions`, ``~/.claude/sessions/<pid>.json``) rather
        than scraping the pane: each live session reports its display ``name`` and
        ``cwd`` in a file keyed by the claude PID, which :mod:`claude_sessions`
        joins to the owning tmux session by walking that PID up to a tmux pane PID.
        This is screen-independent, so it works while a session is showing a prompt
        (the exact case the old input-box-border scrape missed), and it reflects a
        runtime ``/rename`` — the maintainer's sessions run
        ``claude --dangerously-skip-permissions`` with NO ``-n`` in argv, so the
        name lives only in that registry.

        A session is adopted ONLY when (a) its registry ``cwd`` resolves inside a
        FLEET repo (the watch-set) AND (b) its ``name`` is an ACTIVE plan topic in
        that repo (a discovered ``plan/<topic>/`` with a ``handoff.md``). Registry
        membership already proves it is a live Claude process, so no worker-command
        guard is needed. The mapping's ``tmux`` field is the bare session name
        holding the work — NOT the repo-qualified ``tmux_id`` the daemon would
        spawn. A ``(repo, topic)`` already mapped is left untouched (no double-add).
        Returns the newly-adopted Tracks.

        Codex sessions are NOT in Claude's registry, so they are not adopted (a
        documented gap; codex would need its own session store read). Distinct from
        :meth:`auto_link`, which links only the repo-qualified ``<repo-slug>--<topic>``
        session the daemon itself launches.
        """
        watch = self._resolve_watch()
        active: dict[str, set[str]] = {}
        for repo, topic, _ in registry.discover_plans(watch):
            active.setdefault(repo, set()).add(topic)
        existing = {(t.repo, t.topic) for t in registry.read_mapping(self.store_path)}
        sessions_dir = (
            self.sessions_dir
            if self.sessions_dir is not None
            else claude_sessions.default_sessions_dir()
        )
        mapped = claude_sessions.map_named_sessions(
            sessions_dir,
            self.tmux.pane_pid_sessions(),
            ppid_of=self.ppid_of,
            starttime_of=self.starttime_of,
        )
        adopted: list[registry.Track] = []
        for session, name, cwd in mapped:
            repo = next((r for r in watch if signals.path_in_repo(cwd, r)), None)
            if repo is None:
                continue
            topic = name
            if topic not in active.get(repo, set()):
                continue
            if (repo, topic) in existing:
                continue
            track = registry.Track(
                topic=topic,
                repo=repo,
                tmux=session,
                handoff=default_handoff(repo, topic),
                resume=default_resume(repo, topic),
            )
            registry.append_mapping(track, self.store_path, added_at=_iso_now())
            existing.add((repo, topic))
            adopted.append(track)
            self._log(f"adopted session {session} → {repo}::{topic}")
        return adopted

    def build_rows(self, *, act: bool = True) -> list[registry.Track]:
        """Discovery ⋈ mapping (the tick's row set).

        When ``act`` (the daemon loop) this runs archive-GC + registry adoption +
        auto-link, all of which MUTATE the store. When NOT ``act`` (the ``list``
        command, advertised read-only) it does NONE — it just joins discovery
        against the current mapping, so `list` cannot silently rewrite / GC /
        adopt / re-link the store out from under a running daemon (adversarial code
        review 2026-07-13, blocker B6).
        """
        watch = self._resolve_watch()
        discovered = registry.discover_plans(watch)
        if not act:
            return registry.join(discovered, registry.read_mapping(self.store_path))
        self.archive_gc()
        # Continuous adoption (not just at bootstrap): pick up any live Claude
        # session whose registry name is now an active topic — so a session that
        # was mid-prompt, renamed, or launched after startup is tracked within one
        # tick rather than being missed forever.
        self.adopt_sessions()
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

    def _pane_settled(self, target: str) -> bool:
        """True if two captures ~``_SETTLE_DELAY`` apart are identical (``target`` = pane id).

        A single capture cannot distinguish active token-streaming from idle —
        the live Claude TUI renders no persistent busy spinner while streaming
        (verified 2026-07-13). Before the daemon INJECTS or RESTARTS an
        apparently-idle track, it confirms the pane is not actively changing. A
        changing pane is treated as busy (`working`) and skipped this tick —
        over-firing busy is the safe direction.
        """
        first = signals.strip_ansi(self.tmux.capture_pane(target))
        self.sleep(_SETTLE_DELAY)
        second = signals.strip_ansi(self.tmux.capture_pane(target))
        return first == second

    def _pane_is_managed_claude(self, target: str, repo: str) -> bool:
        """True iff ``target``'s pane is a live Claude TUI whose cwd is inside ``repo``.

        The identity gate for EVERY act (inject / restart). ``pane_is_claude`` and
        ``path_in_repo`` exist and are tested, but the shipped daemon wired them
        only into auto-link and the restart poll, NOT the act path — so a tracked
        Claude that had exited to a shell (the pane retains the dead TUI's idle-box
        frame) would get the wrap-up pasted INTO THE SHELL, where the
        ``… > .overseer-ready`` marker line executes and FORGES a valid
        certification (adversarial code review 2026-07-13, blocker B3 = Codex #1). Gating
        every act on process identity + cwd closes that, and hardens B1's residual
        (a name that resolved to the wrong session would fail the cwd check).

        ``target`` is the resolved pane id (RB3), so the identity read is of the
        exact pane, never a prefix-matched sibling.
        """
        if not signals.pane_is_claude(self.tmux.pane_current_command(target)):
            return False
        return signals.path_in_repo(self.tmux.pane_current_path(target), repo)

    def _void_ready_marker(self, track: registry.Track) -> None:
        """Delete a track's ready marker, clear its stamp, AND reset its inject state.

        Used both after a successful restart and when a certified track genuinely
        resumes work. ``clear_injection_stamp`` deletes the sidecar key, resetting
        BOTH the round's ``at`` and its notified bands — so after a void (or a
        restart) the round fully resets and every escalation band can fire again in
        the next round. Voiding on the FILESYSTEM (marker + stamp) makes it durable
        across a daemon restart. It ALSO pops the in-memory ``_inject`` state
        (mirroring ``_do_restart``) so the stale ``last_ctx`` does not linger; the
        next threshold crossing opens a clean round that writes a new stamp
        (adversarial code re-review 2026-07-13, blocker RB2).
        """
        try:
            signals.ready_marker_path(track.repo, track.topic).unlink(missing_ok=True)
        except OSError as exc:
            self._log(f"could not delete ready marker for {track.repo}::{track.topic}: {exc}")
        registry.clear_injection_stamp(track.repo, track.topic, self.stamp_path)
        self._inject.pop(_key(track.repo, track.topic), None)

    def _void_if_stale(self, track: registry.Track, ready: bool) -> bool:
        """Void a ready marker on a busy/blocked tick ONLY if it is past the grace.

        Returns the (possibly cleared) ``ready`` flag. A marker younger than
        ``_MARKER_VOID_GRACE`` is the certifying turn's own busy tail and is LEFT
        intact (RB1); an older one means the session resumed work after certifying,
        so it is voided.
        """
        if not ready:
            return ready
        marker = signals.ready_marker_path(track.repo, track.topic)
        try:
            age = self.now() - marker.stat().st_mtime
        except OSError:
            return ready  # unreadable → leave it; ready_marker_valid already gates
        if age > _MARKER_VOID_GRACE:
            self._void_ready_marker(track)
            self._log(
                f"voided stale ready marker for {track.repo}::{track.topic} "
                f"(age {age:.0f}s > {_MARKER_VOID_GRACE:.0f}s grace; session resumed work)"
            )
            return False
        return ready

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

        # Resolve the pane id ONCE and target every subsequent pane op by it (RB3).
        # A pane id is exact and never prefix/fnmatch-matched, so if the tracked
        # session dies mid-tick the ops fail-soft instead of a bare `-t <name>`
        # falling back to a live SIBLING session (e.g. dead `livespec--overseer`
        # resolving to live `livespec--overseer-rewrite`) and, worst case,
        # `respawn-pane -k` killing it. Stable across respawn.
        target = self.tmux.pane_id(session)
        if target is None:
            return RowView(topic=topic, repo=repo, tmux=session, ctx=None, status="session-gone")

        # Identity gate (B3): the mapped session exists, but before reading its pane
        # for any ACT we confirm it is really OUR Claude in OUR repo — never
        # keystroke into a shell / wrong session / human split-pane.
        if not self._pane_is_managed_claude(target, repo):
            return RowView(topic=topic, repo=repo, tmux=session, ctx=None, status="not-claude")

        capture = self.tmux.capture_pane(target)
        # A pane can show an empty prompt yet still be running a
        # `Bash(run_in_background)` command — that command runs as a DESCENDANT
        # shell of the pane's process. A descendant shell ⇒ active background work
        # ⇒ the session is BUSY (suppresses both injection AND restart), even
        # though the pane text looks idle. Runtime-agnostic (walks the process
        # tree, independent of any Claude-specific registry).
        pane_pid = self.tmux.pane_pid(session)
        bg_shell = pane_pid is not None and claude_sessions.has_active_subshell(
            pane_pid, children_of=self.children_of, comm_of=self.comm_of
        )
        busy = signals.is_busy(capture) or bg_shell
        gate = signals.is_structured_gate(capture)
        idle = signals.is_idle_input(capture)
        blocked = signals.blocked_marker(repo, topic)
        current_ctx = signals.parse_ctx_remaining(capture)
        eff_ctx = self._effective_ctx(key, current_ctx)

        stamp = registry.read_injection_stamp(repo, topic, self.stamp_path)
        ready = signals.ready_marker_valid(repo, topic, stamp)

        # A per-track override (an int ``ctx_threshold``) wins; otherwise inherit
        # the daemon-wide default (``warn_percent``, set from ``--warn-percent``).
        threshold = track.ctx_threshold if track.ctx_threshold is not None else self.warn_percent

        # The row note defaults to the blocked-marker text (if any); the busy
        # branch overrides it to "background shell" when a live background shell is
        # the SOLE reason the pane isn't idle, so the operator can see WHY.
        note: str | None = blocked if blocked else None

        # Precedence, top to bottom. Single-capture `busy` and the human gates
        # are checked first. For an apparently-idle track that would ACT
        # (restart / inject), the daemon first confirms the pane is SETTLED
        # (`_pane_settled`) — a single frame can't see active token-streaming, so
        # a changing pane is treated as `working` and skipped this tick.
        if busy:
            status = "working"
            if bg_shell and not signals.is_busy(capture):
                note = "background shell"
            if act:
                # Void the certification ONLY if it is past the grace — a young
                # marker is the certifying turn's own busy tail and must survive
                # (RB1); an old one means the session resumed work after certifying.
                ready = self._void_if_stale(track, ready)
        elif gate or blocked is not None:
            status = "blocked:human"
            if act:
                ready = self._void_if_stale(track, ready)
                detail = blocked if blocked else "structured gate on pane"
                self._surface(f"{repo}::{topic} blocked on human: {detail}")
        elif not idle:
            # Pane present but not a verified idle-input state and not busy —
            # a transient/settling capture. Wait; never act.
            status = "settling"
        elif act and not self._pane_settled(target):
            # One frame looks idle, but the pane is actively changing (streaming).
            status = "working"
        elif act and not self._pane_is_managed_claude(target, repo):
            # TOCTOU re-check (Codex re-review #1): the identity gate ran at the top
            # of the tick, but capturing + the settle delay opened a window in which
            # the pane could have exited to a shell (or cd'd out of the repo). Re-
            # verify identity IMMEDIATELY before any act, so a wrap-up is never
            # pasted into — nor a respawn aimed at — a pane no longer proven ours.
            status = "not-claude"
        elif ready:
            status = "restarting"
            if act:
                self._do_restart(track, target)
        elif eff_ctx is not None and eff_ctx <= threshold:
            if act:
                self._maybe_inject(track, target, eff_ctx, threshold)
            if eff_ctx <= DANGER_CTX_REMAINING and not ready:
                status = self._danger_or_force_restart(
                    track, target, key, eff_ctx, warned=stamp is not None, act=act
                )
            else:
                status = "warned"
        else:
            status = "idle"

        # The idle-stall force-restart clock accrues ONLY across a CONTINUOUS
        # idle-danger stall. Any OTHER resolved state (working, blocked, warned
        # above danger, idle) means the session is not stalled, so reset it — a
        # brief idle dip must never count toward the non-negotiable force-restart.
        # ``restarting`` is excluded so a FAILED force-restart retries promptly
        # instead of resetting its own grace (a SUCCESSFUL restart already popped
        # the state), and ``danger`` is excluded because that IS the accruing stall.
        if act and status not in ("danger", "restarting"):
            st = self._inject.get(key)
            if st is not None:
                st.danger_idle_since = None

        return RowView(
            topic=topic,
            repo=repo,
            tmux=session,
            ctx=eff_ctx,
            status=status,
            note=note,
        )

    def _danger_or_force_restart(
        self,
        track: registry.Track,
        target: str,
        key: tuple[str, str],
        eff_ctx: int,
        *,
        warned: bool,
        act: bool,
    ) -> str:
        """A warned track STALLED idle at/below the danger line with no ready marker.

        The auto-restart is NON-NEGOTIABLE (maintainer 2026-07-14): the daemon's
        whole job is to keep the track moving, so a session that never certifies —
        because it refused, crashed, ran out of context, or autocompacted — is
        FORCE-restarted rather than surfaced-and-left-forever (the old "danger →
        surface only, never force-kill" behavior, which wedged a real track
        indefinitely — the exact bug this fixes). Reached ONLY from the idle branch
        of :meth:`evaluate`, so the pane is already verified idle + settled +
        managed-Claude + no valid marker — i.e. at a stopping point, NOT mid-work;
        ``respawn-pane -k`` replaces the process while every file / worktree / commit
        on disk survives, and the resume line points the fresh session back at
        ``plan/<topic>/handoff.md``.

        The force-restart fires once the track has been continuously idle-stalled
        for ``_STALL_RESTART_GRACE`` (measured from ``danger_idle_since``, first set
        the tick the stall is observed and reset by :meth:`evaluate` whenever the
        session is not idle-stalled). The grace lets a late ``.overseer-ready`` still
        win the clean marker path first and gives the human a beat to intervene.
        ``warned`` (an injection stamp exists) guards that a wrap-up was actually
        delivered before we force a restart — if the pane is so broken the wrap-up
        never landed, we keep surfacing rather than respawn into a broken tmux.
        Returns the row status: ``restarting`` when the force-restart fires, else
        ``danger``.
        """
        repo, topic = track.repo, track.topic
        if not act:
            return "danger"
        state = self._inject.setdefault(key, _InjectState())
        if state.danger_idle_since is None:
            state.danger_idle_since = self.now()
        stalled = self.now() - state.danger_idle_since
        if warned and stalled >= _STALL_RESTART_GRACE:
            self._surface(
                f"{repo}::{topic} stalled idle at ctx {eff_ctx}% with no ready marker "
                f"for {stalled:.0f}s — force-restarting (auto-restart is non-negotiable)"
            )
            self._do_restart(track, target, certified=False)
            return "restarting"
        detail = (
            f"force-restart in {_STALL_RESTART_GRACE - stalled:.0f}s"
            if warned
            else "awaiting wrap-up delivery"
        )
        self._surface(
            f"{repo}::{topic} won't wrap up (ctx {eff_ctx}% left, no ready marker); {detail}"
        )
        return "danger"

    def _maybe_inject(
        self, track: registry.Track, target: str, eff_ctx: int, threshold: int
    ) -> None:
        """Escalating, spam-proof wrap-up injection: warn once per crossed band.

        The bands are the effective ``threshold`` plus each lower 10%-band below it
        (40 / 30 / 20 / 10). A band fires at most ONCE per round: the set of
        already-notified bands is DURABLE (the injection-stamp sidecar), so a
        daemon restart never re-spams a band it already sent. Multiple bands crossed
        in one tick coalesce into a SINGLE message but mark ALL of them notified.

        ``target`` is the resolved pane id (RB3). The round's ``at`` stamp is
        written ONLY when OPENING the round (the first band of the round) — a
        re-warn at a lower band does NOT rewrite it, so a ready marker the session
        writes still has ``mtime > at`` and certifies, and re-warns never reset the
        notified bands. On a paste failure that OPENED the round, the just-opened
        round is rolled back (stamp cleared) so the next tick retries cleanly (B5).
        """
        repo, topic = track.repo, track.topic
        bands = sorted({threshold} | {b for b in (40, 30, 20, 10) if b < threshold}, reverse=True)
        notified = set(registry.read_notified_bands(repo, topic, self.stamp_path))
        due = [b for b in bands if eff_ctx <= b and b not in notified]
        if not due:
            return
        opened_now = registry.read_injection_stamp(repo, topic, self.stamp_path) is None
        if opened_now:
            # Stamp BEFORE the paste (design) so a marker the session writes has
            # mtime > at. Only on opening — a re-warn preserves the round's at.
            registry.write_injection_stamp(repo, topic, self.now(), self.stamp_path)
        message = wrapup_message(remaining=eff_ctx, repo=repo, topic=topic)
        if self._submit_prompt(target, message):
            for b in due:
                registry.add_notified_band(repo, topic, b, self.stamp_path)
            self._log(f"injected wrap-up into {repo}::{topic} (ctx {eff_ctx}%, bands {due})")
        else:
            if opened_now:
                # Roll back the just-opened round so the next tick retries cleanly.
                registry.clear_injection_stamp(repo, topic, self.stamp_path)
            self._surface(f"{repo}::{topic} wrap-up injection failed; will retry")

    def _do_restart(self, track: registry.Track, target: str, *, certified: bool = True) -> None:
        """Atomic restart interlock: respawn → wait Claude → resume → close the round.

        ``target`` is the resolved pane id (RB3), STABLE across the respawn.

        Shared by BOTH restart callers: the marker path (``certified=True`` — the
        session wrote a valid ``.overseer-ready``) and the idle-stall FORCE path
        (``certified=False`` — a warned track that never certified, per
        :meth:`_danger_or_force_restart`). The respawn + resume mechanics are
        identical; ``certified`` only changes the failure-surface wording (there is
        no marker to "keep" on the force path). ``_void_ready_marker``'s unlink is
        ``missing_ok``, so the force path (no marker on disk) still clears the round
        — stamp + notified bands + in-memory state — cleanly.

        Every tmux step is a HARD GATE (B5). If ``respawn-pane`` fails, or the
        pane never becomes a live Claude, the daemon SURFACES the failure and
        RETURNS WITHOUT closing the round — so a valid certification is preserved and
        the restart is retried, never silently destroyed. The round is closed (and
        the injection stamp cleared — B4) only once the respawn is confirmed; the
        resume-submit result is surfaced but does not block closing, because the
        fresh Claude IS up (a stale marker would else re-restart and kill it, and
        B3's identity gate already blocks re-acting on a non-Claude pane).
        ``_void_ready_marker`` also pops the in-memory inject state (RB2), so the
        redundant explicit pop below is belt-and-suspenders.
        """
        keep = "keeping ready marker" if certified else "will retry next tick"
        if not self.tmux.respawn_pane(target, track.repo, self._launch_command(track)):
            self._surface(f"{track.repo}::{track.topic} restart respawn FAILED; {keep}")
            return
        if not self._await_claude(target):
            self._surface(f"{track.repo}::{track.topic} respawned pane never became Claude; {keep}")
            return
        resume = track.resume or default_resume(track.repo, track.topic)
        if not self._submit_prompt(target, resume):
            self._surface(f"{track.repo}::{track.topic} resume line not submitted after restart")
        self._void_ready_marker(track)
        self._inject.pop(_key(track.repo, track.topic), None)
        self._log(f"restarted {track.repo}::{track.topic} (pane {target})")

    @staticmethod
    def _launch_command(track: registry.Track) -> str:
        """The (re)start command: ``claude --dangerously-skip-permissions -n <topic>``.

        ``--dangerously-skip-permissions`` is REQUIRED (maintainer 2026-07-14): a
        (re)started track must resume AUTONOMOUSLY. Without it the fresh session
        stalls on the first permission prompt and the whole point of the
        auto-restart — an unattended, hands-off resume — is lost. ``-n <topic>``
        (topic shell-quoted, defensive) sets the session's display name; the resume
        line (read the handoff) is pasted AFTER launch, since a ``claude "<prompt>"``
        argv only pre-fills without submitting.
        """
        return f"claude --dangerously-skip-permissions -n {shlex.quote(track.topic)}"

    def _await_claude(self, target: str) -> bool:
        """Poll ``#{pane_current_command}`` until it is a live Claude TUI, bounded.

        ``target`` is the resolved pane id. Never scrape the ``❯`` prompt glyph
        (ambiguous shell/Claude); wait on the process identity (design). Returns
        False if it never became Claude.
        """
        for _ in range(_RESTART_POLL_MAX):
            if signals.pane_is_claude(self.tmux.pane_current_command(target)):
                return True
            self.sleep(_RESTART_POLL_INTERVAL)
        return False

    def _submit_prompt(self, target: str, text: str) -> bool:
        """Bracketed-paste a payload, then submit it — re-sending Enter until the
        input box clears. Returns True iff the paste LANDED and the box CLEARED.
        ``target`` is the resolved pane id (RB3).

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
        if not self.tmux.bracketed_paste(target, text):
            self._log(f"bracketed paste FAILED for pane {target}")
            return False
        self.sleep(_RESTART_POLL_INTERVAL)
        for _ in range(_SUBMIT_MAX_ENTERS):
            self.tmux.send_keys(target, "Enter")
            self.sleep(_SUBMIT_POLL)
            if signals.input_box_ready(self.tmux.capture_pane(target)):
                return True
        return False

    # ----------------------------------------------------------------- #
    # Reboot recovery (startup-only, never per-tick).
    # ----------------------------------------------------------------- #

    def recover_missing_sessions(self) -> list[str]:
        """Recreate any mapped session that is not currently live (design).

        Run ONCE at daemon startup: a fresh overseer reads the mapping, and for
        each row whose ``<repo-slug>--<topic>`` session is gone, creates the
        session, launches ``claude --dangerously-skip-permissions -n <topic>`` in
        the repo (:meth:`_launch_command`), and pastes the resume line. Not a
        per-tick action (a session the user deliberately
        kills should not be revived every 10s). Returns the recovered names.
        """
        recovered: list[str] = []
        for track in registry.read_mapping(self.store_path):
            session = self._session_of(track)
            if self.tmux.session_exists(session):
                continue
            self.tmux.new_session(session, track.repo)
            # Require the EXACT session to now exist before launching (Codex
            # re-review #3): if `new-session` failed, `_do_launch`'s pane-id
            # resolution + `respawn-pane` would target the bare name, which could
            # prefix-match a live sibling and replace IT. Fail-soft: surface + skip.
            if not self.tmux.session_exists(session):
                self._surface(
                    f"reboot-recovery: new-session did not create {session} "
                    f"for {track.repo}::{track.topic}; skipping"
                )
                continue
            if self._do_launch(track, session):
                recovered.append(session)
                self._log(f"reboot-recovery recreated {session} for {track.repo}::{track.topic}")
            else:
                self._surface(
                    f"reboot-recovery FAILED to launch {session} for {track.repo}::{track.topic}"
                )
        return recovered

    def _do_launch(self, track: registry.Track, session: str) -> bool:
        """Launch ``claude --dangerously-skip-permissions -n <topic>`` and paste the resume line.

        ``session`` is the (just-created or existing) session NAME; the pane id is
        resolved from it and every pane op targets that id (RB3). Returns True iff
        respawn succeeded, the pane became a live Claude, and the resume line
        submitted — so callers (`recover`, `start`) can surface a failure rather
        than silently claim a launch happened (B5).
        """
        target = self.tmux.pane_id(session)
        if target is None:
            return False
        if not self.tmux.respawn_pane(target, track.repo, self._launch_command(track)):
            return False
        if not self._await_claude(target):
            return False
        resume = track.resume or default_resume(track.repo, track.topic)
        return self._submit_prompt(target, resume)

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

    def unignored_tmp_repos(self) -> list[str]:
        """Watched repos whose ``tmp/overseer/`` is NOT gitignored (present roots only).

        The overseer writes its markers under each track's ``<repo>/tmp/overseer/``;
        if that path is not gitignored, a marker would dirty the tracked tree — the
        exact thing the overseer must never do. A transiently-absent repo root is
        skipped (not a violation), mirroring the GC's ``repo_root_present`` guard.
        """
        return [
            repo
            for repo in self._resolve_watch()
            if registry.repo_root_present(repo) and not self.gitignore_check(repo)
        ]

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
        offenders = self.unignored_tmp_repos()
        if offenders:
            self._surface(
                "refusing to start: tmp/overseer/ is NOT gitignored in "
                + ", ".join(offenders)
                + " — add `tmp/` to each repo's .gitignore (the overseer writes markers "
                "there and must never dirty a tracked tree)"
            )
            return
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


def _build_supervisor() -> Supervisor:
    """Build the daemon's ``Supervisor`` for the CLI — with NO tunable surface.

    The invocation surface carries no watch-set / store / stamp knobs (they were
    de-gold-plated 2026-07-13): the watch-set is the whole fleet, read from the
    core repo's ``.livespec-fleet-manifest.jsonc``, and the mapping store + the
    injection-stamp sidecar are the hard-coded ``registry`` defaults
    (``~/.livespec-overseer.jsonl`` / ``~/.livespec-overseer-stamps.json``). The
    ``Supervisor`` dataclass keeps ``store_path`` / ``stamp_path`` / ``watch_repos``
    injectable, but ONLY the beside-tests inject them — never the CLI.
    """
    return Supervisor(manifest_path=_default_manifest())


def _upsert(track: registry.Track) -> None:
    """Replace any existing (repo, topic) mapping row in the hard-coded store, then
    append (one row each)."""
    registry.remove_mapping(track.repo, track.topic, None)
    registry.append_mapping(track, None, added_at=_iso_now())


def run_daemon(warn_percent: int | None = None) -> int:
    """Start the fleet daemon with fixed defaults — the ``overseerd`` entrypoint.

    Called by the dedicated ``overseerd`` executable: watch every fleet member
    (discovered from the manifest, resolved relative to THIS file so it works from
    any cwd), with the hard-coded store + stamp paths and the default loop
    interval. ``warn_percent`` (from ``overseerd --warn-percent N``) is the
    daemon-wide default remaining-% at which the first wrap-up fires; None means
    the built-in ``registry.DEFAULT_CTX_THRESHOLD``. A per-track ``ctx_threshold``
    override still wins over it. ``recover=False`` keeps the daemon a pure
    surface-only watcher — it never auto-spawns/revives a session at startup;
    (re)launching a mapped-but-dead session is a deliberate ``start`` via the
    skill. This function does not return (the loop runs until the process is
    killed); the ``int`` is a formality so ``overseerd`` can ``raise SystemExit``.
    """
    supervisor = _build_supervisor()
    # Set the field after building (rather than threading it through
    # `_build_supervisor`) so the daemon keeps its single no-arg builder.
    supervisor.warn_percent = (
        warn_percent if warn_percent is not None else registry.DEFAULT_CTX_THRESHOLD
    )
    supervisor.run(interval=LOOP_INTERVAL_SECONDS, once=False, recover=False)
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    sup = _build_supervisor()
    sup.tick(act=False)  # read-only render: no injection/restart
    return 0


def _cmd_adopt(args: argparse.Namespace) -> int:
    adopted = _build_supervisor().adopt_sessions()
    for track in adopted:
        print(f"adopted {track.tmux} → {track.repo}::{track.topic}")
    print(f"adopted {len(adopted)} existing session(s)")
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
    _upsert(track)
    print(f"added mapping {repo}::{args.topic} (tmux {track.tmux})")
    return 0


def _cmd_remove(args: argparse.Namespace) -> int:
    removed = registry.remove_mapping(os.path.normpath(args.repo), args.topic, None)
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
    sup = Supervisor(tmux=io)
    track = registry.Track(
        topic=topic,
        repo=repo,
        tmux=session,
        handoff=default_handoff(repo, topic),
        resume=default_resume(repo, topic),
    )
    if io.session_exists(session) and not force:
        # Fail CLOSED (RB4): refuse to respawn-kill an existing session unless we
        # POSITIVELY know it is not a live Claude. An unreadable
        # `pane_current_command` (None) might be a live Claude mid-work, so treat
        # unknown like Claude — a genuinely dead shell reports its shell name
        # positively, so failing closed on None costs nothing.
        cmd = io.pane_current_command(session)
        if cmd is None or signals.pane_is_claude(cmd):
            _upsert(track)
            print(
                f"{repo}::{topic}: session {session} already running (or its identity is "
                f"unreadable) — mapping upserted, NOT respawned. Pass --force to respawn "
                f"(kills the running session)."
            )
            return 0
    if not io.session_exists(session):
        io.new_session(session, repo)
        # Require the EXACT session to exist before launching (Codex re-review #3):
        # a failed `new-session` must not let `_do_launch` respawn a prefix-matched
        # sibling.
        if not io.session_exists(session):
            print(
                f"start FAILED: could not create tmux session {session} for {repo}::{topic}",
                file=sys.stderr,
            )
            return 1
    if not sup._do_launch(track, session):
        print(f"start FAILED to launch {repo}::{topic} in tmux session {session}", file=sys.stderr)
        return 1
    _upsert(track)
    print(f"started {repo}::{topic} in tmux session {session}")
    return 0


def _add_track_args(parser: argparse.ArgumentParser) -> None:
    """The shared ``--repo`` / ``--topic`` keyword flags for the track subcommands.

    Keyword (not positional) so the ``/overseer`` skill is the operator surface:
    it prompts for whichever is omitted and passes both. Required here so a stray
    bare invocation fails loudly rather than acting on a half-specified track.
    """
    parser.add_argument("--repo", required=True, help="repo checkout path the plan lives in")
    parser.add_argument("--topic", required=True, help="plan topic (the plan/<topic>/ dir name)")


def main(argv: list[str] | None = None) -> int:
    """The track-management CLI (`list` / `add` / `remove` / `unassign` / `start`).

    This is the MODULE's one-shot surface, invoked from the `/overseer` skill's
    bottom pane. It deliberately carries NO `daemon` subcommand: the daemon is the
    dedicated `overseerd` executable (which calls `run_daemon`), not a subcommand
    here — a daemon that IS the executable has no business being a subcommand of a
    track-management CLI. No watch-set / store / stamp knobs either; those are
    fixed (see `_build_supervisor`).
    """
    parser = argparse.ArgumentParser(
        prog="overseer", description="livespec overseer track-management CLI"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="print the current joined table once (read-only)")
    p_list.set_defaults(func=_cmd_list)

    p_adopt = sub.add_parser(
        "adopt", help="adopt existing worker sessions matching active plan topics"
    )
    p_adopt.set_defaults(func=_cmd_adopt)

    p_add = sub.add_parser("add", help="add a (repo, topic) mapping row")
    _add_track_args(p_add)
    p_add.set_defaults(func=_cmd_add)

    p_remove = sub.add_parser("remove", help="remove a (repo, topic) mapping row")
    _add_track_args(p_remove)
    p_remove.set_defaults(func=_cmd_remove)

    # unassign is a synonym for remove: drop the mapping so the plan reverts to
    # `unassigned` (never force-kills the session — surface-only).
    p_unassign = sub.add_parser("unassign", help="detach a plan's mapping (revert to unassigned)")
    _add_track_args(p_unassign)
    p_unassign.set_defaults(func=_cmd_remove)

    p_start = sub.add_parser("start", help="surface-only: launch a session for a plan and map it")
    _add_track_args(p_start)
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
