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
import os
import sys
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

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
            if registry.archived_or_gone(repo, topic):
                self._log(f"archive-GC dropping mapping row {repo}::{topic}")
                return False
            return True

        return registry.rewrite_mapping(keep, self.store_path)

    def auto_link(self, track: registry.Track) -> registry.Track | None:
        """Link a live session to an unassigned discovered plan — safely.

        A link is created ONLY when a session named ``<repo-slug>:<topic>``
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

    def build_rows(self) -> list[registry.Track]:
        """Discovery ⋈ mapping after archive-GC + auto-link (the tick's row set)."""
        watch = self._resolve_watch()
        discovered = registry.discover_plans(watch)
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
        elif gate or blocked is not None:
            status = "blocked:human"
            if act:
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
            registry.write_injection_stamp(track.repo, track.topic, self.now(), self.stamp_path)
            self._submit_prompt(session, message)
            state.count = 1
            state.ctx_at_last = eff_ctx
            self._log(f"injected wrap-up into {track.repo}::{track.topic} (ctx {eff_ctx}%)")
        elif state.count == 1 and state.ctx_at_last is not None and eff_ctx < state.ctx_at_last:
            self._submit_prompt(session, message)  # stamp preserved from the first inject
            state.count = 2
            state.ctx_at_last = eff_ctx
            self._log(f"re-sent wrap-up into {track.repo}::{track.topic} (ctx {eff_ctx}%)")

    def _do_restart(self, track: registry.Track, session: str) -> None:
        """Atomic restart interlock: respawn → wait Claude → resume → delete marker."""
        self.tmux.respawn_pane(session, track.repo, f"claude -n {track.topic}")
        for _ in range(_RESTART_POLL_MAX):
            if signals.pane_is_claude(self.tmux.pane_current_command(session)):
                break
            self.sleep(_RESTART_POLL_INTERVAL)
        resume = track.resume or default_resume(track.repo, track.topic)
        self._submit_prompt(session, resume)
        try:
            signals.ready_marker_path(track.repo, track.topic).unlink(missing_ok=True)
        except OSError as exc:
            self._log(f"could not delete ready marker for {track.repo}::{track.topic}: {exc}")
        self._inject.pop(_key(track.repo, track.topic), None)
        self._log(f"restarted {track.repo}::{track.topic} (session {session})")

    def _submit_prompt(self, session: str, text: str) -> None:
        """Bracketed-paste a payload then submit it with a single Enter keystroke.

        The paste is atomic (never fragments — blocker #2); the lone Enter is a
        submit, not payload typing. A brief pause lets the TUI ingest the paste
        before the Enter arrives.
        """
        self.tmux.bracketed_paste(session, text)
        self.sleep(_RESTART_POLL_INTERVAL)
        self.tmux.send_keys(session, "Enter")

    # ----------------------------------------------------------------- #
    # Reboot recovery (startup-only, never per-tick).
    # ----------------------------------------------------------------- #

    def recover_missing_sessions(self) -> list[str]:
        """Recreate any mapped session that is not currently live (design).

        Run ONCE at daemon startup: a fresh overseer reads the mapping, and for
        each row whose ``<repo-slug>:<topic>`` session is gone, creates the
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
            self._do_launch(track, session)
            recovered.append(session)
            self._log(f"reboot-recovery recreated {session} for {track.repo}::{track.topic}")
        return recovered

    def _do_launch(self, track: registry.Track, session: str) -> None:
        """Launch ``claude -n <topic>`` into ``session`` and paste the resume line."""
        self.tmux.respawn_pane(session, track.repo, f"claude -n {track.topic}")
        for _ in range(_RESTART_POLL_MAX):
            if signals.pane_is_claude(self.tmux.pane_current_command(session)):
                break
            self.sleep(_RESTART_POLL_INTERVAL)
        resume = track.resume or default_resume(track.repo, track.topic)
        self._submit_prompt(session, resume)

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
        views = [self.evaluate(track, act=act) for track in self.build_rows()]
        self.render(views)
        return views

    def run(
        self, *, interval: float = LOOP_INTERVAL_SECONDS, once: bool = False, recover: bool = False
    ) -> None:
        """Run the poll loop. ``once`` runs a single tick (live-exercise/testing)."""
        if recover:
            self.recover_missing_sessions()
        while True:
            try:
                self.tick(act=True)
            except KeyboardInterrupt:
                self._log("interrupted; exiting")
                return
            if once:
                return
            self.sleep(interval)


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
    """Surface-only, user-initiated launch. The daemon never invokes this."""
    repo = os.path.normpath(args.repo)
    topic = args.topic
    session = registry.tmux_id(repo, topic)
    io = tmuxio.TmuxIO()
    sup = Supervisor(tmux=io, store_path=getattr(args, "store", None), stamp_path=None)
    if not io.session_exists(session):
        io.new_session(session, repo)
    track = registry.Track(
        topic=topic,
        repo=repo,
        tmux=session,
        handoff=default_handoff(repo, topic),
        resume=default_resume(repo, topic),
    )
    sup._do_launch(track, session)
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
    p_start.set_defaults(func=_cmd_start)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
