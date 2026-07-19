"""tmuxio.py — the ONE module that shells out to tmux.

Stdlib-only, host-only (see ``registry.py`` header for the folder's gate
status). Every other overseer module
(``registry.py``, ``signals.py``) is pure; this is the single subprocess
boundary so the daemon can be unit-tested against a *fake* tmux with no real
tmux running.

Design invariants honored here (see ``design.md``):

  - **``command tmux`` semantics.** We invoke the ``tmux`` binary through
    ``subprocess.run`` with an argv LIST and ``shell=False``. Because no shell
    is spawned, a user's zsh ``tmux`` function shim is bypassed — exactly what
    ``command tmux`` achieves interactively. No string is ever passed to a
    shell for word-splitting.
  - **Bracketed paste for multi-line payloads.** :meth:`bracketed_paste` loads
    the text into a tmux paste buffer and pastes it with ``paste-buffer -p`` so
    the receiving Claude TUI treats the whole multi-line blob as ONE pasted
    input that cannot fragment into separate submitted prompts
    (adversarial-review blocker #2). It does NOT submit — submitting is a
    separate single ``Enter`` keystroke the daemon sends via :meth:`send_keys`,
    which is not payload fragmentation.
  - **Atomic restart.** :meth:`respawn_pane` uses ``respawn-pane -k`` to replace
    the pane's process in one step — never ``/exit`` + screen-scraping a shell
    prompt (blocker #7).
  - **Fail-soft.** A missing session, a missing tmux binary, or any non-zero
    tmux exit returns a sentinel (``""`` / ``None`` / ``False`` / ``[]``) and
    NEVER raises, so one bad session can never crash the daemon loop.
"""

from __future__ import annotations

import itertools
import os
import subprocess
from collections.abc import Callable
from typing import Any, Protocol

import streams

__all__ = ["PaneDriver", "TmuxIO", "WindowLayoutDriver"]


class PaneDriver(Protocol):
    """The tmux surface the daemon actually depends on — its injectable seam.

    :class:`TmuxIO` satisfies this structurally, and so does the beside-tests'
    ``FakeTmux``; neither declares it, because a ``Protocol`` is checked by shape
    rather than by inheritance (the project bans inheritance in favor of exactly
    this). Typing ``Supervisor.tmux`` as ``PaneDriver`` instead of ``object`` is
    what lets a type checker see through the seam at all.

    It declares the TWELVE methods the ``Supervisor`` calls, not all nineteen
    :class:`TmuxIO` exposes. The narrower surface is the point: it states what a
    substitute must implement to be substitutable, so a test double is complete
    when it satisfies this and not before. The seven omitted methods
    (``list_sessions``, ``split_window_top``, ``set_pane_title``,
    ``select_layout_even``, ``pane_by_title``, ``set_pane_height_percent``,
    ``window_pane_titles``) drive the two-pane LAYOUT from the CLI entry points,
    which hold a concrete ``TmuxIO`` rather than reaching through this seam.
    """

    def capture_pane(self, session: str) -> str: ...

    def pane_id(self, session: str) -> str | None: ...

    def pane_pid(self, session: str) -> int | None: ...

    def pane_current_command(self, session: str) -> str | None: ...

    def pane_current_path(self, session: str) -> str | None: ...

    def session_exists(self, session: str) -> bool: ...

    def pane_pid_sessions(self) -> dict[int, str]: ...

    def send_keys(self, session: str, keys: str) -> bool: ...

    def bracketed_paste(self, session: str, text: str) -> bool: ...

    def respawn_pane(self, session: str, cwd: str, command: str) -> bool: ...

    def new_session(self, name: str, cwd: str) -> bool: ...

    def rename_window(self, pane: str, name: str) -> bool: ...


class WindowLayoutDriver(Protocol):
    """The tmux surface the two-pane BOOTSTRAP depends on — the launcher's seam.

    The counterpart to :class:`PaneDriver`, and the reason that one declares only
    twelve of :class:`TmuxIO`'s methods: these six are window-LAYOUT operations
    (split, title, resize, enumerate), used once at bootstrap by ``overseer-start``
    and never by the daemon's per-tick loop. Splitting the surfaces keeps each
    stated obligation honest — a daemon test double does not have to pretend it can
    resize a pane, and a launcher test double does not have to pretend it can paste.

    ``TmuxIO`` satisfies both structurally, being the one real implementation.
    """

    def window_pane_titles(self, pane: str) -> list[str]: ...

    def split_window_top(self, pane: str, cwd: str, command: str) -> str | None: ...

    def set_pane_title(self, pane: str, title: str) -> bool: ...

    def select_layout_even(self, pane: str) -> bool: ...

    def pane_by_title(self, pane: str, title: str) -> str | None: ...

    def set_pane_height_percent(self, pane: str, percent: int) -> bool: ...


# The tmux paste buffer the injector loads into. A UNIQUE name per paste (pid +
# monotonic counter) so two overseer instances — or a daemon and the bottom-pane
# CLI — cannot clobber each other's in-flight buffer between the load and the
# paste (adversarial code review 2026-07-13, blocker B6: the fixed global name
# ``overseer-inject`` raced across instances, pasting the wrong repo's text).
# ``paste-buffer -d`` deletes the specific buffer right after paste.
_INJECT_BUFFER_PREFIX = "overseer-inject"
_buffer_counter = itertools.count()

# Fields in one ``list-panes -F`` row: ``#{pane_id}``, ``#{pane_active}``, and the
# caller's requested field. The row is split with ``maxsplit`` one less than this,
# so a requested field containing a literal tab stays intact in the last element.
_PANE_ROW_FIELDS = 3


def _next_inject_buffer() -> str:
    return f"{_INJECT_BUFFER_PREFIX}-{os.getpid()}-{next(_buffer_counter)}"


def _warn(message: str) -> None:
    """Fail-soft diagnostic to stderr (never crash the caller)."""
    streams.write_stderr(text=f"overseer.tmuxio: {message}\n")


class TmuxIO:
    """A thin, fail-soft wrapper around the ``tmux`` CLI.

    Instantiate the real one with ``TmuxIO()``; the daemon takes it as an
    injectable dependency so tests substitute a fake object exposing the same
    methods. ``run`` is injectable purely so :mod:`tmuxio`'s OWN tests can drive
    argv construction without a live tmux — the daemon always uses the default.
    """

    def __init__(
        self,
        *,
        tmux_bin: str = "tmux",
        run: Callable[..., Any] | None = None,
    ) -> None:
        self._tmux = tmux_bin
        self._run = run if run is not None else subprocess.run

    # ----------------------------------------------------------------- #
    # Internal: run one tmux subcommand, fail-soft.
    # ----------------------------------------------------------------- #

    def _call(self, args: list[str], *, input_text: str | None = None) -> Any:
        """Run ``tmux <args>`` and return the CompletedProcess, or None on error.

        ``shell=False`` (argv list) bypasses any zsh ``tmux`` shim — the
        ``command tmux`` effect. A missing binary or OS error returns None.
        """
        try:
            return self._run(
                [self._tmux, *args],
                input=input_text,
                capture_output=True,
                text=True,
                check=False,
            )
        except (OSError, ValueError) as exc:
            _warn(f"tmux {' '.join(args[:2])} failed to spawn: {exc}")
            return None

    @staticmethod
    def _ok(completed: Any) -> bool:
        return completed is not None and getattr(completed, "returncode", 1) == 0

    # ----------------------------------------------------------------- #
    # Reads.
    # ----------------------------------------------------------------- #

    def capture_pane(self, session: str) -> str:
        """``tmux capture-pane -p -t <session>`` → visible pane text (``""`` on error)."""
        completed = self._call(["capture-pane", "-p", "-t", session])
        if not self._ok(completed):
            return ""
        return completed.stdout

    def _pane_field(self, target: str, fmt: str) -> str | None:
        """One RELIABLE per-pane read via ``list-panes`` (not ``display-message``).

        ``display-message -p -t <session>`` was observed returning EMPTY for some
        detached sessions (prior-session live note 2026-07-13); ``list-panes -t
        <target> -F`` reads the pane list directly and is reliable (re-verified
        2026-07-13: 21/21 sessions, repeatedly). ``target`` may be a SESSION NAME
        (→ the active pane's field) or an exact PANE ID like ``%5`` (→ that pane's
        field, filtered by ``#{pane_id}`` so RB3 exactness holds and a dead pane
        fails soft to None rather than a prefix sibling). None on any error or
        empty value.
        """
        completed = self._call(
            ["list-panes", "-t", target, "-F", "#{pane_id}\t#{pane_active}\t" + fmt]
        )
        if not self._ok(completed):
            return None
        rows = [
            parts
            for line in (completed.stdout or "").splitlines()
            if line.strip()
            for parts in [line.split("\t", _PANE_ROW_FIELDS - 1)]
            if len(parts) == _PANE_ROW_FIELDS
        ]
        if not rows:
            return None
        if target.startswith("%"):
            chosen = next((r for r in rows if r[0] == target), None)
        else:
            chosen = next((r for r in rows if r[1] == "1"), rows[0])
        if chosen is None:
            return None
        return chosen[2].strip() or None

    def pane_id(self, session: str) -> str | None:
        """``#{pane_id}`` — the pane's globally-unique id (e.g. ``%5``), or None.

        Resolved from the (exact-verified) session name once per tick; the daemon
        then targets every subsequent pane op by this id, NOT the name. A pane id
        is exact and is NEVER prefix/fnmatch-matched, so if the tracked session
        dies mid-tick the id simply fails-soft (no match) instead of a bare ``-t
        <name>`` falling back to a live sibling session and acting on the wrong one
        (adversarial code re-review 2026-07-13, blocker RB3). The id is STABLE
        across ``respawn-pane`` (same pane, new process), so restart + resume keep
        targeting the right pane.
        """
        return self._pane_field(session, "#{pane_id}")

    def pane_pid(self, session: str) -> int | None:
        """``#{pane_pid}`` — the pane's process PID (the login shell), or None."""
        value = self._pane_field(session, "#{pane_pid}")
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def pane_current_command(self, session: str) -> str | None:
        """``#{pane_current_command}`` — the pane's foreground command (e.g. ``node``)."""
        return self._pane_field(session, "#{pane_current_command}")

    def pane_current_path(self, session: str) -> str | None:
        """``#{pane_current_path}`` — the pane's working directory."""
        return self._pane_field(session, "#{pane_current_path}")

    def session_exists(self, session: str) -> bool:
        """True iff a session named EXACTLY ``session`` is live.

        Uses exact membership in :meth:`list_sessions`, NOT ``tmux has-session -t
        <session>``: a bare ``-t`` target PREFIX/fnmatch-matches, so ``has-session
        -t foo`` succeeds when only ``foobar`` exists (verified live 2026-07-13,
        adversarial code review blocker B1) — which let the daemon believe a gone
        session was live and act on an unrelated prefix-matching one. Exact
        membership is the only prefix-proof existence test. Every subsequent
        ``-t <session>`` call is then safe because an EXACT session name takes
        precedence over a prefix match, so it resolves to this exact session.
        """
        return session in self.list_sessions()

    def list_sessions(self) -> list[str]:
        """``tmux list-sessions -F '#{session_name}'`` → names (``[]`` on error)."""
        completed = self._call(["list-sessions", "-F", "#{session_name}"])
        if not self._ok(completed):
            return []
        return [line for line in (completed.stdout or "").splitlines() if line.strip()]

    def pane_pid_sessions(self) -> dict[int, str]:
        """``{pane_pid: session_name}`` for EVERY pane across all sessions (``{}`` on error).

        ``tmux list-panes -a -F '#{pane_pid}\\t#{session_name}'`` — the process-side
        of the registry→tmux join (:mod:`claude_sessions`): a claude PID is a
        descendant of its pane's PID, so walking the claude PID up its parent chain
        to one of these pane PIDs identifies the owning session. Every pane is
        included (a session may have several), so any pane holding the worker
        resolves. Malformed / non-integer rows are skipped fail-soft.
        """
        completed = self._call(["list-panes", "-a", "-F", "#{pane_pid}\t#{session_name}"])
        if not self._ok(completed):
            return {}
        out: dict[int, str] = {}
        for line in (completed.stdout or "").splitlines():
            pid_str, _, session = line.partition("\t")
            if not session.strip():
                continue
            try:
                out[int(pid_str)] = session
            except ValueError:
                continue
        return out

    # ----------------------------------------------------------------- #
    # Writes.
    # ----------------------------------------------------------------- #

    def send_keys(self, session: str, keys: str) -> bool:
        """``tmux send-keys -t <session> <keys>`` — for a single named key (``Enter``).

        Used ONLY to submit a prompt AFTER a bracketed paste; never to type a
        multi-line payload key-by-key (that would fragment it — blocker #2).
        """
        return self._ok(self._call(["send-keys", "-t", session, keys]))

    def bracketed_paste(self, session: str, text: str) -> bool:
        """Insert ``text`` into the pane as ONE bracketed paste (no submit).

        Two tmux calls: ``load-buffer -`` reads the payload from stdin into a
        named buffer; ``paste-buffer -p -d`` pastes it in bracketed-paste mode
        (so the Claude TUI takes the whole multi-line blob as a single pasted
        input) and deletes the buffer. Submitting is the caller's separate
        :meth:`send_keys` ``Enter`` — because ``paste-buffer`` never submits.
        """
        buffer_name = _next_inject_buffer()
        loaded = self._call(["load-buffer", "-b", buffer_name, "-"], input_text=text)
        if not self._ok(loaded):
            _warn(f"load-buffer failed for session {session!r}")
            return False
        pasted = self._call(["paste-buffer", "-b", buffer_name, "-p", "-d", "-t", session])
        return self._ok(pasted)

    def respawn_pane(self, session: str, cwd: str, command: str) -> bool:
        """``tmux respawn-pane -k -c <cwd> -t <session> <command>``.

        Atomically kills (``-k``) whatever ran in the pane and launches
        ``command`` in ``cwd`` — the safe restart primitive (blocker #7). The
        abrupt kill is safe because the restart interlock already proved the
        handoff is written and the ready marker exists.
        """
        return self._ok(self._call(["respawn-pane", "-k", "-c", cwd, "-t", session, command]))

    def new_session(self, name: str, cwd: str) -> bool:
        """``tmux new-session -d -s <name> -c <cwd>`` — a detached session in ``cwd``."""
        return self._ok(self._call(["new-session", "-d", "-s", name, "-c", cwd]))

    # ----------------------------------------------------------------- #
    # Two-pane bootstrap (the `/overseer` skill splits its OWN window).
    # ----------------------------------------------------------------- #

    def split_window_top(self, pane: str, cwd: str, command: str) -> str | None:
        """Split PANE's window; new pane ABOVE, focus stays on PANE; run COMMAND in CWD.

        ``-v`` splits top/bottom, ``-b`` puts the NEW pane before (above) the
        target, ``-d`` keeps focus on the target (the bottom Claude pane), and
        ``-P -F '#{pane_id}'`` prints the new pane id. Targeting ``pane`` (the
        skill's own ``$TMUX_PANE``) means the daemon pane is created in the
        skill's OWN window — never in a session grabbed by name. Returns the new
        pane id (e.g. ``%47``) or None on failure.
        """
        completed = self._call(
            [
                "split-window",
                "-v",
                "-b",
                "-d",
                "-P",
                "-F",
                "#{pane_id}",
                "-t",
                pane,
                "-c",
                cwd,
                command,
            ]
        )
        if not self._ok(completed):
            return None
        return (completed.stdout or "").strip() or None

    def set_pane_title(self, pane: str, title: str) -> bool:
        """``tmux select-pane -t <pane> -T <title>`` — tag a pane (idempotency)."""
        return self._ok(self._call(["select-pane", "-t", pane, "-T", title]))

    def select_layout_even(self, pane: str) -> bool:
        """``tmux select-layout -t <pane> even-vertical`` — restack the window evenly.

        A THIRD pane that was opened and later closed leaves tmux's rows
        redistributed unevenly. Running this on every ``overseer-start`` normalizes
        the window (targeting ``pane`` targets its window) BEFORE
        :meth:`set_pane_height_percent` gives the daemon its share — so the resize
        starts from a known stack rather than whatever a stray pane left behind.
        """
        return self._ok(self._call(["select-layout", "-t", pane, "even-vertical"]))

    def pane_by_title(self, pane: str, title: str) -> str | None:
        """The pane id in PANE's window whose title is TITLE (``None`` if absent).

        The idempotent-path counterpart of :meth:`window_pane_titles`: that answers
        "is the daemon pane here?", this answers "which pane IS it?" — needed to
        target the daemon pane for a resize when ``overseer-start`` re-runs and did
        not create it (so never held its id).
        """
        completed = self._call(["list-panes", "-t", pane, "-F", "#{pane_id}\t#{pane_title}"])
        if not self._ok(completed):
            return None
        for line in (completed.stdout or "").splitlines():
            pane_id, _, pane_title = line.partition("\t")
            if pane_title.strip() == title:
                return pane_id.strip() or None
        return None

    def set_pane_height_percent(self, pane: str, percent: int) -> bool:
        """``tmux resize-pane -t <pane> -y <percent>%`` — size PANE to a share of its window.

        Percentage sizes are a tmux feature (verified on 3.5a), so the split does not
        have to be recomputed in rows against a window height that changes whenever the
        terminal is resized.
        """
        return self._ok(self._call(["resize-pane", "-t", pane, "-y", f"{percent}%"]))

    def rename_window(self, pane: str, name: str) -> bool:
        """Rename PANE's window to NAME, and PIN the name (``automatic-rename off``).

        Pinning is part of renaming, not an optional extra: tmux otherwise re-derives a
        window's name from its foreground command on the next tick and silently
        overwrites NAME. Both steps must succeed for the rename to hold.
        """
        if not self._ok(self._call(["rename-window", "-t", pane, name])):
            return False
        return self._ok(self._call(["set-window-option", "-t", pane, "automatic-rename", "off"]))

    def window_pane_titles(self, pane: str) -> list[str]:
        """Every pane title in PANE's window (``[]`` on error) — the idempotency read."""
        completed = self._call(["list-panes", "-t", pane, "-F", "#{pane_title}"])
        if not self._ok(completed):
            return []
        return [line for line in (completed.stdout or "").splitlines() if line.strip()]
