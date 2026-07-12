"""signals.py — pure pane-text parsing + filesystem-marker certification.

Stdlib-only, host-only (see ``registry.py`` header). **No subprocess calls
here.** Every pane function takes a captured-text STRING and returns a value,
so it is unit-testable with no tmux — the actual ``tmux capture-pane`` +
``tmux display-message`` subprocesses belong to the daemon (the next build).

The load-bearing correctness fact (see design.md, adversarial review): a pane's
text stream cannot carry a trustworthy "the session asserts X now" signal —
prompt-echo, model quotation, scroll, and line-wrap all corrupt it. So the
readiness/blocked *certification* is out-of-band on the filesystem
(``.overseer-ready`` / ``.overseer-blocked`` marker files), and pane text is
trusted ONLY for the busy / idle / gate signals, which are not echo-forgeable
in a harmful direction (a false "busy" merely suppresses action — the safe
direction).
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

__all__ = [
    "blocked_marker",
    "blocked_marker_path",
    "is_busy",
    "is_idle_input",
    "is_structured_gate",
    "pane_is_claude",
    "pane_is_shell",
    "parse_ctx_remaining",
    "path_in_repo",
    "ready_marker_path",
    "ready_marker_valid",
    "strip_ansi",
]


# --------------------------------------------------------------------------- #
# ANSI stripping (terminal escape sequences corrupt naive substring matching).
# --------------------------------------------------------------------------- #

_ANSI_RE = re.compile(
    r"\x1b\[[0-9;?]*[ -/]*[@-~]"  # CSI: colors, cursor moves, erases
    r"|\x1b\][^\x07]*\x07"  # OSC: e.g. terminal-title, BEL-terminated
    r"|\x1b[@-Z\\-_]"  # two-char escapes (e.g. ESC c)
)


def strip_ansi(text: str) -> str:
    """Remove ANSI/VT escape sequences from captured pane text."""
    return _ANSI_RE.sub("", text)


# --------------------------------------------------------------------------- #
# Context-% reading — anchored + fail-closed (see design.md, context-% reading,
# adversarial-review blocker #5).
# --------------------------------------------------------------------------- #

_CTX_RE = re.compile(r"Ctx:\s*(\d+)%\s*left")


def _last_non_empty_line(capture_text: str) -> str | None:
    """The last line whose ANSI-stripped, whitespace-stripped body is non-empty."""
    for raw in reversed(capture_text.splitlines()):
        line = strip_ansi(raw).strip()
        if line:
            return line
    return None


def parse_ctx_remaining(capture_text: str) -> int | None:
    """Remaining-context percent from the statusline, anchored + fail-closed.

    Reads ONLY the last non-empty row of the capture (the statusline row),
    strips ANSI, and returns the LAST ``Ctx: N% left`` match on that row.
    Returns None ("unknown") if the last row carries no match — it NEVER scans
    the whole capture, because page content (including the overseer design doc
    itself) contains the literal string ``Ctx: N% left`` and would yield a
    false reading. "unknown" must NEVER count as a threshold crossing upstream.
    """
    last = _last_non_empty_line(capture_text)
    if last is None:
        return None
    matches = _CTX_RE.findall(last)
    if not matches:
        return None
    return int(matches[-1])


# --------------------------------------------------------------------------- #
# Busy / structured-gate / idle-input detection (see design.md, signal sources).
# --------------------------------------------------------------------------- #

# `Waiting for N background…` where N is a number.
_WAITING_RE = re.compile(r"Waiting for \d+ background", re.IGNORECASE)
# `N shell` (running shell subprocesses), e.g. "2 shells".
_SHELL_RE = re.compile(r"\b\d+\s+shells?\b", re.IGNORECASE)


def is_busy(capture_text: str) -> bool:
    """True if any busy marker is present (`esc to interrupt`, `Waiting for N
    background`, `N shell`).

    A liberal (over-firing) busy detector is the SAFE direction: a false busy
    merely suppresses an injection/restart; a missed busy is the dangerous one.
    """
    text = strip_ansi(capture_text)
    if "esc to interrupt" in text.lower():
        return True
    if _WAITING_RE.search(text):
        return True
    return bool(_SHELL_RE.search(text))


# The permission-prompt / picker cursor: a `❯` immediately before a numbered
# option (`❯ 1.`), present in both the Claude permission dialog and the
# AskUserQuestion picker. Best-effort; documented markers.
_GATE_CURSOR_RE = re.compile(r"❯\s*\d+\.")


def is_structured_gate(capture_text: str) -> bool:
    """True if the pane shows a structured permission-prompt / picker gate.

    Best-effort. Keyed on two low-false-positive markers: a ``❯ N.`` numbered
    cursor option, or the literal permission question ``Do you want to
    proceed`` (case-insensitive). Used to SUPPRESS injection — never keystroke
    into a gate (adversarial-review blocker #6).
    """
    text = strip_ansi(capture_text)
    if _GATE_CURSOR_RE.search(text):
        return True
    return "do you want to proceed" in text.lower()


# The idle input box: the Claude TUI shows a `? for shortcuts` hint line only at
# the idle prompt (when busy it is replaced by `esc to interrupt`). The border
# fallback covers captures where the hint scrolled off but the box is present.
_PROMPT_HINT = "? for shortcuts"
_PROMPT_LINE_RE = re.compile(r"(?m)^\s*(?:│\s*)?>\s")


def _prompt_box_present(text: str) -> bool:
    if _PROMPT_HINT in text.lower():
        return True
    return "╭" in text and "╰" in text and bool(_PROMPT_LINE_RE.search(text))


def is_idle_input(capture_text: str) -> bool:
    """True only for a VERIFIED normal input state.

    Prompt box present AND not busy AND not a structured gate. "Not busy" alone
    is NOT idle-input (see design.md, signal sources) — a positive prompt-box
    marker is required, so a blank/frozen pane is not mistaken for idle.
    """
    text = strip_ansi(capture_text)
    if not _prompt_box_present(text):
        return False
    if is_busy(capture_text):
        return False
    return not is_structured_gate(capture_text)


# --------------------------------------------------------------------------- #
# Out-of-band marker certification (see design.md, the certification protocol,
# blockers #1,#3,#4). These read the filesystem but NEVER a subprocess.
# --------------------------------------------------------------------------- #


def ready_marker_path(repo: str, topic: str) -> Path:
    """``<repo>/plan/<topic>/.overseer-ready``."""
    return Path(repo) / "plan" / topic / ".overseer-ready"


def blocked_marker_path(repo: str, topic: str) -> Path:
    """``<repo>/plan/<topic>/.overseer-blocked``."""
    return Path(repo) / "plan" / topic / ".overseer-blocked"


def ready_marker_valid(
    repo: str,
    topic: str,
    handoff_path: str | os.PathLike[str],
    injection_stamp: float | None,
) -> bool:
    """The load-bearing restart certification. True only when ALL hold:

    1. an injection stamp exists for this round (``injection_stamp`` is not
       None) — without a recorded injection there is no round to certify,
    2. the ``.overseer-ready`` marker file EXISTS,
    3. its mtime is strictly newer than ``injection_stamp`` (this round, not a
       stale marker), AND
    4. its stripped contents equal the SHA-256 hex of the current on-disk
       ``handoff.md`` (proving the session actually updated the handoff).

    Any missing/unreadable file → False (fail-closed). A file write cannot be
    forged by prompt-echo, cannot scroll off, and cannot line-wrap, so the
    pane-text blockers all dissolve here.
    """
    if injection_stamp is None:
        return False
    marker = ready_marker_path(repo, topic)
    try:
        if not marker.is_file():
            return False
        if marker.stat().st_mtime <= injection_stamp:
            return False
        expected = hashlib.sha256(Path(handoff_path).read_bytes()).hexdigest()
        actual = marker.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    return actual == expected


def blocked_marker(repo: str, topic: str) -> str | None:
    """The stripped contents of ``.overseer-blocked`` if present, else None.

    Presence (not content) is the blocked signal, so an existing-but-empty
    marker returns ``""`` (not None); only an absent/unreadable marker returns
    None.
    """
    marker = blocked_marker_path(repo, topic)
    try:
        if not marker.is_file():
            return None
        return marker.read_text(encoding="utf-8").strip()
    except OSError:
        return None


# --------------------------------------------------------------------------- #
# Process-identity helpers — interpret tmux `#{pane_current_command}` /
# `#{pane_current_path}` (see design.md, signal sources). Pure; no fs access.
# --------------------------------------------------------------------------- #

# A live Claude Code TUI runs as a `node` process; `claude` covers a wrapper.
_CLAUDE_COMMANDS = frozenset({"node", "claude"})
_SHELL_COMMANDS = frozenset({"zsh", "bash", "sh", "fish", "dash", "ksh"})


def pane_is_claude(pane_current_command: str | None) -> bool:
    """True if ``#{pane_current_command}`` looks like a running Claude TUI."""
    cmd = (pane_current_command or "").strip().lower()
    if not cmd:
        return False
    return cmd in _CLAUDE_COMMANDS or "claude" in cmd


def pane_is_shell(pane_current_command: str | None) -> bool:
    """True if ``#{pane_current_command}`` is an interactive shell."""
    return (pane_current_command or "").strip().lower() in _SHELL_COMMANDS


def path_in_repo(pane_current_path: str | None, repo: str | os.PathLike[str]) -> bool:
    """True if ``#{pane_current_path}`` resolves inside ``repo``.

    Pure path prefix check (``os.path.normpath``, no symlink resolution, no fs
    access) used for the daemon's restart-proof and its auto-link guard (a live
    session is linked to a row only when its cwd is inside the row's repo —
    never by topic name alone, adversarial-review blocker #8).
    """
    if not pane_current_path or not str(repo):
        return False
    current = os.path.normpath(pane_current_path)
    root = os.path.normpath(str(repo))
    return current == root or current.startswith(root + os.sep)
