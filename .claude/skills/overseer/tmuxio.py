"""tmuxio.py — the ONE module that shells out to tmux.

Stdlib-only, host-only (see ``registry.py`` header — this whole skill folder is
deliberately OUTSIDE the livespec product gates). Every other overseer module
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
import sys
from collections.abc import Callable
from typing import Any

__all__ = ["TmuxIO"]

# The tmux paste buffer the injector loads into. A UNIQUE name per paste (pid +
# monotonic counter) so two overseer instances — or a daemon and the bottom-pane
# CLI — cannot clobber each other's in-flight buffer between the load and the
# paste (adversarial code review 2026-07-13, blocker B6: the fixed global name
# ``overseer-inject`` raced across instances, pasting the wrong repo's text).
# ``paste-buffer -d`` deletes the specific buffer right after paste.
_INJECT_BUFFER_PREFIX = "overseer-inject"
_buffer_counter = itertools.count()


def _next_inject_buffer() -> str:
    return f"{_INJECT_BUFFER_PREFIX}-{os.getpid()}-{next(_buffer_counter)}"


def _warn(message: str) -> None:
    """Fail-soft diagnostic to stderr (never crash the caller)."""
    print(f"overseer.tmuxio: {message}", file=sys.stderr)


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

    def _display(self, session: str, fmt: str) -> str | None:
        """``tmux display-message -p -t <session> '<fmt>'`` → stripped value or None."""
        completed = self._call(["display-message", "-p", "-t", session, fmt])
        if not self._ok(completed):
            return None
        value = (completed.stdout or "").strip()
        return value or None

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
        return self._display(session, "#{pane_id}")

    def pane_current_command(self, session: str) -> str | None:
        """``#{pane_current_command}`` — the pane's foreground command (e.g. ``node``)."""
        return self._display(session, "#{pane_current_command}")

    def pane_current_path(self, session: str) -> str | None:
        """``#{pane_current_path}`` — the pane's working directory."""
        return self._display(session, "#{pane_current_path}")

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

    def window_pane_titles(self, pane: str) -> list[str]:
        """Every pane title in PANE's window (``[]`` on error) — the idempotency read."""
        completed = self._call(["list-panes", "-t", pane, "-F", "#{pane_title}"])
        if not self._ok(completed):
            return []
        return [line for line in (completed.stdout or "").splitlines() if line.strip()]
