"""supervisor.py — the overseer daemon: poll loop, state machine, table, CLI.

Stdlib-only, host-only (see ``registry.py`` header — the whole skill folder is
outside the livespec product gates). This module *acts and renders*; it holds
NO semantic judgment. Every "am I done / blocked?" decision is made by the
tracked session's own LLM and DECLARED out-of-band on the filesystem (the ONE
``.overseer-state`` file); this daemon only pattern-matches deterministic tmux
signals and that declaration — it never infers readiness for itself.

It builds on the already-merged pure-logic core:
  - ``registry.py`` — discovery ⋈ mapping, the JSONL store, injection stamps.
  - ``signals.py``  — pane parsing (busy / gate / idle / ctx%) + the ONE indicator
    file (``read_state`` / ``ready_valid``).
  - ``tmuxio.py``   — the single tmux subprocess boundary (injectable, faked in
    tests).

THE CARDINAL RULE (maintainer 2026-07-14): **the daemon NEVER restarts a session
that has not declared itself ready.** A tracked session declares its own state by
writing ONE line to ONE file (``<repo>/tmp/overseer/<topic>/.overseer-state``):

    ready                       at a clean stopping point — restart me
    blocked: <one-line reason>  needs a human decision the session cannot make
    winding-down                acknowledged the wrap-up; wrapping up now

``ready`` is the SOLE authorization for a restart. The daemon never infers it from a
timer, from idleness, or from anything else: "idle + settled" is NOT "safe to kill" —
a session can be idle while a background build runs, while a sub-agent works, or while
it waits on a human in another pane. Only the session knows, so only the session may
say so. A session that declares NOTHING is reported to the human as not responding and
is left alone — that is a bug in the session, never a licence for the daemon to guess.

One file with a VALUE, not two presence-markers: two files could both exist, and their
precedence was incidental rather than designed.

Per-tick state machine (precedence, top to bottom — working / blocked:human are
detected FIRST so injection is suppressed there):

    working        is_busy (incl. a live background shell)  → leave alone
    blocked:human  is_structured_gate OR state == blocked   → surface; suppress inject
    restarting     state == ready (fresh) AND idle-input    → respawn + resume + clear state
    winding-down   fresh ACK                                → wait; suppress re-warn
    warned/danger  ctx ≤ threshold AND idle-input           → escalating wrap-up; danger SURFACES
    idle           ctx > threshold                          → leave alone
    settling       pane present but not verified idle       → wait

``restarting`` is checked BEFORE ``warned``: a fresh ``ready`` means the session
already declared it is done, so it supersedes any re-warn. The wrap-up ESCALATES by
10% band (50/40 suggest → 30/20/10 insist), and a fresh ``winding-down`` suppresses it
so the daemon never keystrokes into a session that is already wrapping up.
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import fcntl
import os
import shlex
import shutil
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
import codex_sessions
import registry
import signals
import streams
import tmuxio

__all__ = [
    "DANGER_CTX_REMAINING",
    "LOOP_INTERVAL_SECONDS",
    "RowView",
    "Supervisor",
    "default_resume",
    "idle_nudge_message",
    "main",
    "wrapup_message",
]

# ~10s fast loop (design). Configurable via the daemon CLI ``--interval``.
LOOP_INTERVAL_SECONDS = 10

# The "danger" line, expressed in REMAINING-context percent: ~20% left ≈ 80% used.
# At/below this with no `ready` declaration, the daemon SURFACES the track to the
# human — loudly, with its tmux coordinates — and does NOTHING ELSE. It NEVER kills
# a session that has not declared itself ready (maintainer 2026-07-14: "NEVER
# forcibly restart a session that is not ready; it MUST drop the indicator file for
# action"). A timer cannot know whether a session is safe to kill: "idle + settled"
# is not "at a safe stopping point" — a session can be idle while a background build
# runs, while a sub-agent works, or while it waits on a human in another pane. Only
# the session knows, so only the session may authorize the restart.
DANGER_CTX_REMAINING = 20

# The statuses that mean "a human must go look at this track". They are the membership
# test for the `NEEDS YOU` block the daemon renders under its table, and for the tmux
# window-name badge — the two surfaces that answer "what needs attention?".
#
# `unassigned` is deliberately NOT here: a discovered plan with no session is startable,
# not stuck, and there are dozens of them — including them would bury the handful of rows
# that genuinely want the operator, which is the exact failure this block exists to fix.
# `session-gone` IS attention: a plan we have seen running is no longer in any tmux,
# and the operator decides whether to restart or unassign it. `not-claude` is gone.
ATTENTION_STATUSES = ("blocked:human", "danger", "session-gone")

# The row note a track carries while its POST-RESPAWN resume line has not yet SUBMITTED
# (R1, 2026-07-18). The daemon self-heals — it re-sends Enter every tick (never a
# re-respawn) until the box clears — but until it lands the operator should SEE the track
# is mid-restart and stranded, and a human may need to press Enter if the retry cannot
# clear it. Matched by `needs_attention` so the row stays in `NEEDS YOU` (and the alert
# stays edge-triggered, not re-armed) until the resume actually submits.
_RESUME_PENDING_NOTE = "resume not submitted — daemon retrying Enter"

# Claude's registry `status` values (`~/.claude/sessions/<pid>.json`) that mean the session
# is doing work — the AUTHORITATIVE busy signal for an adopted Claude session. `busy` =
# actively generating / running an in-process sub-agent; `shell` = at the prompt with a live
# `Bash(run_in_background)` command (Claude's own background-work signal). `idle` / `waiting`
# are NOT here (at a prompt, nothing running / waiting for the human).
_CLAUDE_BUSY_STATUSES = frozenset({"busy", "shell"})

# The tmux window name the daemon owns; it badges an attention count onto it
# (`overseer` → `overseer(2!)`).
WINDOW_NAME = "overseer"

# Live-table row color (TTY-only; see `Supervisor.render`). The operator scans the
# table by hue: each row is tinted by its STATUS so the handful that want a human
# stand out from the background of `unassigned` plans. Color is a whole-LINE
# affordance — the ANSI codes wrap the already-padded row, never a cell, so column
# alignment (widths computed on plain-text `len`) is preserved. Emitted ONLY to a
# TTY (`render` gates on `out.isatty()`), so piped `list` output and the
# beside-tests' `StringIO` stay plain text.
#
#   green  = actively working (working / winding-down / restarting / settling)
#   yellow = idle, waiting on a human (`blocked:human`), or low on context
#            (`warned` / `danger`)
#   red    = broken: the session is gone (`session-gone` — the only red status;
#            `not-claude` was deleted)
#   default (uncolored — terminal white/gray) = `unassigned`, and any unmapped status
_ANSI_RESET = "\x1b[0m"
_ANSI_GREEN = "\x1b[32m"
_ANSI_YELLOW = "\x1b[33m"
_ANSI_RED = "\x1b[31m"
_STATUS_COLOR = {
    "working": _ANSI_GREEN,
    "winding-down": _ANSI_GREEN,
    "restarting": _ANSI_GREEN,
    "settling": _ANSI_GREEN,
    "idle": _ANSI_YELLOW,
    "idle-with-context-left": _ANSI_YELLOW,
    "warned": _ANSI_YELLOW,
    "danger": _ANSI_YELLOW,
    "blocked:human": _ANSI_YELLOW,
    "session-gone": _ANSI_RED,
}


def _row_color(status: str) -> str:
    """The ANSI SGR prefix a row with STATUS is tinted with, or ``""`` for the
    terminal default (``unassigned`` and any unmapped status)."""
    return _STATUS_COLOR.get(status, "")


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

# Grace window before a stale `ready` declaration is voided on a busy observation. The
# wrap-up protocol makes the session write `ready` as the LAST tool
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

# How long a `winding-down` acknowledgement may sit before the daemon SURFACES it as
# "acknowledged but not finishing". The ACK buys patience — while it is fresh the
# daemon stops re-warning, so it never keystrokes into a session that is actively
# wrapping up. But an ACK must not become an infinite stall: past this window the
# daemon resumes escalating and reports the track. It STILL never acts on it — the
# escalation is louder words, never a kill.
_ACK_STALE_AFTER = 900.0

# Minimum CONTINUOUS idle duration before the keep-going ("idle-with-context-left") nudge
# may fire. The nudge pastes + submits text into the session, so firing it on a session that
# is only BRIEFLY at the prompt (between turns, or the human is mid-thought) INTERRUPTS
# active work — the maintainer-reported failure (2026-07-18: "too aggressive, TOO SOON …
# interrupting active sessions"). A session must sit cleanly idle (empty prompt, not busy,
# above its wind-down threshold) for at least this long before it is nudged. In-memory
# (`_InjectState.idle_since`), so a daemon restart resets the clock — which only DELAYS a
# nudge, the safe direction.
_IDLE_NUDGE_AFTER = 3600.0  # 1 hour


# --------------------------------------------------------------------------- #
# The wrap-up message + resume line. Single-sourced here so Build C's
# convention doc and tracked-session handoffs reference the SAME text.
# --------------------------------------------------------------------------- #

# At/below this remaining-%, the wrap-up STOPS suggesting and DEMANDS shutdown. The
# escalation the maintainer asked for (2026-07-14): a gentle nudge at the first bands
# (50/40), then insistent at 30/20/10. Re-sending identical text five times is
# repetition, not escalation — and with the force-restart gone, this escalation IS the
# lever, so it has to actually get sharper.
_INSIST_AT = 30

_WRAPUP_SUGGEST_HEAD = """\
You are down to {n}% of your context. Please start wrapping up for a clean session
restart — do it now, while you still have room to do it properly."""

_WRAPUP_INSIST_HEAD = """\
STOP AND WIND DOWN NOW. You have only {n}% of your context left. Finish what is in
flight, do not start anything new, and shut down — you are close to the point where
you can no longer hand off cleanly."""

_WRAPUP_BODY = """\
You WILL be restarted — but ONLY when YOU say so. The overseer never kills a session
that has not declared itself ready. When you stop, this pane is respawned into a fresh
session handed exactly ONE prompt:
    read {handoff} and follow it
So {handoff} is the ONLY thing the next session inherits. Do NOT leave your resume state
anywhere else (a scratchpad file, this transcript) — it will be LOST. If your real
pending work has drifted from what that file says, REWRITE that file.

Declare your state by writing ONE line to the single state file
{state_file} — one of exactly these three values:

    winding-down                  I got this message and am wrapping up now.
    ready                         I am at a clean stopping point — restart me.
    blocked: <one-line reason>    I need a human decision I cannot make myself.

ACKNOWLEDGE FIRST, right now, before anything else:
    mkdir -p {marker_dir} && echo winding-down > {state_file}

Then:
 1. Bring your OWN work to a clean, resumable stopping point, and UPDATE {handoff} to
    match. Your session owns its handoff and everything under plan/; the overseer never
    reads or writes those.
 2. COMMIT {handoff}. Writing it to disk is NOT saving it — an uncommitted handoff has
    no history, no attribution, and is one `git checkout` from gone. You cannot commit
    at the primary checkout (the commit-refuse hook rejects it), and a fresh worktree
    will NOT contain your edits, so copy them across:
        W="$HOME/.worktrees/{slug}/wrapup-{topic}"
        mise exec -- git -C {repo} worktree add -b wrapup-{topic} "$W" master
        cp {handoff} "$W/plan/{topic}/handoff.md"
        cd "$W" && mise exec -- git add plan/ && mise exec -- git commit
        mise exec -- git push && gh pr create --fill && gh pr merge --auto --rebase --delete-branch
    Doc-only commits take the fast seven-target gate at both commit and push, so this is
    quick. Never pass --no-verify. If a hook rejects you, fix the cause or declare
    `blocked: <reason>` — do not bypass it and do not discard the file.
 3. Stop every background sub-agent and subprocess you started.
 4. Declare done, and stop:
        echo ready > {state_file}

`ready` is the ONLY thing that restarts you. If you write nothing at all, you are NOT
restarted and NOT killed — you are reported to the human as not responding, and your
track sits there until a person intervenes. Do not do that to them: write the file."""


def wrapup_message(*, remaining: int, repo: str, topic: str) -> str:
    """The wrap-up text injected when a track crosses a ctx warn band.

    ESCALATES with the band (maintainer 2026-07-14): a suggestion while there is still
    room (above ``_INSIST_AT``), then an insistent shut-down demand at 30/20/10.
    ``remaining`` fills ``{n}`` with the CURRENT remaining-context percent, so each
    re-warn reflects the live value.

    ``repo``/``topic`` build the TEMP dir (``<repo>/tmp/overseer/<topic>/``) holding the
    single ``.overseer-state`` file the session writes — never anything under ``plan/`` —
    and the ``plan/<topic>/handoff.md`` path the restart resumes FROM. Constructing that
    path is pure string work (``default_handoff``): the overseer POINTS at the handoff,
    exactly as the resume line does, and never opens it.

    Two failures shaped this text. A tracked session once REFUSED to declare anything —
    reasoning that the resume line pointed at a handoff which no longer matched its real
    pending work (which it had stashed in a scratchpad) — and wedged its track at 13%
    forever; so the message now says plainly that the handoff is the ONLY inherited
    artifact and that drift is fixed by REWRITING it. And because the daemon must never
    guess a session is safe to kill, the message also makes the session's declaration the
    sole authorization: no ``ready``, no restart.
    """
    head = _WRAPUP_INSIST_HEAD if remaining <= _INSIST_AT else _WRAPUP_SUGGEST_HEAD
    return f"{head}\n\n{_WRAPUP_BODY}".format(
        n=remaining,
        marker_dir=str(signals.marker_dir(repo, topic)),
        state_file=str(signals.state_path(repo, topic)),
        handoff=default_handoff(repo, topic),
        repo=repo,
        topic=topic,
        slug=registry.repo_slug(repo),
    )


def default_handoff(repo: str, topic: str) -> str:
    """``<repo>/plan/<topic>/handoff.md`` — the discovery-convention handoff path."""
    return str(Path(repo) / "plan" / topic / "handoff.md")


def default_resume(repo: str, topic: str) -> str:
    """The first prompt pasted into a (re)started session: read the handoff."""
    return f"read {default_handoff(repo, topic)} and follow it"


_IDLE_NUDGE = """\
You are idle at {n}% context — ABOVE the {threshold}% wind-down line, so you have room to
keep going. Do NOT stop, and do NOT offer to stop, while you are above {threshold}%.

Pick your work back up and continue — your task is in
    {handoff}
Keep going until you are near {threshold}%; the overseer will then send the wind-down.

The overseer has marked your track `idle-with-context-left` in
    {state_file}
That marker clears as soon as you take another turn (the daemon clears it when it sees you
working again); you may also `rm {state_file}` yourself.

If you are NOT free to continue — you are WAITING ON A HUMAN (you asked a question or hit a
decision you cannot make, and cannot raise a prompt, e.g. Codex in YOLO mode) — then say so
out-of-band so the operator is alerted, INSTEAD of sitting idle:
    echo 'blocked: <one-line reason>' > {state_file}"""


def idle_nudge_message(*, remaining: int, threshold: int, repo: str, topic: str) -> str:
    """The single "keep going" nudge injected into an idle session that still has context
    left (``remaining`` > ``threshold``).

    The inverse of :func:`wrapup_message`: instead of "wind down", it says "you have room,
    do not stop above the wind-down line". It is sent at most ONCE per idle episode — the
    ``idle-with-context-left`` marker the daemon writes edge-triggers it, and that marker
    clears when the session next goes non-idle, re-arming a fresh nudge for the next
    episode.

    It also carries the out-of-band escape for the case the daemon cannot see: a session
    genuinely WAITING on a human that expressed it only in prose (Codex in YOLO mode cannot
    raise a structured gate) is told to declare ``blocked: <reason>`` — the existing token —
    so the operator is alerted rather than the track being nudged to keep going.
    """
    return _IDLE_NUDGE.format(
        n=remaining,
        threshold=threshold,
        handoff=default_handoff(repo, topic),
        state_file=str(signals.state_path(repo, topic)),
    )


def default_gitignore_check(repo: str) -> bool:
    """True iff ``<repo>/tmp/overseer/`` is gitignored in ``repo``.

    ``git -C <repo> check-ignore -q tmp/overseer`` exits 0 when the path is
    ignored, 1 when it is not, 128 on error — so only a 0 means "ignored". The
    daemon refuses to start unless every watched repo passes, because the overseer
    writes its markers there and must never dirty a tracked tree. Fail-soft to
    False (treated as "not ignored" → refuse) on any spawn error.
    """
    try:
        completed = subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["git", "-C", repo, "check-ignore", "-q", "tmp/overseer"],  # noqa: S607 — PATH git
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


# The Status cell carries a session-authored NOTE (a `blocked:` reason, or the
# live-outside-tmux detail) that can be arbitrarily long and multi-line. Rendered raw it
# blew up the whole Status column (the column is sized to its widest cell) and broke row
# alignment (maintainer 2026-07-16, after a 705-byte `blocked:` completion summary). So
# the note is flattened to one line and elided in the TABLE; a longer, still-bounded
# preview goes into the `NEEDS YOU` alert (whose full detail the operator reads in the
# tracked pane the alert points at — so a preview is enough and a 705-byte dump is not).
_MAX_NOTE_IN_TABLE = 48
_MAX_REASON_IN_ALERT = 160


def _elide(text: str, limit: int) -> str:
    """``text`` flattened to a single line and truncated to ``limit`` chars with a
    trailing ellipsis (the result is never longer than ``limit``).

    ``" ".join(text.split())`` collapses every whitespace run — including newlines, which
    would otherwise split a table row across lines — into single spaces.
    """
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1].rstrip() + "…"


# --------------------------------------------------------------------------- #
# View + per-track internal state.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, kw_only=True)
class RowView:
    """One rendered table row: the outward projection of a track this tick.

    ``runtime`` is the harness driving the track — ``"claude"`` or ``"codex"`` —
    carried so the table's ``tmux`` column can annotate the session name
    (``livespec (claude)`` / ``livespec1 (codex)``) and the operator can tell at a
    glance which runtime a track is. It is set exactly for a row with a LIVE MANAGED
    pane (``evaluate`` derives it from ``is_codex`` and sets it alongside
    ``tmux=session``); the no-managed-pane rows (``unassigned`` / ``session-gone`` /
    ``live-outside-tmux``) carry ``tmux=None`` and leave it ``None`` — those cells
    render a bare ``—`` with no ``(...)`` (there is no live session, and for the first
    two no runtime either).
    """

    topic: str
    repo: str
    tmux: str | None
    ctx: int | None
    status: str
    note: str | None = None
    runtime: str | None = None


def needs_attention(row: RowView) -> bool:
    """True if ROW is a track a human must go look at (the ``NEEDS YOU`` membership test).

    A malformed state file is matched on the NOTE rather than the status, because it does
    not have a status of its own: ``evaluate`` reports it by hanging a ``BAD state file``
    note on whatever status the track otherwise has. It is fail-closed (treated as no
    declaration) and needs a human, so it belongs in the block.
    """
    if row.status in ATTENTION_STATUSES:
        return True
    if row.note and row.note.startswith("BAD state file"):
        return True
    # A stranded post-respawn resume (R1) is also a NEEDS-YOU row: the daemon keeps
    # retrying the Enter, but the operator should see it — and keeping it here keeps the
    # `_alert` edge-triggered (not re-armed) so it fires once, not every tick.
    return bool(row.note and row.note.startswith(_RESUME_PENDING_NOTE))


def _tmux_cell(row: RowView) -> str:
    """The ``tmux`` column value: the session name annotated with its RUNTIME.

    A row with a live managed pane renders ``<tmux> (<runtime>)`` — ``livespec (claude)``
    / ``livespec1 (codex)`` — so the operator can tell at a glance which harness a track
    is; a no-managed-pane row (``tmux=None``: ``unassigned`` / ``session-gone`` /
    ``live-outside-tmux``) renders the bare ``—`` with no ``(...)``. The annotation is
    part of the CELL, so the column width in :meth:`Supervisor.render` MUST be computed
    from this string, not the bare name, or the column misaligns.

    Single-sourced here so the table (:meth:`Supervisor.render`) and the ``NEEDS YOU``
    block (:meth:`Supervisor._attention_lines`) — the operator's handover surface, where
    knowing the runtime before jumping into a Claude-vs-Codex pane has the same value —
    format the tmux cell identically and cannot drift. The jump command itself still uses
    the bare ``row.tmux`` (``tmux switch-client -t <session>``); only the DISPLAYED cell
    is annotated.
    """
    if row.tmux is None:
        return "—"
    if row.runtime is None:
        return row.tmux
    return f"{row.tmux} ({row.runtime})"


@dataclass
class _InjectState:
    """Per-track wrap-up bookkeeping (in-memory; reset on restart/recovery).

    ``last_ctx`` is the last KNOWN remaining-% (used by
    :meth:`Supervisor._effective_ctx` when a tick reads ctx as unknown — design:
    keep last known, and unknown never triggers a crossing). ``idle_since`` is the epoch
    time the session ENTERED its current continuous-idle episode (None when not cleanly
    idle) — it gates the keep-going nudge behind a minimum idle duration
    (``_IDLE_NUDGE_AFTER``) so a session that is only BRIEFLY at the prompt (between turns)
    is never interrupted. Both are in-memory: a daemon restart resets them, which only ever
    DELAYS a nudge (the safe direction). The injection-round timestamp and the set of
    already-notified escalation bands are DURABLE, in the injection-stamp sidecar
    (``registry.read_injection_stamp`` / ``read_notified_bands`` / ``add_notified_band``),
    so a daemon restart never re-spams a band it already sent — they are not in-memory here.
    """

    last_ctx: int | None = None
    idle_since: float | None = None


@dataclass(frozen=True, kw_only=True)
class _Observation:
    """Everything one tick OBSERVES about a track, before deciding anything.

    :meth:`Supervisor.evaluate` is a two-phase function: gather the facts, then
    run a cascade of guards over them. This record is the seam between the two
    phases — every field is read by the cascade, nothing here decides anything.
    Splitting it out keeps the cascade readable top-to-bottom as one precedence
    order rather than interleaving reads with decisions.

    ``istate`` is deliberately the LIVE ``_InjectState`` object out of
    ``Supervisor._inject``, not a copy: the cascade mutates it (recording an
    injection round), and observation already advanced its idle-episode clock.
    """

    capture: str
    busy: bool
    gate: bool
    idle: bool
    is_codex: bool
    runtime: str
    codex_fallback: bool
    claude_status: str | None
    eff_ctx: int | None
    istate: _InjectState
    declared: signals.TrackState | None
    malformed: bool
    blocked: str | None
    acked: bool
    ready: bool


# --------------------------------------------------------------------------- #
# The daemon.
# --------------------------------------------------------------------------- #


@dataclass
class Supervisor:
    """The deterministic multi-track supervisor.

    All external state is injectable so tests drive it with a fake ``tmux`` and
    ``tmp_path`` stores — no real tmux, no touching ``~``. ``watch_repos`` may
    be given explicitly (tests) or read from the ``$HOME`` watch-set declaration
    (daemon CLI).
    """

    tmux: tmuxio.PaneDriver = field(default_factory=tmuxio.TmuxIO)
    store_path: str | os.PathLike[str] | None = None
    stamp_path: str | os.PathLike[str] | None = None
    watch_repos: list[str] | None = None
    watch_set_path: str | os.PathLike[str] | None = None
    extra_repos: list[str] = field(default_factory=list)
    # Daemon-wide default warn threshold (remaining-% at which the FIRST wrap-up
    # fires) for any track WITHOUT a per-track ``ctx_threshold`` override. Set from
    # ``overseerd --warn-percent`` via ``run_daemon``; a track's own override wins.
    warn_percent: int = registry.DEFAULT_CTX_THRESHOLD
    # Resolved at CONSTRUCTION rather than at import, so a caller (or a test)
    # that redirects sys.stdout first still gets the stream it expects.
    out: IO[str] = field(default_factory=lambda: sys.stdout)
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
    # Codex session-discovery seams (default: real /proc scan + ~/.codex; the beside-tests
    # inject fakes). Unlike Claude — whose candidate pids come from the injected registry
    # dir (`sessions_dir`) — Codex discovers its pids by a live `/proc` `comm==codex` scan
    # and reads `~/.codex/session_index.jsonl` for the topic, so its host coupling is a
    # DISTINCT reader set. It MUST be injectable or every adopt/refresh test would read the
    # host's real /proc and ~/.codex (test-isolation defect #6). `codex_home=None` means the
    # codex_sessions functions resolve the real `~/.codex` themselves, so it is threaded
    # through as-is (no `_sessions_dir`-style helper needed). `ppid_of` (the tmux-join walk)
    # is shared with the Claude seam above.
    codex_home: str | os.PathLike[str] | None = None
    codex_pids_of_comm: Callable[[str], list[int]] = codex_sessions.proc_pids_of_comm
    codex_fd_targets_of: Callable[[int], list[str]] = codex_sessions.proc_fd_targets
    # Host-precondition seams (default: the real `/proc` + a real PATH lookup; the
    # beside-tests' `_sup` factory defaults them to a SUPPORTED-looking host so the
    # suite never depends on the RUNNER having tmux). Linux + tmux is a DECLARED
    # REQUIREMENT, deliberately NOT an abstraction boundary: the session readers read
    # `/proc/<pid>/stat`, which macOS does not have AT ALL, and every acting mechanic
    # drives a real tmux. `which` is asked about the literal `tmux` NAME rather than a
    # caller's injected `tmux_bin`, because this gate asks "is this host supported at
    # all?" — not "is that particular binary resolvable", which a fake tmux would
    # wrongly satisfy.
    proc_root: str | os.PathLike[str] = "/proc"
    which: Callable[[str], str | None] = shutil.which
    codex_cwd_of: Callable[[int], str | None] = codex_sessions.proc_cwd
    # Startup gate: `<repo>/tmp/overseer/` MUST be gitignored (the overseer only
    # writes temp files, never tracked ones). Injectable so tests fake the check.
    gitignore_check: Callable[[str], bool] = default_gitignore_check
    # The daemon's OWN pane (its `$TMUX_PANE`, inherited because `overseerd` is launched
    # inside the top pane). Used only to badge the attention count onto the tmux WINDOW
    # name — the one overseer surface visible from a session the operator is attached to.
    # None (not in tmux, or a test) simply disables the badge.
    own_pane: str | None = None
    _inject: dict[tuple[str, str], _InjectState] = field(default_factory=dict, init=False)
    # Edge-trigger memory for `_alert`: track key → the last alert line emitted for it.
    # Keeps the log an EVENT HISTORY (one line per condition entered) instead of the same
    # line re-emitted every tick. Re-armed in `evaluate` when the track goes healthy.
    _alerted: dict[tuple[str, str], str] = field(default_factory=dict, init=False)
    # Last window name written, so the badge is only re-sent when the count CHANGES
    # (a tmux call every tick for an unchanged name is pure noise).
    _window_name: str | None = field(default=None, init=False)
    # `{tmux_session: claude_registry_status}` for this tick, recomputed at the top of
    # every `build_rows`. Claude's own live self-report ("busy"/"idle"/"waiting") is an
    # AUTHORITATIVE busy signal that catches in-process sub-agents the process-tree walk
    # cannot see. Empty for Codex sessions (not in Claude's registry) and in direct-
    # `evaluate` beside-tests that don't set it.
    _claude_status: dict[str, str] = field(default_factory=dict, init=False)
    # `{tmux_session: {claude_registry_name, ...}}` for this tick, recomputed beside
    # `_claude_status`. The identity gate (`_pane_is_managed_claude`) checks that the track's
    # TOPIC is among the live Claude names in the pane's tmux session — parity with the Codex
    # gate's `name == topic` check — so a generic reused tmux window the store maps to topic A
    # but now running topic B's Claude is not mis-driven (R2, 2026-07-18). It is a SET (not a
    # last-wins single) so a helper Claude sharing the tmux session cannot shadow the track's
    # own name and flap it to `session-gone` (review SF5). Empty for Codex sessions (not in
    # Claude's registry) and in direct-`evaluate` beside-tests that don't set it — an unknown
    # tmux session preserves the prior repo+process gate (fail-soft).
    _claude_names: dict[str, set[str]] = field(default_factory=dict, init=False)
    # {tmux_session: CodexSession} for every live NAMED codex session, recomputed each
    # tick beside _claude_status. Membership IS the exact answer to "is this pane
    # Codex?" — the pane command says `bun` (the launcher), which is too generic to
    # trust. Typed loosely to keep the dataclass free of a codex_sessions import cycle.
    _codex: dict[tuple[str, str], codex_sessions.CodexSession] = field(
        default_factory=dict, init=False
    )
    # Topics that appear in >=2 watched repos this tick, recomputed at the top of
    # `build_rows` (before adopt/auto_link/evaluate run, so every session-name
    # derivation this tick sees the same set). `registry.tmux_id` repo-qualifies
    # ONLY these — so a session is named after its bare plan topic unless that topic
    # genuinely collides across repos (maintainer-declared 2026-07-19). Empty in
    # direct-`evaluate` beside-tests that don't run `build_rows` — which yields the
    # bare-topic name, the correct default for a single-repo fixture.
    _colliding: frozenset[str] = field(default_factory=frozenset, init=False)

    # ----------------------------------------------------------------- #
    # Diagnostics.
    # ----------------------------------------------------------------- #

    def _log(self, message: str) -> None:
        streams.write_stderr(text=f"{_iso_now()} overseer: {message}\n")

    def _surface(self, message: str) -> None:
        """Surface a DAEMON-level alert to the operator (stderr; the bottom pane reads it).

        For anything scoped to a TRACK, use :meth:`_alert` instead — it guarantees the
        tmux coordinates the operator needs in order to act.
        """
        streams.write_stderr(text=f"{_iso_now()} overseer[SURFACE]: {message}\n")

    def _alert(
        self,
        *,
        repo: str,
        topic: str,
        session: str | None,
        pane: str | None,
        message: str,
    ) -> None:
        """Surface a TRACK-scoped alert that always names WHERE to act.

        Every track alert carries the plan topic, its repo, the tmux SESSION and PANE
        holding it, and a copy-pasteable jump command. ``repo::topic`` alone tells the
        operator WHAT is stuck but never WHERE to go — they were left to hunt for the
        session by hand (maintainer 2026-07-14).

        This is load-bearing for the notify-never-block contract (invariant 8): because
        the overseer NEVER prompts on a track's behalf, this line is the operator's ONLY
        handover, so it MUST be self-sufficient. Every new track-scoped alert goes
        through here — never a bare ``_surface`` with an f-string of ``repo::topic``.

        EDGE-TRIGGERED: emitted when a track ENTERS a condition (or the condition's text
        changes), NOT once per tick. The log is the daemon's EVENT HISTORY — the surface
        the bottom pane reads to answer "what happened, and when?" — while CURRENT state
        is owned by the re-rendered table + its ``NEEDS YOU`` block. Re-emitting an
        unchanged alert every tick buried that history in thousands of identical lines (a
        track blocked overnight logged ~3,000 of them) and answered a question the table
        already answers better. The re-arm is in :meth:`evaluate`: when a track returns to
        a healthy status its entry is dropped, so the NEXT time it goes bad it reports
        again.
        """
        where = f"tmux session '{session}' pane {pane}" if session else "no live tmux session"
        jump = f" — jump: tmux switch-client -t {session}" if session else ""
        line = f"{topic} ({registry.repo_slug(repo)}) — {message} [{where}]{jump}"
        key = _key(repo, topic)
        if self._alerted.get(key) == line:
            return
        self._alerted[key] = line
        self._surface(line)

    # ----------------------------------------------------------------- #
    # Watch-set + discovery ⋈ mapping.
    # ----------------------------------------------------------------- #

    def _resolve_watch(self) -> list[str]:
        if self.watch_repos is not None:
            return [os.path.normpath(r) for r in self.watch_repos]
        if self.watch_set_path is not None:
            return registry.watch_set_from_config(self.watch_set_path, self.extra_repos)
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

        A link is created ONLY when a session named ``tmux_id(repo, topic)`` (the
        bare plan topic, or ``<repo-slug>-<topic>`` on a cross-repo collision — the
        SAME name the daemon would spawn) exists AND its ``#{pane_current_path}``
        resolves inside the row's repo. The ``path_in_repo`` guard is what actually
        prevents cross-linking two repos that share a topic (blocker #8): even if a
        colliding topic were not repo-qualified, the pane's cwd must match the row's
        repo. Returns the new mapped Track, or None if not linked.
        """
        session = registry.tmux_id(track.repo, track.topic, self._colliding)
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
        guard is needed. The mapping's ``tmux`` field is the ACTUAL session name
        holding the work (any name — a generic `livespec`, an operator-renamed one) —
        NOT necessarily the ``tmux_id`` the daemon would derive+spawn. A
        ``(repo, topic)`` already mapped is left untouched (no double-add).
        Returns the newly-adopted Tracks.

        Codex sessions are NOT in Claude's registry, but they ARE adopted through the
        SAME path: this method sums ``claude_sessions.map_named_sessions`` +
        ``codex_sessions.map_codex_sessions`` (below), both emitting the same
        ``(tmux, name, cwd)`` triple, so a live NAMED codex session is adopted exactly
        like a Claude one. Distinct from :meth:`auto_link`, which links only the
        derived ``tmux_id`` session (the bare topic, or ``<repo-slug>-<topic>`` on a
        cross-repo collision) the daemon itself launches.
        """
        watch = self._resolve_watch()
        active: dict[str, set[str]] = {}
        for repo, topic, _ in registry.discover_plans(watch):
            active.setdefault(repo, set()).add(topic)
        existing = {(t.repo, t.topic): t.tmux for t in registry.read_mapping(self.store_path)}
        pane_pids = self.tmux.pane_pid_sessions()
        # BOTH runtimes, through ONE path. `codex_sessions.map_codex_sessions` emits the
        # same `(tmux_session, name, cwd)` triple as its Claude twin precisely so adoption
        # never grows a parallel Codex branch that could drift. Codex sessions are absent
        # from Claude's registry, so without this they are invisible: the plan is
        # discovered and shows `unassigned` while a real session runs in its tmux
        # (maintainer-reported live 2026-07-17: rop-sweep-library-checks in
        # `livespec-dev-tooling`, rop-sweep-consumer-cleanup in `livespec3`).
        #
        # `Codex Companion Task: …` threads filter themselves out below: their names are
        # not active plan topics, so they fail the same test any non-topic name fails.
        mapped = claude_sessions.map_named_sessions(
            self._sessions_dir(),
            pane_pids,
            ppid_of=self.ppid_of,
            starttime_of=self.starttime_of,
        ) + codex_sessions.map_codex_sessions(
            pane_pids,
            codex_home=self.codex_home,
            ppid_of=self.ppid_of,
            pids_of_comm=self.codex_pids_of_comm,
            cwd_of=self.codex_cwd_of,
            fd_targets_of=self.codex_fd_targets_of,
        )
        # Detect (repo, topic) claimed by MORE THAN ONE live session this tick. Re-pointing
        # such a track would FLIP-FLOP between the sessions' tmux ids every tick — two store
        # rewrites + two "re-pointed" log lines forever (review SF1) — since which one "wins"
        # is just `mapped` order. When ambiguous we skip the re-point entirely and leave the
        # mapping as-is (the identity gate + set-valued `_claude_names` still classify each
        # pane correctly). Resolve repo the same way the loop does, so the counts match.
        live_keys: list[tuple[str, str]] = []
        for _session, name, cwd in mapped:
            r = next((r for r in watch if signals.path_in_repo(cwd, r)), None)
            if r is not None and name in active.get(r, set()):
                live_keys.append((r, name))
        ambiguous = {k for k, count in collections.Counter(live_keys).items() if count > 1}
        adopted: list[registry.Track] = []
        for session, name, cwd in mapped:
            repo = next((r for r in watch if signals.path_in_repo(cwd, r)), None)
            if repo is None:
                continue
            topic = name
            if topic not in active.get(repo, set()):
                continue
            if (repo, topic) in existing:
                # Already mapped. RE-POINT if the live named session has MOVED to a
                # different tmux session than the store records (R2, 2026-07-18): generic
                # reused windows (`livespec1`…) get cycled across topics, so a frozen
                # binding would let an act target the wrong pane. The data is already in
                # `mapped`; rewrite the row's `tmux` and log it like an adoption. Guarded
                # so a steady-state tick (tmux unchanged) never touches the store, and
                # idempotent (`repoint_tmux` no-ops + returns False when unchanged). SKIP
                # when ambiguous (>1 live session for this track) so it cannot flip-flop.
                if (
                    (repo, topic) not in ambiguous
                    and existing[(repo, topic)] != session
                    and registry.repoint_tmux(repo, topic, session, self.store_path)
                ):
                    self._log(
                        f"re-pointed {repo}::{topic} tmux {existing[(repo, topic)]} → {session}"
                    )
                    existing[(repo, topic)] = session
                continue
            track = registry.Track(
                topic=topic,
                repo=repo,
                tmux=session,
                handoff=default_handoff(repo, topic),
                resume=default_resume(repo, topic),
            )
            registry.append_mapping(track, self.store_path, added_at=_iso_now())
            existing[(repo, topic)] = session
            adopted.append(track)
            self._log(f"adopted session {session} → {repo}::{topic}")
        return adopted

    def _sessions_dir(self) -> str | os.PathLike[str]:
        """The Claude session-registry dir (injected override, else the real ``~/.claude``)."""
        return (
            self.sessions_dir
            if self.sessions_dir is not None
            else claude_sessions.default_sessions_dir()
        )

    def _refresh_codex_sessions(self) -> None:
        """Recompute this tick's ``{(tmux_session, name): CodexSession}`` map (read-only).

        The Codex twin of :meth:`_refresh_claude_status`, and the ONLY honest way to ask
        "is this pane Codex?": tmux reports a codex pane's ``#{pane_current_command}`` as
        **`bun`** (the launcher; the vendored codex binary is its child), and `bun` is
        generic — any bun app matches it. Membership in this map is exact: a session is in
        it only because a real codex process, holding a real rollout, resolved to that
        tmux session THIS tick. Keyed by ``(tmux_session, name)`` so two codex sessions
        sharing one tmux session never shadow each other (see
        :func:`codex_sessions.codex_by_tmux_session`). Derived live, so it needs no stored
        ``runtime`` field on the mapping and cannot drift. Fail-soft to an empty map (no
        codex running is the overwhelmingly common case).
        """
        self._codex = codex_sessions.codex_by_tmux_session(
            self.tmux.pane_pid_sessions(),
            codex_home=self.codex_home,
            ppid_of=self.ppid_of,
            pids_of_comm=self.codex_pids_of_comm,
            cwd_of=self.codex_cwd_of,
            fd_targets_of=self.codex_fd_targets_of,
        )

    def _refresh_claude_status(self) -> None:
        """Recompute this tick's ``{tmux_session: claude_status}`` map (read-only).

        Runs at the top of every ``build_rows`` — including the read-only ``list`` path —
        so ``evaluate`` can fold Claude's own ``status: "busy"`` self-report into its busy
        check. It reads only the registry + ``/proc`` (no store mutation), so it is safe on
        the read-only path. Fail-soft: any read error yields an empty map (no session
        marked busy from this signal), never a raised exception.
        """
        pane_pids = self.tmux.pane_pid_sessions()
        # `status` feeds the busy check (last-wins is fine); `names` feeds the identity gate's
        # `topic in names` parity check (R2) and is a SET so a helper Claude in the same tmux
        # session cannot shadow the track's name (review SF5). Both from the same registry.
        self._claude_status = claude_sessions.status_by_tmux_session(
            self._sessions_dir(), pane_pids, ppid_of=self.ppid_of, starttime_of=self.starttime_of
        )
        self._claude_names = claude_sessions.names_by_tmux_session(
            self._sessions_dir(), pane_pids, ppid_of=self.ppid_of, starttime_of=self.starttime_of
        )
        self._refresh_codex_sessions()

    def build_rows(self, *, act: bool = True) -> list[registry.Track]:
        """Discovery ⋈ mapping (the tick's row set).

        When ``act`` (the daemon loop) this runs archive-GC + registry adoption +
        auto-link, all of which MUTATE the store. When NOT ``act`` (the ``list``
        command, advertised read-only) it does NONE — it just joins discovery
        against the current mapping, so `list` cannot silently rewrite / GC /
        adopt / re-link the store out from under a running daemon (adversarial code
        review 2026-07-13, blocker B6).
        """
        self._refresh_claude_status()
        watch = self._resolve_watch()
        discovered = registry.discover_plans(watch)
        # Recompute the cross-repo collision set for THIS tick before any session-name
        # derivation (adopt / auto_link / evaluate → `_session_of`) runs, so they all
        # agree on which topics must be repo-qualified. Set ABOVE the `not act` return so
        # the read-only `list` path derives display names identically.
        self._colliding = registry.colliding_topics(discovered)
        if not act:
            return registry.join(discovered, registry.read_mapping(self.store_path))
        _ = self.archive_gc()
        # Continuous adoption (not just at bootstrap): pick up any live Claude
        # session whose registry name is now an active topic — so a session that
        # was mid-prompt, renamed, or launched after startup is tracked within one
        # tick rather than being missed forever.
        _ = self.adopt_sessions()
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
        # A mapped track carries its real session name (`track.tmux`); only an
        # unmapped one falls back to the derived name, which must use THIS tick's
        # collision set so it matches what `start`/`auto_link` would spawn.
        return track.tmux or registry.tmux_id(track.repo, track.topic, self._colliding)

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

    def _is_codex_track(
        self, session: str | None, repo: str, topic: str, target: str | None = None
    ) -> bool:
        """True iff ``target``'s pane is a live codex session for THIS plan, in THIS repo.

        TWO conditions, and BOTH are load-bearing — one is exact but session-scoped, the
        other pane-scoped but generic, and only together are they exact AND pane-scoped:

        1. ``self._codex`` (rebuilt each tick from real codex processes holding real
           rollouts) has a session keyed by ``(this tmux, this topic)`` whose cwd is in
           this repo. Never a guess. Keyed by ``(tmux, name)`` — not tmux alone — so a
           SECOND codex sharing this tmux session (a different topic) does not shadow this
           track's own session (#4).
        2. ``target``'s OWN pane command is codex-like. `bun` is far too generic to gate
           on alone (any bun app matches), which is why (1) exists — but it is exactly
           what makes this PANE-scoped.

        **Why (2) was added (adversarial review, 2026-07-17).** With only (1) this was
        session-scoped while the Claude identity gate is pane-scoped, so ANY codex process
        resolving into a Claude track's tmux session — a `codex resume <topic>` spawned
        from INSIDE that Claude session's own Bash tool, or a codex TUI opened in a second
        window to dual-drive the same plan — reclassified the live CLAUDE track as codex.
        The consequence is now DESTRUCTIVE, not merely quiet: a Codex track is a full
        citizen (2026-07-17), so a misclassified Claude track would be restarted on its
        `ready` via `codex resume` — the WRONG-runtime respawn that destroys the live
        Claude session — and its wrap-up would be submit-verified as Codex (waiting for a
        busy pane that a Claude submit need not produce). Pane-scoping (2) closes it. The
        naming convention this very change establishes ("codex threads named after plan
        topics") is what makes the collision reachable, so this is not exotic.
        """
        live = self._codex.get((session or "", topic))
        if live is None:
            return False
        # The (tmux, topic) key already pins name == topic; only the repo remains to check.
        if not signals.path_in_repo(live.cwd, repo):
            return False
        if target is None:
            return True  # no pane to check against (callers that only have the mapping)
        return signals.pane_is_codex(self.tmux.pane_current_command(target))

    def _pane_is_managed(self, target: str, repo: str, topic: str, session: str | None) -> bool:
        """The identity gate for EITHER runtime: is this pane OUR session, in OUR repo?

        Claude via the pane's own process identity + the live session's name; Codex via
        the live per-tick session map (`bun` is too generic to gate on). Fail-closed:
        anything unproven is not ours.
        """
        return self._pane_is_managed_claude(target, repo, topic, session) or self._is_codex_track(
            session, repo, topic
        )

    def _pane_is_managed_claude(
        self, target: str, repo: str, topic: str, session: str | None
    ) -> bool:
        """True iff ``target``'s pane is a live Claude TUI for THIS topic, in ``repo``.

        The identity gate for EVERY act (inject / restart). ``pane_is_claude`` and
        ``path_in_repo`` exist and are tested, but the shipped daemon wired them
        only into auto-link and the restart poll, NOT the act path — so a tracked
        Claude that had exited to a shell (the pane retains the dead TUI's idle-box
        frame) would get the wrap-up pasted INTO THE SHELL, where the
        ``echo ready > …/.overseer-state`` line executes and FORGES a valid
        declaration (adversarial code review 2026-07-13, blocker B3 = Codex #1). Gating
        every act on process identity + cwd closes that, and hardens B1's residual
        (a name that resolved to the wrong session would fail the cwd check).

        **The ``topic in names`` parity check (R2, 2026-07-18).** The Codex gate is
        pane-scoped (``_is_codex_track`` requires ``live.name == topic``); the Claude gate
        was not, so a generic reused tmux window (``livespec1``…) the store maps to topic A
        but now running topic B's Claude — same repo — passed the process+cwd check and got
        A's wrap-up injected into B, then a ``ready`` respawn-KILLED B as A. Here a live Claude
        named for THIS topic must be present in this pane's tmux session (``self._claude_names``
        — the SET of all live Claude names in that tmux session, so a HELPER Claude sharing the
        session cannot shadow the track's own name; review SF5). Reject on POSITIVE proof that
        the tmux session has live Claude names but NOT this topic's; an UNKNOWN tmux session
        (empty set — registry miss, or a direct-``evaluate`` test that did not populate the
        map) preserves the prior process+cwd gate — fail-soft, so a transient registry miss can
        never flap a live track to ``session-gone``.

        ``target`` is the resolved pane id (RB3), so the identity read is of the
        exact pane, never a prefix-matched sibling.
        """
        if not signals.pane_is_claude(self.tmux.pane_current_command(target)):
            return False
        if not signals.path_in_repo(self.tmux.pane_current_path(target), repo):
            return False
        names = self._claude_names.get(session or "")
        return not names or topic in names

    def _clear_state(self, track: registry.Track) -> None:
        """Delete a track's state file, clear its stamp, AND reset its inject state.

        Used both after a successful restart and when a session that declared ``ready``
        genuinely resumes work. ``clear_injection_stamp`` deletes the sidecar key,
        resetting BOTH the round's ``at`` and its notified bands — so after a clear (or
        a restart) the round fully resets and every escalation band can fire again in
        the next round. Clearing on the FILESYSTEM (state file + stamp) makes it durable
        across a daemon restart. It ALSO pops the in-memory ``_inject`` state
        (mirroring ``_do_restart``) so the stale ``last_ctx`` does not linger; the
        next threshold crossing opens a clean round that writes a new stamp
        (adversarial code re-review 2026-07-13, blocker RB2).
        """
        try:
            signals.state_path(track.repo, track.topic).unlink(missing_ok=True)
        except OSError as exc:
            self._log(f"could not delete state file for {track.repo}::{track.topic}: {exc}")
        registry.clear_injection_stamp(track.repo, track.topic, self.stamp_path)
        _ = self._inject.pop(_key(track.repo, track.topic), None)

    def _void_if_stale(self, track: registry.Track, *, ready: bool) -> bool:
        """Void a stale ``ready`` declaration on a busy tick ONLY if past the grace.

        Returns the (possibly cleared) ``ready`` flag. A declaration younger than
        ``_MARKER_VOID_GRACE`` is the declaring turn's own busy tail and is LEFT
        intact (RB1); an older one means the session resumed work after declaring
        ready, so its (now false) declaration is voided.
        """
        if not ready:
            return ready
        state = signals.read_state(track.repo, track.topic)
        if state is None:
            return ready  # unreadable → leave it; ready_valid already gates
        age = self.now() - state.mtime
        if age > _MARKER_VOID_GRACE:
            self._clear_state(track)
            self._log(
                f"voided stale ready declaration for {track.repo}::{track.topic} "
                f"(age {age:.0f}s > {_MARKER_VOID_GRACE:.0f}s grace; session resumed work)"
            )
            return False
        return ready

    def _void_stale_blocked(
        self, track: registry.Track, blocked: str | None, *, generating: bool
    ) -> str | None:
        """Void a ``blocked:`` declaration the session has outlived. Returns it, or None.

        A session that is GENERATING is, **by observation, not waiting on a human** — so a
        ``blocked:`` declaration still on disk is provably false. This is NOT the daemon
        making a semantic judgment (invariant 1): it is not guessing that the session is
        unblocked, it is reading that the session is producing tokens, which is
        incompatible with waiting for an answer.

        Why it is needed: nothing else retires a ``blocked:``. ``_clear_state`` runs only
        on the daemon's own restart path, so a pane replaced OUT-OF-BAND (a hand-restarted
        session, a `/clear`) inherits its predecessor's declaration — found live
        2026-07-16, where a fresh session rendered `working (awaiting maintainer next-step
        decision — Codex…)`, a reason written by a session that no longer existed. Left
        alone, the dead reason also fires a false ``blocked:human`` alert the moment the
        session goes idle.

        Two bounds keep it honest, each pinned by a test:

        - **``generating``, not merely ``busy``.** A session busy ONLY via a live
          ``Bash(run_in_background)`` command (Claude ``shell``) is sitting AT ITS PROMPT
          and can legitimately be awaiting a human while a build runs — not provably
          stale, so never voided however old. Only a real generation spinner or Claude
          ``busy`` (actively generating / an in-process sub-agent) qualifies.
        - **The same ``_MARKER_VOID_GRACE`` as ``ready`` (RB1).** The declaring turn's own
          final text streams for 10-60s AFTER the write, so a young declaration must
          survive its own busy tail — else every legitimate declaration is destroyed
          before the pane ever goes idle.

        An idle blocked session is never touched: it keeps its declaration and keeps
        alerting, forever, until the session itself retracts it.
        """
        if blocked is None or not generating:
            return blocked
        state = signals.read_state(track.repo, track.topic)
        if state is None or state.token != signals.STATE_BLOCKED:
            return blocked  # unreadable, or no longer a block → leave it
        age = self.now() - state.mtime
        if age <= _MARKER_VOID_GRACE:
            return blocked  # the declaring turn's own tail (RB1)
        self._clear_state(track)
        self._log(
            f"voided stale blocked declaration for {track.repo}::{track.topic} "
            f"(age {age:.0f}s > {_MARKER_VOID_GRACE:.0f}s grace; session resumed generating)"
        )
        return None

    def _write_idle_nudge_state(self, track: registry.Track) -> None:
        """Write the daemon-owned ``idle-with-context-left`` marker to the state file.

        Called ONLY after the nudge paste lands, and ONLY when the file had no session
        declaration (guarded in :meth:`evaluate`), so it can never overwrite a ``ready`` /
        ``blocked`` / ``winding-down``. It edge-triggers the single-prompt-per-episode rule
        and drives the row's ``idle-with-context-left`` status.
        """
        path = signals.state_path(track.repo, track.topic)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            _ = path.write_text(signals.STATE_IDLE_WITH_CONTEXT_LEFT + "\n", encoding="utf-8")
        except OSError as exc:
            self._log(f"could not write idle-nudge marker for {track.repo}::{track.topic}: {exc}")

    def _clear_idle_nudge_state(self, track: registry.Track) -> None:
        """Clear the ``idle-with-context-left`` marker when the session leaves the idle
        episode (it went non-idle / took a turn) — re-arming a fresh nudge next episode.

        Re-reads the file immediately before unlinking and removes it ONLY if it is still
        the daemon's own marker, so a ``ready`` / ``blocked`` the session wrote in the same
        tick is never clobbered. Unlike :meth:`_clear_state` it touches neither the
        injection stamp nor the in-memory inject state — the nudge opens no round.
        """
        current = signals.read_state(track.repo, track.topic)
        if current is None or current.token != signals.STATE_IDLE_WITH_CONTEXT_LEFT:
            return
        try:
            signals.state_path(track.repo, track.topic).unlink(missing_ok=True)
        # The ONLY uncovered branch in this module, and deliberately so. The read
        # above returns unless the marker is a readable regular file, so every
        # root-proof way to make `unlink` fail (a directory at the path, a file
        # where the parent should be) also makes that read return None and returns
        # first. What remains is a permission-denied PARENT — and CI runs its
        # container steps as root, where chmod denies nothing. A test would pass
        # locally and silently stop exercising this in CI, which is worse than no
        # test. Its sibling in `_clear_state` unlinks with no preceding read, so
        # that one IS covered (a directory there yields EISDIR for every uid).
        except OSError as exc:  # pragma: no cover
            self._log(f"could not clear idle-nudge marker for {track.repo}::{track.topic}: {exc}")

    def _nudge_idle_with_context(
        self,
        track: registry.Track,
        target: str,
        eff_ctx: int,
        threshold: int,
        *,
        is_codex: bool = False,
    ) -> None:
        """Send the single "keep going" nudge to an idle session that still has context
        left, and — only if the paste lands — write the ``idle-with-context-left`` marker
        so it fires at most ONCE per idle episode.

        The inverse of :meth:`_maybe_inject`: it fires ABOVE the threshold to keep a session
        from stopping early, not below it to wind one down. The marker is written AFTER a
        successful submit (as ``_maybe_inject`` marks its bands only on success), so a
        failed paste re-nudges next tick rather than silently marking the episode handled.

        ``is_codex`` selects the runtime-appropriate submit verification (a Codex submit is
        confirmed by the pane going busy, not by a cleared ``❯`` box).
        """
        repo, topic = track.repo, track.topic
        message = idle_nudge_message(remaining=eff_ctx, threshold=threshold, repo=repo, topic=topic)
        if self._submit_prompt(target, message, expect_codex=is_codex):
            self._write_idle_nudge_state(track)
            self._log(
                f"nudged idle-with-context-left {repo}::{topic} "
                f"(ctx {eff_ctx}% > threshold {threshold}%)"
            )
        else:
            self._alert(
                repo=repo,
                topic=topic,
                session=self._session_of(track),
                pane=target,
                message="idle-with-context-left nudge FAILED (paste did not land); will retry",
            )

    def _live_session_outside_tmux(
        self, repo: str, topic: str
    ) -> claude_sessions.ClaudeSession | None:
        """The live Claude registry session for ``(repo, topic)`` running OUTSIDE any
        tmux pane, or None.

        Separates a genuinely gone track from one whose mapped tmux session died while a
        Claude session for the same plan kept working in a NON-tmux terminal (e.g. a bare
        SSH shell). It reads the SAME registry ``adopt_sessions`` uses
        (:func:`claude_sessions.read_live_sessions` — every live named session, tmux or
        not), matches a session whose ``name`` is the topic and whose ``cwd`` is in the
        repo, and returns it ONLY when it does not resolve to any tmux pane
        (:func:`claude_sessions.resolve_tmux_session` is None). A session that resolves to
        a DIFFERENT tmux session is deliberately NOT returned — that is a re-mapping
        concern, not an out-of-tmux one. Such an out-of-tmux session is alive and doing
        work but UNMANAGEABLE by the daemon (no pane to capture / inject / respawn), so
        ``evaluate`` reports it as the informational ``live-outside-tmux`` rather than the
        alarming ``session-gone``.
        """
        pane_pids = self.tmux.pane_pid_sessions()
        for live in claude_sessions.read_live_sessions(
            self._sessions_dir(), starttime_of=self.starttime_of
        ):
            if live.name != topic or not signals.path_in_repo(live.cwd, repo):
                continue
            if (
                claude_sessions.resolve_tmux_session(
                    live.pid, pane_pid_to_session=pane_pids, ppid_of=self.ppid_of
                )
                is None
            ):
                return live
        return None

    def _no_managed_pane_row(self, *, repo: str, topic: str) -> RowView:
        """The row for a track with NO live managed pane: ``live-outside-tmux`` or ``session-gone``.

        The single home for "this track has no pane we can drive". Reached THREE ways —
        the mapped tmux session is gone; or it survives but its session exited to a bare
        shell; or the pane is a genuinely FOREIGN one (fails the identity gate) — all of
        which must answer identically: they are the same fact about the track (no pane to
        drive), and only the tmux housekeeping differs. Keeping one path also keeps the
        live-outside-tmux fallback from being wired into just one of them (it was, and
        the shell case reported a live session as the now-deleted ``not-claude``).

        A Claude for the same plan may still be running in a NON-tmux terminal (a bare
        SSH shell): alive and working, but unmanageable by this tmux-only daemon (no
        pane to capture / inject / respawn). That is the informational
        ``live-outside-tmux``, NOT the alarming ``session-gone`` — the operator should
        not be told finished-looking work was lost when it is merely out of reach.

        **Both rows report ``tmux=None``, and that is the point of the helper**
        (maintainer-declared 2026-07-16: "it shouldn't display the session name; the
        session doesn't exist in that panel anymore"). The ``tmux`` cell means *the tmux
        session HOLDING this track* — an assertion about a live session, not a record of
        the mapping. Every row reaching here has no session in that tmux session: it is
        gone outright, or it survives holding only a bare shell, or the Claude is alive
        somewhere outside tmux entirely. Naming it anyway rendered a live-looking
        ``livespec1`` for a track whose session had exited — the mapping is still in the
        store, and ``session-gone`` already says "this WAS mapped and is now dead", so
        nothing is lost by leaving the cell empty. ``_alert`` degrades on its own
        (``no live tmux session``, no jump command — there is nowhere to jump).

        (The former ``not-claude`` status — which named a foreign pane's session — was
        DELETED, 2026-07-17; a foreign pane now routes here like any other no-managed-pane
        case and reports ``tmux=None``. The identity gate itself is unchanged and still
        governs every act.)
        """
        live = self._live_session_outside_tmux(repo, topic)
        if live is not None:
            note = (
                f"live Claude session (pid {live.pid}) running OUTSIDE tmux — "
                f"daemon cannot manage it"
            )
            if live.status:
                note += f"; self-reported status {live.status}"
            return RowView(
                topic=topic,
                repo=repo,
                tmux=None,
                ctx=None,
                status="live-outside-tmux",
                note=note,
            )
        return RowView(topic=topic, repo=repo, tmux=None, ctx=None, status="session-gone")

    def _observe(
        self, track: registry.Track, *, session: str, target: str, key: tuple[str, str]
    ) -> _Observation:
        """Gather every fact :meth:`evaluate`'s guard cascade decides on.

        Called only after the identity gate has proven ``target`` is our managed
        pane, so every read here is safe to perform. This method DECIDES nothing:
        it never pastes, respawns, alerts, or writes a stamp. Its one mutation is
        advancing the track's continuous-idle clock, which is part of observing
        how long the session has been idle rather than a decision about it.
        """
        repo, topic = track.repo, track.topic
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
        # Claude's own live self-report is AUTHORITATIVE for an adopted Claude session,
        # and its vocabulary maps cleanly onto busy-ness (`~/.claude/sessions/<pid>.json`
        # `status`): `busy` = actively generating / running an in-process sub-agent (which
        # spawns no descendant shell, so the process-walk misses it); `shell` = at the
        # prompt with a live `Bash(run_in_background)` command — Claude's OWN, accurate
        # background-work signal; `waiting` = at a gate/prompt for the human; `idle` =
        # nothing pending. So for a session we have adopted we IGNORE the process-tree
        # shell-walk entirely and trust `status`: it is strictly better than the walk,
        # which both MISSED sub-agents (false-idle) and false-fired on lingering/transient
        # shells (false-working). `has_active_subshell` (`bg_shell`) remains ONLY the
        # runtime-agnostic FALLBACK for a session with no registry entry (Codex).
        # `claude_status is None` ⇒ not an adopted Claude session.
        claude_status = self._claude_status.get(session)
        claude_busy = claude_status in _CLAUDE_BUSY_STATUSES
        codex_fallback = claude_status is None and bg_shell
        busy = signals.is_busy(capture) or claude_busy or codex_fallback
        gate = signals.is_structured_gate(capture)
        is_codex = self._is_codex_track(session, repo, topic, target)
        # The row's RUNTIME, derived ONCE here where `is_codex` is already known, then
        # carried onto every row below that has a live managed pane (`tmux=session`) so the
        # table's tmux column can annotate the session name (`livespec (claude)` /
        # `livespec1 (codex)`). Every branch reaching this point HAS a managed pane (the
        # no-managed-pane / unassigned rows returned above with `tmux=None` and no runtime),
        # so `claude`/`codex` is always the right binary answer here.
        runtime = "codex" if is_codex else "claude"
        # `is_idle_input` knows CLAUDE's prompt: an EMPTY `❯` between two rules. Codex's
        # prompt is a `›` line above its statusline (`… · Context N% left · …`), so it
        # needs its own STRUCTURAL detector (`is_codex_idle_input`) — NOT the coarse
        # "not busy". A Codex track is now a full citizen that gets the wrap-up pasted in
        # and is restarted on `ready`, so this gate is load-bearing: an over-loose idle
        # read would let a booting pane or a Codex approval/trust picker (`› 1.`) be
        # keystroked into. Structural idle keeps that impossible (a picker is a gate; a
        # blank/booting pane has no `›`+statusline shape → `settling`, re-read next tick).
        idle = signals.is_codex_idle_input(capture) if is_codex else signals.is_idle_input(capture)
        # Ctx% is runtime-agnostic: `parse_ctx_remaining` matches BOTH statuslines
        # (`Ctx: N% left` / `Context N% left`), so each runtime reports ITS OWN computed
        # number and there is no occupancy formula here to get wrong.
        current_ctx = signals.parse_ctx_remaining(capture)
        eff_ctx = self._effective_ctx(key, current_ctx)

        # Track the CONTINUOUS-idle episode for the keep-going nudge's minimum-duration gate
        # (`_IDLE_NUDGE_AFTER`). A session is "cleanly idle" only at an empty prompt AND not
        # busy (busy folds in Claude's registry `busy`/`shell`, which an idle-looking capture
        # misses — a sub-agent / background command is active work). The FIRST cleanly-idle
        # tick stamps `idle_since`; ANY non-idle tick clears it, so brief activity resets the
        # clock and only a genuinely long idle spell reaches the nudge.
        istate = self._inject.setdefault(key, _InjectState())
        if idle and not busy:
            if istate.idle_since is None:
                istate.idle_since = self.now()
        else:
            istate.idle_since = None

        stamp = registry.read_injection_stamp(repo, topic, self.stamp_path)

        # The ONE indicator file (`ready` / `blocked` / `winding-down`). A single file
        # with a VALUE — never two presence-markers, which could both exist and whose
        # precedence was incidental rather than designed (maintainer 2026-07-14).
        declared = signals.read_state(repo, topic)
        malformed = declared is not None and not signals.valid_token(declared.token)
        blocked = (
            declared.detail or "(no reason given)"
            if declared is not None and declared.token == signals.STATE_BLOCKED
            else None
        )
        acked = (
            declared is not None
            and declared.token == signals.STATE_WINDING_DOWN
            and (self.now() - declared.mtime) <= _ACK_STALE_AFTER
        )
        return _Observation(
            capture=capture,
            busy=busy,
            gate=gate,
            idle=idle,
            is_codex=is_codex,
            runtime=runtime,
            codex_fallback=codex_fallback,
            claude_status=claude_status,
            eff_ctx=eff_ctx,
            istate=istate,
            declared=declared,
            malformed=malformed,
            blocked=blocked,
            acked=acked,
            ready=signals.ready_valid(repo, topic, stamp),
        )

    def evaluate(  # noqa: C901,PLR0911,PLR0912,PLR0915 — see "On the size of this function"
        self, track: registry.Track, *, act: bool
    ) -> RowView:
        """Derive a track's status and (when ``act``) perform its side effects.

        ``act=False`` is the read-only path used by the ``list`` command: it
        captures the pane and reads markers but performs NO paste / respawn /
        stamp write. The daemon loop calls with ``act=True``.

        **On the size of this function.** What remains after :meth:`_observe` was
        split out is the DECISION CASCADE: an ordered sequence of guards, each of
        which either returns a row or falls through to the next. Its length is the
        number of distinct states a track can be in, and its ordering IS the
        design — the cardinal rule (never restart a session that has not declared
        itself ready) is enforced by which guard comes first, not by any single
        guard in isolation.

        Extracting the fact-gathering was a real seam and is done; it took the
        function from 106 statements / 38 branches / complexity 34 down to 83 / 33
        / 31. Going further would mean cutting the cascade itself into per-state
        helpers, which was considered and rejected (maintainer-declared
        2026-07-19): it would scatter the precedence order across call sites where
        no reader can check it in one pass, and precedence is exactly what a
        reviewer of this function needs to verify. The four complexity rules are
        therefore suppressed HERE, on this one function, rather than for the file
        or the folder — every other function in this module is still held to them.
        """
        if track.is_unassigned:
            return RowView(
                topic=track.topic, repo=track.repo, tmux=None, ctx=None, status="unassigned"
            )

        repo, topic = track.repo, track.topic
        session = self._session_of(track)
        key = _key(repo, topic)

        if not self.tmux.session_exists(session):
            # The mapped TMUX session is gone — but the work may not be. A Claude
            # session for the same plan can keep running in a NON-tmux terminal (a bare
            # SSH shell), which the tmux-only daemon cannot capture, inject, or respawn.
            # Distinguish that live-but-unmanageable case from a genuinely gone track so
            # the operator is not falsely alarmed that finished-looking work was lost.
            return self._no_managed_pane_row(repo=repo, topic=topic)

        # Resolve the pane id ONCE and target every subsequent pane op by it (RB3).
        # A pane id is exact and never prefix/fnmatch-matched, so if the tracked
        # session dies mid-tick the ops fail-soft instead of a bare `-t <name>`
        # falling back to a live SIBLING session (e.g. dead `livespec--overseer`
        # resolving to live `livespec--overseer-rewrite`) and, worst case,
        # `respawn-pane -k` killing it. Stable across respawn.
        target = self.tmux.pane_id(session)
        if target is None:
            return self._no_managed_pane_row(repo=repo, topic=topic)

        # Identity gate (B3): the mapped session exists, but before reading its pane
        # for any ACT we confirm it is really OUR Claude in OUR repo — never
        # keystroke into a shell / wrong session / human split-pane.
        if not self._pane_is_managed(target, repo, topic, session):
            # The gate stays exactly what it was — an ACT guard (never keystroke into a
            # pane not proven ours). What changed is that its answer is no longer a row
            # STATUS of its own. Whether the pane is a bare shell (our session exited) or
            # something foreign, the fact for the operator is identical and simple: this
            # track's session is NOT IN THIS TMUX. It was assigned to something once, so
            # it is `session-gone` — never `unassigned`, which is reserved for a plan
            # whose session we have NEVER seen (maintainer-declared 2026-07-17: "KEEP
            # session-gone if you've ever seen the session, only use unassigned if you've
            # never seen it"). The MAPPING ROW is precisely that memory of having seen it,
            # which is why it is kept rather than pruned.
            #
            # `not-claude` is DELETED (maintainer-declared 2026-07-17: "What the hell is
            # not-claude?"). It was this gate's return value leaking into the UI — it named
            # a check's output, not anything an operator needs — and it made a bare
            # terminal (`livespec1`) look like a tracked pane while no OTHER bare terminal
            # appears at all. The daemon lists PLANS, not panes: a tmux name reaches the
            # table only as a mapping's column value, and `_no_managed_pane_row` already
            # reports `tmux=None` so no dead terminal is named.
            return self._no_managed_pane_row(repo=repo, topic=topic)

        # Phase 1 — OBSERVE. Every fact the guard cascade below decides on is
        # gathered in one place, so the cascade reads as a single top-to-bottom
        # precedence order. Unpacked into locals so each guard reads the same way
        # it always has.
        obs = self._observe(track, session=session, target=target, key=key)
        capture, busy, gate, idle = obs.capture, obs.busy, obs.gate, obs.idle
        is_codex, runtime, codex_fallback = obs.is_codex, obs.runtime, obs.codex_fallback
        claude_status, eff_ctx, istate = obs.claude_status, obs.eff_ctx, obs.istate
        declared, malformed, blocked, acked, ready = (
            obs.declared,
            obs.malformed,
            obs.blocked,
            obs.acked,
            obs.ready,
        )

        # Phase 2 — DECIDE.

        # R1 — self-healing resume retry. A prior tick respawned the fresh Claude but its
        # resume line did not submit (the fresh TUI dropped the Enter, or the daemon died
        # mid-restart). The round is still open (marker + stamp kept), so `ready` is still
        # valid — but re-entering the `elif ready:` branch below would RE-RESPAWN and kill
        # the live fresh session. This branch intercepts first and retries the SUBMIT ONLY:
        # re-send Enter, never a respawn (a fresh `ready` is the sole respawn trigger,
        # invariant 7). It also runs BEFORE the busy/idle cascade because a box holding the
        # un-submitted resume text reads as "not idle" → would otherwise fall to `settling`
        # and never retry. Codex never sets `resume_pending` (its `codex resume` auto-submits
        # the kick), so this is Claude-only by construction.
        if act and registry.read_resume_pending(repo, topic, self.stamp_path):
            if gate:
                # A fresh TUI showing a picker (trust / update / bypass-permissions confirm):
                # NEVER keystroke into a gate (blocker #6). Report it and keep the round open;
                # the retry resumes once the human clears the gate (review SF4).
                self._alert(
                    repo=repo,
                    topic=topic,
                    session=session,
                    pane=target,
                    message="gate on freshly-restarted pane — answer it IN THAT PANE",
                )
                return RowView(
                    topic=topic,
                    repo=repo,
                    tmux=session,
                    ctx=eff_ctx,
                    status="blocked:human",
                    note="structured gate on freshly-restarted pane",
                    runtime=runtime,
                )
            # Branch on the BOX STATE, not on `busy` (review SF3): a freshly-respawned session
            # can read busy for reasons unrelated to the resume (SessionStart hooks), so a
            # top-level `busy` shortcut would false-close the round while the resume is still
            # un-submitted. An EMPTY box means the resume left the box (submitted / never
            # pasted) — the round is done here; the rare paste-failure re-engages via the
            # idle-with-context nudge, not a double-kick. A box holding TEXT means the Enter
            # was dropped — re-send Enter ONLY (never re-paste; the text is already there).
            resolved = True if signals.input_box_ready(capture) else self._resend_enter(target)
            if resolved:
                self._clear_state(track)
                self._log(f"restart resume submitted for {repo}::{topic} (pane {target})")
                return RowView(
                    topic=topic,
                    repo=repo,
                    tmux=session,
                    ctx=eff_ctx,
                    status="restarting",
                    runtime=runtime,
                )
            # Still un-submitted: keep the round open (retry again next tick) and report it.
            self._alert(
                repo=repo,
                topic=topic,
                session=session,
                pane=target,
                message=(
                    "resume line STILL not submitted after restart — "
                    "retrying the Enter (no respawn)"
                ),
            )
            return RowView(
                topic=topic,
                repo=repo,
                tmux=session,
                ctx=eff_ctx,
                status="restarting",
                note=_RESUME_PENDING_NOTE,
                runtime=runtime,
            )

        # A per-track override (an int ``ctx_threshold``) wins; otherwise inherit
        # the daemon-wide default (``warn_percent``, set from ``--warn-percent``).
        threshold = track.ctx_threshold if track.ctx_threshold is not None else self.warn_percent

        # The row note defaults to the blocked reason (if any); the busy branch
        # overrides it to "background shell" when a live background shell is the SOLE
        # reason the pane isn't idle, so the operator can see WHY.
        note: str | None = blocked if blocked else None
        if malformed and declared is not None:
            note = f"BAD state file: {declared.token!r}"
            if act:
                self._alert(
                    repo=repo,
                    topic=topic,
                    session=session,
                    pane=target,
                    message=(
                        f"MALFORMED state file: {declared.token!r} is not one of "
                        f"{', '.join(signals.STATE_TOKENS)} — treated as no declaration "
                        f"(the track will NOT be restarted)"
                    ),
                )

        # Precedence, top to bottom. Single-capture `busy` and the human gates
        # are checked first. For an apparently-idle track that would ACT
        # (restart / inject), the daemon first confirms the pane is SETTLED
        # (`_pane_settled`) — a single frame can't see active token-streaming, so
        # a changing pane is treated as `working` and skipped this tick.
        if busy:
            status = "working"
            if act:
                # A GENERATING session is not waiting on a human, so a `blocked:` it has
                # outlived is provably dead — retire it before the note is derived, or the
                # dead reason rides this row (it is the note default) and later fires a
                # false `blocked:human`. Busy via a BACKGROUND SHELL alone does NOT qualify:
                # that session is at its prompt and may genuinely still be waiting.
                blocked = self._void_stale_blocked(
                    track,
                    blocked,
                    generating=signals.is_busy(capture) or claude_status == "busy",
                )
                note = blocked if blocked else None  # re-derive: the default came from `blocked`
            # When the PANE itself looks idle, the row note explains WHY it is `working`,
            # or the operator would read the idle-looking pane and distrust the status.
            if not signals.is_busy(capture):
                if claude_status == "shell" or codex_fallback:
                    note = "background shell"  # a live `Bash(run_in_background)` command
                # Provably always True where it stands: reaching here needs `busy` True
                # with `is_busy(capture)` False and the `shell`/codex-fallback arm above
                # already excluded, which leaves `claude_busy` as the only disjunct that
                # can be carrying `busy` — and `_CLAUDE_BUSY_STATUSES` holds exactly
                # {"busy", "shell"}. So the else-exit is dead and branch coverage can
                # never close it.
                #
                # KEPT as an `elif` rather than demoted to `else` precisely because that
                # proof depends on the CURRENT contents of `_CLAUDE_BUSY_STATUSES`, which
                # exists to be extended. Add a third status and `else` would silently
                # label it "sub-agent (Claude busy)" — wrong; the `elif` correctly leaves
                # the note unset. The dead arc is the cost of that safety, so it is
                # annotated rather than removed.
                elif claude_status == "busy":  # pragma: no branch
                    note = "sub-agent (Claude busy)"  # in-process sub-agent, no shell
            if act:
                # Void the certification ONLY if it is past the grace — a young
                # marker is the certifying turn's own busy tail and must survive
                # (RB1); an old one means the session resumed work after certifying.
                ready = self._void_if_stale(track, ready=ready)
                # The session took a turn — clear any idle-with-context-left nudge marker
                # so the NEXT idle-with-context episode re-nudges (re-arm on non-idle).
                self._clear_idle_nudge_state(track)
        elif gate or blocked is not None:
            status = "blocked:human"
            if act:
                ready = self._void_if_stale(track, ready=ready)
                # A gate / block is also "non-idle" — drop a stale nudge marker (safe: the
                # helper re-reads and leaves a session-written `blocked` untouched).
                self._clear_idle_nudge_state(track)
                detail = blocked if blocked else "structured gate on pane"
                # The decision belongs to the TRACKED session, which is already showing
                # it in its own pane. The overseer NOTIFIES and hands over coordinates;
                # it never re-asks the question itself (invariant 8).
                self._alert(
                    repo=repo,
                    topic=topic,
                    session=session,
                    pane=target,
                    message=(
                        f"blocked on human: {_elide(detail, _MAX_REASON_IN_ALERT)} "
                        "— answer it IN THAT PANE"
                    ),
                )
        elif not idle:
            # Pane present but not a verified idle-input state and not busy —
            # a transient/settling capture. Wait; never act.
            status = "settling"
        elif act and not self._pane_settled(target):
            # One frame looks idle, but the pane is actively changing (streaming).
            status = "working"
        elif act and not self._pane_is_managed(target, repo, topic, session):
            # TOCTOU re-check (Codex re-review #1): the identity gate ran at the top
            # of the tick, but capturing + the settle delay opened a window in which
            # the pane could have exited to a shell (or cd'd out of the repo). Re-
            # verify identity IMMEDIATELY before any act, so a wrap-up is never
            # pasted into — nor a respawn aimed at — a pane no longer proven ours.
            #
            # `settling` (a one-tick "wait and re-read"), NOT a status of its own: the
            # pane changed UNDER US mid-tick, which is exactly what settling means. The
            # act is suppressed either way, and the next tick re-enters at the top gate,
            # which classifies the settled truth (`session-gone` if it really has gone).
            status = "settling"
        elif ready:
            # The session DECLARED `ready`. This is the ONLY path to a restart — the
            # daemon never infers it (maintainer 2026-07-14). RUNTIME-DISPATCHED: for a
            # Codex track `_do_restart` routes to `codex resume <id>`, NEVER the claude
            # launch command — aiming `claude -n <topic>` at a codex pane would REPLACE
            # the codex session with a claude one and destroy it. That routing (not a
            # separate monitor-only refusal) is what preserves the one place a bug here is
            # destructive rather than merely wrong; the sabotage-verified guard test pins
            # it. A Codex track is now a full citizen (maintainer-declared 2026-07-17):
            # it is restarted on its own `ready` exactly like a Claude one.
            status = "restarting"
            if act:
                self._do_restart(track, target, is_codex=is_codex)
        elif eff_ctx is not None and eff_ctx <= threshold:
            # A FRESH `winding-down` ACK buys patience: the session heard us and is
            # wrapping up, so stop re-warning (never keystroke into a session that is
            # actively winding down). A STALE ACK resumes escalating — an ACK must not
            # become an infinite stall — but still never authorizes an act.
            if act and not acked:
                self._maybe_inject(track, target, eff_ctx, threshold, is_codex=is_codex)
            if acked:
                status = "winding-down"
            elif eff_ctx <= DANGER_CTX_REMAINING:
                status = "danger"
                if act:
                    self._alert_non_responder(
                        repo=repo,
                        topic=topic,
                        session=session,
                        pane=target,
                        eff_ctx=eff_ctx,
                        declared=declared,
                    )
            else:
                status = "warned"
        else:
            # Idle at an empty prompt with the context ABOVE the wind-down threshold. If
            # the session has declared nothing, nudge it ONCE this episode to keep going
            # rather than stop early (the inverse of the wrap-up). The daemon-written
            # `idle-with-context-left` marker makes it single-prompt; it clears when the
            # session next goes non-idle, re-arming a fresh nudge for the next episode.
            nudged_already = (
                declared is not None and declared.token == signals.STATE_IDLE_WITH_CONTEXT_LEFT
            )
            has_context_left = eff_ctx is not None and eff_ctx > threshold
            # Claude's own `waiting` = at a gate/prompt for the human. Even when no
            # structured gate is visible in the capture (it scrolled, or it is a prose
            # question a YOLO session cannot raise as a prompt), that IS "a blocking
            # question for the human" — so it must NOT be nudged to keep going.
            waiting_on_human = claude_status == "waiting"
            # `eff_ctx is not None` is spelled out here as well as inside
            # `has_context_left` so the type checker can narrow it for the
            # `_nudge_idle_with_context` call below. It is not redundant to a reader
            # either: a nudge needs a KNOWN remaining-context percentage to quote.
            if (
                eff_ctx is not None
                and has_context_left
                and not waiting_on_human
                and (declared is None or nudged_already)
            ):
                status = "idle-with-context-left"
                # Fire the nudge ONLY after the session has been continuously idle for at
                # least `_IDLE_NUDGE_AFTER` (maintainer 2026-07-18: the nudge was "too
                # aggressive, TOO SOON", interrupting sessions merely between turns). The
                # status still reads `idle-with-context-left` immediately (it is descriptive,
                # not an attention row); only the keystroke waits for the 1-hour floor.
                idle_long_enough = (
                    istate.idle_since is not None
                    and (self.now() - istate.idle_since) >= _IDLE_NUDGE_AFTER
                )
                if act and not nudged_already and idle_long_enough:
                    self._nudge_idle_with_context(
                        track, target, eff_ctx, threshold, is_codex=is_codex
                    )
            else:
                status = "idle"

        view = RowView(
            topic=topic,
            repo=repo,
            tmux=session,
            ctx=eff_ctx,
            status=status,
            note=note,
            runtime=runtime,
        )
        # Re-arm the edge-triggered alert once the track is healthy again, so the NEXT
        # time it goes bad it reports afresh rather than being suppressed as a duplicate
        # of the condition it was in hours ago.
        if act and not needs_attention(view):
            _ = self._alerted.pop(key, None)
        return view

    def _alert_non_responder(
        self,
        *,
        repo: str,
        topic: str,
        session: str,
        pane: str,
        eff_ctx: int,
        declared: signals.TrackState | None,
    ) -> None:
        """Report a track deep in the danger band that is not honouring the protocol.

        This is the WHOLE response to such a session: the daemon SAYS SO, loudly, with
        the coordinates to go fix it — and does nothing else. It does NOT restart it
        (maintainer 2026-07-14: "NEVER forcibly restart a session that is not ready; it
        MUST drop the indicator file for action"), because a timer cannot know whether a
        session is safe to kill.

        Two ways to get here, and the report must not conflate them (they need different
        fixes):

        - **declared nothing at all** — the session ignored an escalating wrap-up (once
          per 10% band, insistent from 30%) telling it to ACK immediately. A session bug.
        - **a STALE ``winding-down``** — it DID acknowledge, then never finished; the ACK
          aged out of ``_ACK_STALE_AFTER``. It is hung mid-wrap-up, not deaf.

        Either way this is a DEFECT REPORT about that session, not a chore for the
        operator to work around: the fix is to make the session honour the protocol,
        never to have the overseer guess on its behalf.
        """
        if declared is not None and declared.token == signals.STATE_WINDING_DOWN:
            age = self.now() - declared.mtime
            what = (
                f"ACKNOWLEDGED the wrap-up {age:.0f}s ago but never finished "
                f"(stale `{signals.STATE_WINDING_DOWN}`; it is hung mid-wrap-up)"
            )
        else:
            what = (
                f"has declared NOTHING (no {signals.state_path(repo, topic).name}) — "
                f"it is ignoring the wrap-up protocol"
            )
        self._alert(
            repo=repo,
            topic=topic,
            session=session,
            pane=pane,
            message=(
                f"NOT RESPONDING — ctx {eff_ctx}% left and it {what}. The overseer will "
                f"NOT restart it: only the session may authorize that. A human must act."
            ),
        )

    def _maybe_inject(
        self,
        track: registry.Track,
        target: str,
        eff_ctx: int,
        threshold: int,
        *,
        is_codex: bool = False,
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

        ``is_codex`` selects the runtime-appropriate submit verification — this is the
        change that makes the escalating wrap-up (the daemon's ONLY lever now that
        nothing is force-killed) reach a Codex track, not just a Claude one.
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
        if self._submit_prompt(target, message, expect_codex=is_codex):
            for b in due:
                registry.add_notified_band(repo, topic, b, self.stamp_path)
            self._log(f"injected wrap-up into {repo}::{topic} (ctx {eff_ctx}%, bands {due})")
        else:
            if opened_now:
                # Roll back the just-opened round so the next tick retries cleanly.
                registry.clear_injection_stamp(repo, topic, self.stamp_path)
            self._alert(
                repo=repo,
                topic=topic,
                session=self._session_of(track),
                pane=target,
                message="wrap-up injection FAILED (paste did not land); will retry",
            )

    def _do_restart(self, track: registry.Track, target: str, *, is_codex: bool = False) -> None:
        """Atomic restart, RUNTIME-DISPATCHED: respawn → wait for the TUI → resume → close.

        ``target`` is the resolved pane id (RB3), STABLE across the respawn.

        There is exactly ONE caller and exactly one authorization: the session itself
        declared ``ready`` in its state file (``signals.ready_valid``). The daemon has
        no other path to a restart — it never decides a session is done (maintainer
        2026-07-14). The abrupt ``respawn-pane -k`` is safe precisely BECAUSE of that
        declaration: the session asserted it is at a clean stopping point.

        **The one destructive bug this daemon can have** is aiming the CLAUDE launch
        command at a Codex pane — it would REPLACE the codex session with a claude one.
        ``is_codex`` routes a Codex track to :meth:`_do_codex_restart` (``codex resume``)
        so the claude command is never issued to a codex pane; the sabotage-verified
        guard test (``…never issues the claude command``) pins that the routing holds.

        Every tmux step is a HARD GATE (B5). If ``respawn-pane`` fails, or the pane
        never becomes a live Claude, the daemon SURFACES the failure and RETURNS
        WITHOUT closing the round — so the session's declaration is preserved and the
        restart is retried, never silently destroyed.

        **The submit is SELF-HEALING (R1, 2026-07-18).** The round is closed (state file
        deleted + injection stamp cleared — B4) ONLY when the resume line actually SUBMITS.
        A freshly-respawned TUI can DROP the Enter while still drawing its welcome screen,
        leaving the fresh session live but idle with an un-run handoff (proven live
        2026-07-17). On that failure this does NOT clear the marker or log "restarted" —
        it marks a round-scoped ``resume_pending`` (``registry.set_resume_pending``) and
        alerts, and the NEXT tick's ``evaluate`` retries the SUBMIT ONLY (``_resend_enter``
        — never a re-respawn; a fresh ``ready`` stays the sole respawn trigger, so the retry
        can never escalate to a kill). Separating "is the fresh Claude up?" from "did the
        resume submit?" is the fix for the discarded-marker bug where the old code cleared
        the marker and reported success regardless. On the SUCCESS path ``_clear_state``
        also pops the in-memory inject state (RB2), so the redundant explicit pop is
        belt-and-suspenders.
        """
        if is_codex:
            self._do_codex_restart(track, target)
            return
        if not self.tmux.respawn_pane(target, track.repo, self._launch_command(track)):
            self._alert(
                repo=track.repo,
                topic=track.topic,
                session=self._session_of(track),
                pane=target,
                message="restart respawn FAILED; keeping the ready declaration so it retries",
            )
            return
        if not self._await_pane(target, signals.pane_is_claude):
            self._alert(
                repo=track.repo,
                topic=track.topic,
                session=self._session_of(track),
                pane=target,
                message="respawned pane never became Claude; keeping the ready declaration",
            )
            return
        # Wait for the fresh TUI to finish its FIRST paint and render a ready (empty)
        # input box before pasting — a half-drawn welcome/news screen DROPS the Enter,
        # which is exactly what stranded resumes live (2026-07-17). Best-effort: if the
        # box never appears in time, proceed anyway and let the submit-retry below (and
        # the next tick's `resume_pending` retry) recover.
        _ = self._await_input_box(target)
        # If the fresh TUI came up on a picker (a trust / update / bypass-permissions
        # gate), NEVER keystroke into it (blocker #6) — pasting + Enter would auto-accept
        # its default. Defer to the `resume_pending` retry, which reports the gate as
        # `blocked:human` and resumes once the human clears it (review SF4).
        if signals.is_structured_gate(self.tmux.capture_pane(target)):
            registry.set_resume_pending(track.repo, track.topic, self.stamp_path)
            self._alert(
                repo=track.repo,
                topic=track.topic,
                session=self._session_of(track),
                pane=target,
                message="freshly-restarted pane is on a gate — not keystroking it; will retry",
            )
            return
        resume = track.resume or default_resume(track.repo, track.topic)
        if self._submit_prompt(target, resume):
            self._clear_state(track)
            _ = self._inject.pop(_key(track.repo, track.topic), None)
            self._log(f"restarted {track.repo}::{track.topic} (pane {target})")
            return
        # The fresh Claude IS up, but the resume line did not submit (the fresh TUI
        # dropped the Enter). Separate the two facts the old code conflated — "is the
        # fresh Claude up?" (yes) and "did the resume submit?" (no) — and DO NOT give up:
        # keep the `ready` marker + stamp, record a round-scoped `resume_pending`, and let
        # the NEXT tick retry the SUBMIT ONLY (re-send Enter, never a re-respawn — a fresh
        # `ready` is the sole respawn trigger, so the retry can never escalate to a kill).
        # Never log a clean "restarted" here; the alert is edge-triggered and persists (the
        # row stays NEEDS-YOU) until the resume actually submits.
        registry.set_resume_pending(track.repo, track.topic, self.stamp_path)
        self._alert(
            repo=track.repo,
            topic=track.topic,
            session=self._session_of(track),
            pane=target,
            message="resume line NOT submitted after restart — will retry the Enter (no respawn)",
        )

    def _do_codex_restart(self, track: registry.Track, target: str) -> None:
        """Atomic restart of a CODEX track: respawn with ``codex resume <id> "<kick>"``.

        The Codex analogue of the Claude restart, and SIMPLER (proven live 2026-07-17):
        ``codex resume`` takes the kick as an ARGUMENT and AUTO-SUBMITS it, so there is
        no separate resume-line paste and no fresh-TUI submit race. It resumes the SAME
        session by its exact UUID — codex appends to the same rollout, so the
        ``thread_name`` (hence adoptability) survives the restart by construction. Resume
        by UUID, never by name: "UUIDs take precedence", and a name could be ambiguous or
        drop to a picker.

        The session id comes from the live per-tick Codex map (``self._codex``), looked up
        by ``(tmux, topic)`` so a second codex sharing this tmux session cannot supply the
        WRONG session id (#4); if the session vanished between the map refresh and here,
        the declaration is KEPT and the restart retried next tick (B5), exactly like a
        failed respawn.
        """
        session = self._session_of(track)
        live = self._codex.get((session, track.topic))
        if live is None:
            self._alert(
                repo=track.repo,
                topic=track.topic,
                session=session,
                pane=target,
                message="codex session vanished before restart; keeping the ready declaration",
            )
            return
        resume = track.resume or default_resume(track.repo, track.topic)
        command = self._codex_launch_command(live.session_id, resume)
        if not self.tmux.respawn_pane(target, track.repo, command):
            self._alert(
                repo=track.repo,
                topic=track.topic,
                session=session,
                pane=target,
                message="restart respawn FAILED; keeping the ready declaration so it retries",
            )
            return
        if not self._await_pane(target, signals.pane_is_codex):
            self._alert(
                repo=track.repo,
                topic=track.topic,
                session=session,
                pane=target,
                message="respawned pane never became Codex; keeping the ready declaration",
            )
            return
        # The kick was submitted BY the `codex resume` argument — no separate paste step.
        self._clear_state(track)
        _ = self._inject.pop(_key(track.repo, track.topic), None)
        self._log(f"restarted (codex) {track.repo}::{track.topic} (pane {target})")

    @staticmethod
    def _launch_command(track: registry.Track) -> str:
        """The Claude (re)start command: ``claude --dangerously-skip-permissions -n <topic>``.

        ``--dangerously-skip-permissions`` is REQUIRED (maintainer 2026-07-14): a
        (re)started track must resume AUTONOMOUSLY. Without it the fresh session
        stalls on the first permission prompt and the whole point of the
        auto-restart — an unattended, hands-off resume — is lost. ``-n <topic>``
        (topic shell-quoted, defensive) sets the session's display name; the resume
        line (read the handoff) is pasted AFTER launch, since a ``claude "<prompt>"``
        argv only pre-fills without submitting.

        The command deliberately carries NO tmux env scoping — no ``unset TMUX``,
        no ``TMUX_TMPDIR`` export. The former L1 env inversion (an agent-private
        socket namespace prefixed onto every spawn) was REMOVED by
        ``plan/tmux-fleet-visibility/``: it blinded every spawned agent to the real
        fleet (producing false session-liveness claims) while failing open whenever
        its tmpfs-backed directory vanished, and the L2 ``PreToolUse`` command
        guards are the layer that actually distinguishes a listing from a teardown.
        A bare ``tmux ls`` in a spawned agent MUST tell the truth; do not re-add a
        scoping prefix here.

        This is the Claude-ONLY command — it must NEVER be aimed at a codex pane (it would
        destroy the session). ``_do_restart`` dispatches a Codex track to
        :meth:`_codex_launch_command` instead.
        """
        return f"claude --dangerously-skip-permissions -n {shlex.quote(track.topic)}"

    @staticmethod
    def _codex_launch_command(session_id: str, resume: str) -> str:
        """The Codex (re)start command:
        ``codex resume --dangerously-bypass-approvals-and-sandbox <session-id> "<resume>"``.

        ``--dangerously-bypass-approvals-and-sandbox`` is the codex twin of the Claude
        path's REQUIRED ``--dangerously-skip-permissions`` (maintainer-declared 2026-07-17):
        without it the resumed session uses codex's default INTERACTIVE approval policy and
        stalls at a ``› 1.`` approval picker on its first tool call — the daemon would
        (correctly) report `blocked:human` and the "auto-restart" would not be hands-off.
        Codex documents the flag as "intended solely for environments that are externally
        sandboxed", which this local-only overseer host is (the whole fleet already runs
        `claude --dangerously-skip-permissions`).

        Resume by the exact UUID (never the name — "UUIDs take precedence" and a name can
        be ambiguous / drop to a picker), which reattaches the SAME rollout so the
        ``thread_name`` survives (adoptability). The resume line is the kick and is passed
        as the PROMPT argument, which Codex auto-submits (verified live 2026-07-17) — so
        unlike the Claude path there is no separate paste. Fields are shell-quoted; the
        flag precedes the positional ``SESSION_ID``/``PROMPT`` per ``codex resume``'s usage.

        Like :meth:`_launch_command`, this carries NO tmux env scoping — the L1
        env inversion was removed by ``plan/tmux-fleet-visibility/`` (see that
        method's docstring); do not re-add a scoping prefix here.
        """
        return (
            "codex resume --dangerously-bypass-approvals-and-sandbox "
            f"{shlex.quote(session_id)} {shlex.quote(resume)}"
        )

    def _await_pane(self, target: str, is_ready: Callable[[str | None], bool]) -> bool:
        """Poll ``#{pane_current_command}`` until ``is_ready(cmd)``, bounded.

        ``target`` is the resolved pane id. Never scrape the ``❯``/``›`` prompt glyph
        (ambiguous shell/TUI); wait on the process identity (design). ``is_ready`` is the
        runtime predicate — :func:`signals.pane_is_claude` for a Claude restart,
        :func:`signals.pane_is_codex` for a Codex one. Returns False if it never became
        that runtime.
        """
        for _ in range(_RESTART_POLL_MAX):
            if is_ready(self.tmux.pane_current_command(target)):
                return True
            self.sleep(_RESTART_POLL_INTERVAL)
        return False

    def _await_input_box(self, target: str) -> bool:
        """Poll until the pane renders a ready (empty) Claude input box, bounded.

        Used right after a respawn, BEFORE pasting the resume line: a freshly-respawned
        Claude is often still drawing its welcome/news screen, and a paste + Enter that
        arrives then is dropped (the stranded-resume failure). Waiting for the empty `❯`
        box (`signals.input_box_ready`) means the TUI has finished its first paint and is
        ready to accept input. Best-effort — returns True if the box appeared, False if it
        never did within the bound; the caller proceeds either way (the submit-verify loop
        and the next-tick `resume_pending` retry recover a residual drop).
        """
        for _ in range(_RESTART_POLL_MAX):
            if signals.input_box_ready(self.tmux.capture_pane(target)):
                return True
            self.sleep(_RESTART_POLL_INTERVAL)
        return False

    def _resend_enter(self, target: str) -> bool:
        """Re-send Enter (NEVER re-paste, NEVER re-respawn) until the resume submits.

        The retry half of the self-healing resume (R1): the resume line is ALREADY sitting
        in the box from the prior respawn, so re-pasting would duplicate it — this only
        re-sends Enter, bounded by `_SUBMIT_MAX_ENTERS`. Submitted is confirmed by the Claude
        box CLEARING (`signals.input_box_ready`) — the same signal `_submit_prompt` uses on
        the Claude path — NOT by the pane going busy: a freshly-respawned session can be busy
        for reasons unrelated to the resume (SessionStart hooks), so a busy check would
        false-confirm an un-submitted resume (review SF3). An extra Enter on an already-empty
        prompt is a harmless no-op.
        """
        for _ in range(_SUBMIT_MAX_ENTERS):
            _ = self.tmux.send_keys(target, "Enter")
            self.sleep(_SUBMIT_POLL)
            if signals.input_box_ready(self.tmux.capture_pane(target)):
                return True
        return False

    def _submit_prompt(self, target: str, text: str, *, expect_codex: bool = False) -> bool:
        """Bracketed-paste a payload, then submit it — re-sending Enter until it lands.
        Returns True iff the paste LANDED and the submit is CONFIRMED. ``target`` is the
        resolved pane id (RB3).

        The paste is atomic (never fragments — blocker #2). A SINGLE Enter is
        enough on a steady idle session, but a freshly-`respawn`-ed session is
        often still drawing its welcome/news screen when the Enter arrives, and
        that first Enter is dropped — leaving the resume line un-submitted and the
        auto-restart stalled (verified live 2026-07-13). So we verify after each Enter
        and re-send up to `_SUBMIT_MAX_ENTERS` times; an extra Enter on an already-empty
        prompt is a harmless no-op (neither TUI submits an empty message).

        The confirm signal is RUNTIME-SPECIFIC because the two TUIs render differently:

        - **Claude** — the empty `❯` box returns (`signals.input_box_ready`, which does
          NOT require not-busy, so a now-working pane also reads submitted).
        - **Codex** (`expect_codex`) — the pane goes BUSY (`signals.is_busy` matches
          Codex's `esc to interrupt` / `Working …`). Codex has no `❯` box and its empty
          box shows a grey rotating PLACEHOLDER indistinguishable from typed text in an
          ANSI-stripped capture, so "box cleared" is not a usable signal; "the model
          started responding" is (verified live 2026-07-17 — busy within ~1s of Enter).
          Caveat (adversarial review 2026-07-17): the Codex confirm reads `is_busy` over
          the whole capture, so a payload the daemon PASTES must not itself contain a
          busy-marker substring (`esc to interrupt`, `· Ns ·`, `↓ N tokens`, `(running`),
          or an UNSUBMITTED payload sitting in the composer would false-read as submitted.
          The current wrap-up / nudge / resume texts are all clear of these; keep them so.

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
            _ = self.tmux.send_keys(target, "Enter")
            self.sleep(_SUBMIT_POLL)
            capture = self.tmux.capture_pane(target)
            submitted = (
                signals.is_busy(capture) if expect_codex else signals.input_box_ready(capture)
            )
            if submitted:
                return True
        return False

    # ----------------------------------------------------------------- #
    # Reboot recovery (startup-only, never per-tick).
    # ----------------------------------------------------------------- #

    def recover_missing_sessions(self) -> list[str]:
        """Recreate any mapped session that is not currently live (design).

        Run ONCE at daemon startup: a fresh overseer reads the mapping, and for
        each row whose mapped session (``_session_of``: the row's stored ``tmux``, or
        the derived bare-topic / collision name) is gone, recreates it. Not a
        per-tick action (a session the user deliberately kills should not be revived
        every 10s). Returns the recovered names.

        RUNTIME-DISPATCHED (defect #5, 2026-07-18). A dead codex process is absent from the
        live ``self._codex`` map (there is no rollout fd at cold start), so the runtime is
        derived from the PERSISTENT codex index instead — which SURVIVES the session's death.
        If the track's TOPIC names a session in ``session_index.jsonl``
        (:func:`codex_sessions.latest_session_for_thread_name`), the track is CODEX and is
        recovered by :meth:`_recover_codex_track` — ``codex resume <id>`` reattaches the SAME
        rollout (option c) when it still exists on disk, else a skip+surface (option b), NEVER
        a mis-recreation as Claude. Otherwise the track is Claude and is recreated with
        ``claude --dangerously-skip-permissions -n <topic>`` (:meth:`_launch_command`) + a
        resume-line paste. Either way the ``session_exists`` gate means only a genuinely
        ABSENT session is recreated, so no live session is ever killed.
        """
        recovered: list[str] = []
        for track in registry.read_mapping(self.store_path):
            session = self._session_of(track)
            if self.tmux.session_exists(session):
                continue
            # Runtime dispatch: a topic named in the persistent codex index is a CODEX track.
            # The index survives the session's death, so it is the ONLY runtime signal at cold
            # start. `_recover_codex_track` resumes the same rollout (option c) or skips+surfaces
            # (option b) — it NEVER falls through to the Claude path below (rollout-orphaning).
            codex_id = codex_sessions.latest_session_for_thread_name(
                track.topic, codex_home=self.codex_home
            )
            if codex_id is not None:
                name = self._recover_codex_track(track, session, codex_id)
                if name is not None:
                    recovered.append(name)
                continue
            _ = self.tmux.new_session(session, track.repo)
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

    def _recover_codex_track(
        self, track: registry.Track, session: str, session_id: str
    ) -> str | None:
        """Reboot-recover a CODEX track (defect #5): resume the SAME rollout, or skip+surface.

        **Option (c) — resume.** If the session's rollout still exists on disk
        (:func:`codex_sessions.rollout_exists`), create the tmux session and respawn it with
        ``codex resume --dangerously-bypass-approvals-and-sandbox <id> "<kick>"``
        (:meth:`_do_codex_launch`). ``codex resume`` reattaches the SAME conversation and
        preserves its ``thread_name``, so the daemon re-adopts the track on the next tick —
        parity-or-better continuity vs. the Claude path's fresh-session-plus-handoff (verified
        live 2026-07-18: a 26-day-old session reattached, thread_name intact, and — because the
        respawn cwd is ``track.repo``, matching the session's recorded cwd — with no working-dir
        picker).

        **Option (b) — skip + surface.** If the rollout is GONE, ``codex resume`` cannot
        reattach, so recovery SKIPS the track and surfaces it for the operator, NEVER
        mis-recreating it as Claude (which would orphan the rollout). A relaunched codex is
        re-adopted automatically.

        Returns the recovered session name, or None on skip/failure (mirroring the Claude
        path's ``session_exists``/launch gates).
        """
        if not codex_sessions.rollout_exists(session_id, codex_home=self.codex_home):
            self._surface(
                f"reboot-recovery: codex track {track.repo}::{track.topic} was down at boot and "
                f"its rollout is gone (session {session_id}); relaunch it and it will re-adopt"
            )
            return None
        _ = self.tmux.new_session(session, track.repo)
        if not self.tmux.session_exists(session):
            self._surface(
                f"reboot-recovery: new-session did not create {session} "
                f"for {track.repo}::{track.topic}; skipping"
            )
            return None
        if self._do_codex_launch(track, session, session_id):
            self._log(
                f"reboot-recovery resumed codex {session} for {track.repo}::{track.topic} "
                f"(session {session_id})"
            )
            return session
        self._surface(
            f"reboot-recovery FAILED to resume codex {session} for {track.repo}::{track.topic}"
        )
        return None

    def _do_codex_launch(self, track: registry.Track, session: str, session_id: str) -> bool:
        """Respawn ``session`` with ``codex resume <id> "<kick>"`` and await a live codex pane.

        The codex twin of :meth:`_do_launch`, and SIMPLER: ``codex resume`` takes the kick as
        its PROMPT argument and AUTO-SUBMITS it (verified live 2026-07-17), so there is no
        separate resume-line paste. ``session`` is the just-created session NAME; the pane id
        is resolved from it and every pane op targets that id (RB3). The respawn cwd is
        ``track.repo`` — which matches the codex session's recorded cwd — so ``codex resume``
        reattaches directly. Returns True iff respawn succeeded and the pane became a live
        codex TUI (a failed respawn / non-codex pane surfaces via the caller).
        """
        target = self.tmux.pane_id(session)
        if target is None:
            return False
        resume = track.resume or default_resume(track.repo, track.topic)
        command = self._codex_launch_command(session_id, resume)
        if not self.tmux.respawn_pane(target, track.repo, command):
            return False
        return self._await_pane(target, signals.pane_is_codex)

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
        if not self._await_pane(target, signals.pane_is_claude):
            return False
        resume = track.resume or default_resume(track.repo, track.topic)
        return self._submit_prompt(target, resume)

    # ----------------------------------------------------------------- #
    # Table rendering.
    # ----------------------------------------------------------------- #

    def render(self, rows: Iterable[RowView]) -> None:
        """Clear the screen and print the live ``Status · Topic · tmux · Ctx% · Repo`` table.

        Re-rendered from live captures every tick, and stamped with the current
        wall-clock time, so a ``/clear``-orphaned pane can never freeze on a
        stale "all idle" snapshot (the second historical failure mode). Status leads
        (maintainer 2026-07-15): it is the column the operator scans first.

        Each data row is tinted by its status (``_row_color``) so the operator can
        scan the list by hue — green working, yellow idle/waiting, red broken. The
        color wraps the WHOLE padded line (never a cell), so alignment is untouched,
        and is emitted ONLY to a TTY (``out.isatty()``): piped ``list`` output and the
        beside-tests' ``StringIO`` stay plain. The header + separator stay uncolored.
        """
        rows = list(rows)
        lines: list[str] = []
        lines.append(f"overseer — {_iso_now()} — {len(rows)} track(s)")
        header = ("Status", "Topic", "tmux", "Ctx%", "Repo")
        table: list[tuple[str, ...]] = [header]
        for row in rows:
            # Elide the session-authored note so an over-long / multi-line value cannot
            # blow up the Status column width or break the row (the full note still
            # reaches the NEEDS YOU block below).
            note = _elide(row.note, _MAX_NOTE_IN_TABLE) if row.note else None
            table.append(
                (
                    row.status if not note else f"{row.status} ({note})",
                    row.topic,
                    # The tmux cell is the session name annotated with its runtime
                    # (`livespec (claude)`); the column width is computed below from THIS
                    # already-annotated string (the `max(len(...))` over `table`), so the
                    # column stays aligned — never widen it from the bare name.
                    _tmux_cell(row),
                    "—" if row.ctx is None else f"{row.ctx}%",
                    registry.repo_slug(row.repo),
                )
            )
        widths = [max(len(r[i]) for r in table) for i in range(len(header))]
        isatty = getattr(self.out, "isatty", None)
        use_color = bool(isatty) and isatty()
        for i, cells in enumerate(table):
            line = "  ".join(cell.ljust(widths[j]) for j, cell in enumerate(cells))
            if i == 0:
                lines.append(line)
                lines.append("  ".join("-" * widths[j] for j in range(len(header))))
                continue
            # table[i] for i >= 1 is the projection of rows[i - 1]; tint by its raw
            # status (not the note-decorated cell text).
            color = _row_color(rows[i - 1].status) if use_color else ""
            lines.append(f"{color}{line}{_ANSI_RESET}" if color else line)
        lines.extend(self._attention_lines(rows))
        # Clear scrollback + screen + home, then the table.
        _ = self.out.write("\x1b[3J\x1b[2J\x1b[H" + "\n".join(lines) + "\n")
        self.out.flush()

    def _attention_lines(self, rows: list[RowView]) -> list[str]:
        """The ``NEEDS YOU`` block: the rows a human must act on, and where to go.

        THIS is the answer to "what needs attention?", and it lives here — in the daemon's
        re-rendered table — for two reasons that the bottom pane cannot satisfy:

        - it inherits the tick's refresh, so a track the operator resolves DISAPPEARS from
          it on the next render (it can never go stale, which is the whole bug: an LLM
          pane prints text ONCE and that text then ages silently); and
        - it costs no tokens, so it can refresh forever.

        The table alone was not enough: dozens of `unassigned` rows buried the two that
        actually wanted the operator. This filters to exactly those, and carries the same
        jump command `_alert` does, so the block is a sufficient handover on its own.

        Each row's coordinates are LABELED (`topic: … | tmux: … | repo: …`) so the operator
        never has to guess which unlabeled token is which — a bare `autonomous-mode
        (livespec)` said WHAT but the tmux session (WHERE to go) had to be inferred from the
        jump line (maintainer 2026-07-14).
        """
        attention = [row for row in rows if needs_attention(row)]
        lines = [""]
        if not attention:
            lines.append("NEEDS YOU: nothing — every tracked session is healthy.")
            return lines
        lines.append(f"NEEDS YOU ({len(attention)}):")
        for row in attention:
            # Elide the note here too: a session can write an arbitrarily long `blocked:`
            # reason, and the full text lives in the pane this line points at.
            detail = f" — {_elide(row.note, _MAX_REASON_IN_ALERT)}" if row.note else ""
            # Annotate the tmux coordinate with the runtime the SAME way the table does
            # (`_tmux_cell`), so the operator knows whether they are jumping into a Claude
            # or a Codex pane before they do. The jump command itself stays the bare
            # session name (`tmux switch-client -t` takes no runtime).
            coords = (
                f"topic: {row.topic} | tmux: {_tmux_cell(row)} "
                f"| repo: {registry.repo_slug(row.repo)}"
            )
            lines.append(f"  ! {coords} — {row.status}{detail}")
            if row.tmux:
                lines.append(f"      jump: tmux switch-client -t {row.tmux}")
        return lines

    def _refresh_window_name(self, attention: int) -> None:
        """Badge the attention count onto the tmux WINDOW name (``overseer`` → ``overseer(2!)``).

        The only overseer surface visible WITHOUT looking at the overseer window: tmux
        renders the window name in the status bar of whatever session the operator is
        currently attached to. So a track that wants them is noticed while they are heads-
        down in a different session — no pane switch, no polling, no tokens.

        Only written when the count CHANGES, and a no-op when the daemon is not in tmux
        (``own_pane`` unset).
        """
        pane = self.own_pane
        if not pane:
            return
        name = f"{WINDOW_NAME}({attention}!)" if attention else WINDOW_NAME
        if name == self._window_name:
            return
        if self.tmux.rename_window(pane, name):
            self._window_name = name

    # ----------------------------------------------------------------- #
    # Tick + loop.
    # ----------------------------------------------------------------- #

    def tick(self, *, act: bool = True) -> list[RowView]:
        """One loop iteration: build rows, evaluate each, render the table + attention block."""
        views = [self.evaluate(track, act=act) for track in self.build_rows(act=act)]
        self.render(views)
        # Only the DAEMON badges the window. `list` is advertised read-only, so it must
        # not rename the maintainer's window as a side effect of printing a table.
        if act:
            self._refresh_window_name(sum(1 for view in views if needs_attention(view)))
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

    def unsupported_host_reasons(self) -> list[str]:
        """Declared host preconditions that are ABSENT here (empty list == supported).

        Linux + tmux is a DECLARED REQUIREMENT rather than an abstraction boundary,
        so the honest failure is an immediate refusal naming what is missing — not a
        `FileNotFoundError` surfacing several ticks deep, from whichever reader
        happened to touch the host first. Two things are checked because two things
        are genuinely required: `/proc` (the Claude and Codex session readers both
        parse `/proc/<pid>/…`, and macOS has no `/proc` at all — absent, not merely
        different), and a real `tmux` on PATH (every acting mechanic shells out to
        it).
        """
        reasons: list[str] = []
        if not Path(self.proc_root).is_dir():
            reasons.append(
                f"{os.fspath(self.proc_root)} is not a directory — the session readers "
                "parse /proc/<pid>/ and macOS has no /proc at all (Linux is required)"
            )
        if self.which("tmux") is None:
            reasons.append("tmux is not on PATH — every acting mechanic drives a real tmux")
        return reasons

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
        unsupported = self.unsupported_host_reasons()
        if unsupported:
            self._surface(
                "refusing to start: unsupported host — "
                + "; ".join(unsupported)
                + " (the overseer declares Linux + tmux as a REQUIREMENT and "
                "deliberately does not abstract the host boundary)"
            )
            return
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
                _ = self.recover_missing_sessions()
            while True:
                try:
                    _ = self.tick(act=True)
                except KeyboardInterrupt:
                    self._log("interrupted; exiting")
                    return
                # The daemon's per-iteration resilience catch: a bug in one track's
                # tick must not take the whole daemon down and strand every OTHER
                # track it is supervising, so the traceback is logged in FULL and the
                # loop continues to the next tick. It never exits — that is what
                # makes it a loop-iteration catch rather than a supervisor boundary.
                # The marker wording is one of the five standardized forms; `sole`
                # here scopes to this supervision loop.
                except Exception:  # noqa: BLE001 — sole loop-iteration bug-catcher: log traceback, continue
                    self._log("tick error (continuing):\n" + traceback.format_exc())
                if once:
                    return
                self.sleep(interval)
        finally:
            self._release_singleton_lock(lock)


# --------------------------------------------------------------------------- #
# CLI. The daemon NEVER calls `start` — launching a session is surface-only.
# --------------------------------------------------------------------------- #


def _build_supervisor() -> Supervisor:
    """Build the daemon's ``Supervisor`` for the CLI — with NO tunable surface.

    The invocation surface carries no watch-set / store / stamp knobs (they were
    de-gold-plated 2026-07-13): the watch-set is declared in ``$HOME``
    (``~/.livespec-overseer-repos.json``), and the mapping store + the
    injection-stamp sidecar are the hard-coded ``registry`` defaults
    (``~/.livespec-overseer.jsonl`` / ``~/.livespec-overseer-stamps.json``). The
    ``Supervisor`` dataclass keeps ``store_path`` / ``stamp_path`` / ``watch_repos``
    injectable, but ONLY the beside-tests inject them — never the CLI.

    ``own_pane`` is read from the environment rather than passed: ``overseerd`` runs
    INSIDE the daemon pane, so tmux has already exported that pane's id as ``$TMUX_PANE``.
    It is used only to badge the attention count onto the window name, so when it is
    absent (not under tmux) the badge simply never fires.
    """
    return Supervisor(
        watch_set_path=registry.DEFAULT_WATCH_SET_PATH,
        own_pane=os.environ.get("TMUX_PANE"),
    )


def _cli_colliding() -> frozenset[str]:
    """Cross-repo topic-collision set for one-shot CLI naming (``add`` / ``start``).

    Reads the SAME watch-set the daemon uses (the ``$HOME`` declaration at
    ``~/.livespec-overseer-repos.json``) and computes :func:`registry.colliding_topics`
    over its discovery, so a CLI-created session is named EXACTLY as the daemon would
    name it: the bare plan topic, or ``<slug>-<topic>`` only when the topic collides
    across repos.
    """
    watch = registry.watch_set_from_config(registry.DEFAULT_WATCH_SET_PATH, [])
    return registry.colliding_topics(registry.discover_plans(watch))


def _upsert(track: registry.Track) -> None:
    """Replace any existing (repo, topic) mapping row in the hard-coded store, then
    append (one row each)."""
    _ = registry.remove_mapping(track.repo, track.topic, None)
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


def _cmd_list(_args: argparse.Namespace) -> int:
    sup = _build_supervisor()
    _ = sup.tick(act=False)  # read-only render: no injection/restart
    return 0


def _cmd_adopt(_args: argparse.Namespace) -> int:
    adopted = _build_supervisor().adopt_sessions()
    for track in adopted:
        streams.write_stdout(text=f"adopted {track.tmux} → {track.repo}::{track.topic}\n")
    streams.write_stdout(text=f"adopted {len(adopted)} existing session(s)\n")
    return 0


def _cmd_add(args: argparse.Namespace) -> int:
    repo = os.path.normpath(args.repo)
    track = registry.Track(
        topic=args.topic,
        repo=repo,
        tmux=registry.tmux_id(repo, args.topic, _cli_colliding()),
        handoff=default_handoff(repo, args.topic),
        resume=default_resume(repo, args.topic),
    )
    _upsert(track)
    streams.write_stdout(text=f"added mapping {repo}::{args.topic} (tmux {track.tmux})\n")
    return 0


def _cmd_remove(args: argparse.Namespace) -> int:
    removed = registry.remove_mapping(os.path.normpath(args.repo), args.topic, None)
    streams.write_stdout(text=f"removed {removed} mapping row(s) for {args.repo}::{args.topic}\n")
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
    session = registry.tmux_id(repo, topic, _cli_colliding())
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
        # POSITIVELY know it is DEAD. Only a bare SHELL proves that — a dead session
        # reports its shell name positively, so demanding proof costs nothing, while an
        # unreadable `pane_current_command` (None) or ANY other program might be live
        # work mid-flight.
        #
        # This asks "is it proven dead?", NOT "is it a live Claude?" (adversarial review,
        # probe-proven, 2026-07-17). The old test was `cmd is None or pane_is_claude(cmd)`,
        # which knew only ONE runtime: a live CODEX pane reports `bun`, failed the
        # Claude test, and was treated exactly like a dead shell — so a bare `start`
        # respawn-KILLED a live Codex TUI and replaced it with a claude one. The guard's
        # own stated purpose was already "fail closed on anything unproven-dead"; it just
        # enumerated the live runtimes instead of the dead one, which does not scale to a
        # second runtime and never did.
        cmd = io.pane_current_command(session)
        if not signals.pane_is_shell(cmd):
            _upsert(track)
            streams.write_stdout(
                text=(
                    f"{repo}::{topic}: session {session} already running (or its identity is "
                    f"unreadable) — mapping upserted, NOT respawned. Pass --force to respawn "
                    f"(kills the running session).\n"
                )
            )
            return 0
    if not io.session_exists(session):
        _ = io.new_session(session, repo)
        # Require the EXACT session to exist before launching (Codex re-review #3):
        # a failed `new-session` must not let `_do_launch` respawn a prefix-matched
        # sibling.
        if not io.session_exists(session):
            streams.write_stderr(
                text=(
                    f"start FAILED: could not create tmux session {session} "
                    f"for {repo}::{topic}\n"
                )
            )
            return 1
    # The SLF001 escape below: `_do_launch` is private to callers OUTSIDE this
    # module. This is the module's own CLI entry driving the Supervisor it just
    # built, and the underscore keeps the method's naming symmetry with its sibling
    # `_do_codex_launch`; promoting one of the pair and not the other would be worse
    # than this single documented access.
    if not sup._do_launch(track, session):  # noqa: SLF001 — same-module CLI entry
        streams.write_stderr(
            text=f"start FAILED to launch {repo}::{topic} in tmux session {session}\n"
        )
        return 1
    _upsert(track)
    streams.write_stdout(text=f"started {repo}::{topic} in tmux session {session}\n")
    return 0


def _add_track_args(parser: argparse.ArgumentParser) -> None:
    """The shared ``--repo`` / ``--topic`` keyword flags for the track subcommands.

    Keyword (not positional) so the ``/overseer`` skill is the operator surface:
    it prompts for whichever is omitted and passes both. Required here so a stray
    bare invocation fails loudly rather than acting on a half-specified track.
    """
    _ = parser.add_argument("--repo", required=True, help="repo checkout path the plan lives in")
    _ = parser.add_argument(
        "--topic", required=True, help="plan topic (the plan/<topic>/ dir name)"
    )


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
    _ = p_start.add_argument(
        "--force",
        action="store_true",
        help="respawn even if the session already runs a live Claude (kills it)",
    )
    p_start.set_defaults(func=_cmd_start)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
