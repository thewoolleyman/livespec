"""signals.py — pure pane-text parsing + filesystem-marker certification.

Stdlib-only, host-only (see ``registry.py`` header). **No subprocess calls
here.** Every pane function takes a captured-text STRING and returns a value,
so it is unit-testable with no tmux — the actual ``tmux capture-pane`` +
``tmux display-message`` subprocesses belong to the daemon (the next build).

The load-bearing correctness fact (see design.md, adversarial review): a pane's
text stream cannot carry a trustworthy "the session asserts X now" signal —
prompt-echo, model quotation, scroll, and line-wrap all corrupt it. So the
session's self-declared *state* is out-of-band on the filesystem (the ONE
``.overseer-state`` file: ``ready`` / ``blocked`` / ``winding-down``), and pane text is
trusted ONLY for the busy / idle / gate signals, which are not echo-forgeable
in a harmful direction (a false "busy" merely suppresses action — the safe
direction).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "STATE_BLOCKED",
    "STATE_IDLE_WITH_CONTEXT_LEFT",
    "STATE_READY",
    "STATE_TOKENS",
    "STATE_WINDING_DOWN",
    "TrackState",
    "codex_prompt_present",
    "input_box_ready",
    "is_busy",
    "is_codex_idle_input",
    "is_idle_input",
    "is_structured_gate",
    "marker_dir",
    "pane_is_claude",
    "pane_is_codex",
    "pane_is_shell",
    "parse_ctx_remaining",
    "path_in_repo",
    "read_state",
    "ready_valid",
    "state_path",
    "strip_ansi",
    "valid_token",
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

# Claude renders `Ctx: N% left`; Codex renders `Context N% left`. Both are the
# RUNTIME'S OWN computed number, which is the whole point of reading it here rather
# than recomputing occupancy ourselves — see the Codex note in `codex_sessions`.
_CTX_RE = re.compile(r"(?:Ctx:|Context)\s*(\d+)%\s*left")

# How many trailing non-empty rows to scan for the statusline. The live Claude
# TUI renders the statusline as the SECOND-to-last row — a footer hint line
# (`⏵⏵ bypass permissions…` / `? for shortcuts`) renders BELOW it (verified
# live 2026-07-13), so reading only the LAST row misses `Ctx:` entirely. A
# small bound (not the whole capture) preserves the anti-false-match intent
# (blocker #5): page content containing `Ctx: N% left` sits far above the
# bottom few rows.
_CTX_TAIL_ROWS = 4


def _tail_non_empty_lines(capture_text: str, n: int) -> list[str]:
    """The last ``n`` ANSI-stripped, non-empty lines, in top-to-bottom order."""
    out: list[str] = []
    for raw in reversed(capture_text.splitlines()):
        line = strip_ansi(raw).strip()
        if line:
            out.append(line)
            if len(out) >= n:
                break
    out.reverse()
    return out


def parse_ctx_remaining(capture_text: str) -> int | None:
    """Remaining-context percent from the statusline, anchored + fail-closed.

    Scans only the last few non-empty rows (`_CTX_TAIL_ROWS`) — the statusline
    is the SECOND-to-last row in the live TUI, with a footer hint line below it
    — and returns the LAST ``Ctx: N% left`` match found across them. Returns
    None ("unknown") if none of those rows carries a match; it NEVER scans the
    whole capture, because page content (including the overseer design doc
    itself) contains the literal string ``Ctx: N% left`` and would yield a false
    reading. "unknown" must NEVER count as a threshold crossing upstream.
    """
    matches: list[str] = []
    for line in _tail_non_empty_lines(capture_text, _CTX_TAIL_ROWS):
        matches.extend(_CTX_RE.findall(line))
    if not matches:
        return None
    return int(matches[-1])


# --------------------------------------------------------------------------- #
# Busy / structured-gate / idle-input detection (see design.md, signal sources).
# --------------------------------------------------------------------------- #

# `Waiting for N background…` where N is a number.
_WAITING_RE = re.compile(r"Waiting for \d+ background", re.IGNORECASE)
# Active-generation markers (verified live 2026-07-13). The live TUI busy
# indicator is a spinner line such as
#   ``✻ Galloping… (running stop hooks… 1/3 · 24s · ↓ 1.4k tokens)``
# — NOT the string ``esc to interrupt``. These CONTENT signals fire only during
# active generation and NOT on the lingering completed-turn summary
# ``✻ Brewed for 25s`` (no parenthetical, no token counter, and `for Ns` rather
# than the `· Ns ·` dot-delimited elapsed form). Glyph-independent, so a
# rotating spinner glyph can't break it.
_BUSY_ACTIVE_RE = re.compile(
    r"esc to interrupt"  # kept: older/other layouts may still show it
    r"|[↓↑]\s*[\d.]+\s*k?\s*tokens"  # streaming token counter (active only)
    r"|·\s*\d+\s*s\s*[·)]"  # `· 24s ·` / `· 24s)` dot-delimited elapsed
    r"|\(\s*running\b",  # `(running … hook…` phase
    re.IGNORECASE,
)


def is_busy(capture_text: str) -> bool:
    """True if the pane is actively working.

    Fires on the live active-generation spinner (`_BUSY_ACTIVE_RE`) or a
    `Waiting for N background` line. A liberal (over-firing) busy detector is the
    SAFE direction: a false busy merely suppresses an injection/restart; a missed
    busy is the dangerous one. The lingering completed-turn summary
    (`✻ Brewed for 25s`) is deliberately NOT treated as busy.
    """
    text = strip_ansi(capture_text)
    if _WAITING_RE.search(text):
        return True
    return bool(_BUSY_ACTIVE_RE.search(text))


# The permission-prompt / picker cursor: a `❯` (Claude) or `›` (Codex) immediately
# before a numbered option (`❯ 1.` / `› 1.`), present in the Claude permission dialog,
# the AskUserQuestion picker, AND Codex's approval / directory-trust picker (verified
# live 2026-07-17: `› 1. Yes, continue` / `  2. No, quit`). BOTH glyphs are load-bearing
# — a Codex track is now a full citizen that gets the wrap-up pasted in, so a Codex
# picker MUST suppress injection or the paste would type into the `1/2` chooser.
# Best-effort; documented markers.
_GATE_CURSOR_RE = re.compile(r"[❯›]\s*\d+\.")


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


# The live idle input box is an EMPTY `❯` prompt line sandwiched between two
# horizontal rule lines (`────…`), with the statusline + footer hint below it
# (verified live 2026-07-13 — NOT a `╭─╮` rounded box with `? for shortcuts`).
# We detect that structural shape: it is stable across idle and busy and is
# independent of the footer-hint wording and the spinner glyph.
#
# The border MAY carry an embedded title. `claude -n <topic>` renders the session
# name INTO the top border (`─── mytopic ──` — verified live 2026-07-13), so the
# top border is NOT a pure rule; a pure-rule-only match would make EVERY session
# the daemon itself launches (all of `start` / `--recover` / post-restart, which
# always pass `-n <topic>`) read as never-idle → never injected/restarted again →
# run to autocompact, the exact failure the overseer exists to prevent (adversarial
# code review 2026-07-13, blocker B2). So a border is: starts with ≥3 rule chars
# AND ends with ≥2 rule chars (a pure rule satisfies this too). That is tight
# enough that ordinary wrapped prose / tool output — which does not both start and
# end with box-drawing rule chars — is not mistaken for a border.
_BORDER_RE = re.compile(r"^[─—━]{3,}.*[─—━]{2,}$")


def _is_border(line: str) -> bool:
    """True if ``line`` is a box border: a pure rule OR a rule with an embedded title."""
    return _BORDER_RE.match(line) is not None


def _is_empty_prompt(line: str) -> bool:
    """True if ``line`` is the empty idle prompt: the `❯` glyph with nothing after."""
    return line.startswith("❯") and not line[1:].strip()


def _input_box_present(text: str) -> bool:
    """True if an EMPTY `❯` prompt sits between two box-border lines.

    Scans the non-empty lines and requires an empty `❯` with a border line
    immediately before and after it. The border above MAY carry the `-n <topic>`
    title (`─── mytopic ──`); the border below is a pure rule. The empty-prompt
    requirement means a box that already holds typed/pasted input is NOT treated
    as idle (the daemon must never inject over existing input). A numbered-option
    gate (`❯ 1.`) is not empty and not border-bracketed, so it is excluded here
    (and by :func:`is_structured_gate`).
    """
    ne = [stripped for raw in text.splitlines() if (stripped := strip_ansi(raw).strip())]
    for i, line in enumerate(ne):
        if not _is_empty_prompt(line):
            continue
        above = i >= 1 and _is_border(ne[i - 1])
        below = i + 1 < len(ne) and _is_border(ne[i + 1])
        if above and below:
            return True
    return False


def is_idle_input(capture_text: str) -> bool:
    """True only for a VERIFIED normal, EMPTY input state.

    An empty `❯` prompt box (positive structural marker) is present AND the pane
    is not busy AND not a structured gate. "Not busy" alone is NOT idle-input
    (see design.md, signal sources) — a blank / frozen / booting pane has no
    input box and is therefore not idle.
    """
    if is_busy(capture_text):
        return False
    if is_structured_gate(capture_text):
        return False
    return _input_box_present(capture_text)


def input_box_ready(capture_text: str) -> bool:
    """True if the EMPTY `❯` input box is present (regardless of busy/gate).

    Unlike :func:`is_idle_input`, this does NOT require not-busy — it is the
    "the prompt cleared" signal the daemon uses to confirm a pasted prompt
    actually SUBMITTED (after submit the box empties; while a fresh session is
    still drawing its welcome screen the box holds the un-submitted paste, so
    this stays False until an Enter lands).
    """
    return _input_box_present(capture_text)


# The Codex TUI renders a DIFFERENT idle shape from Claude's `❯`-between-rules box: a
# `›` input line sitting above its statusline (`model · cwd · Context N% left · <name>`),
# with a grey ROTATING placeholder when the box is empty — indistinguishable from typed
# text in an ANSI-stripped capture. So Codex idle detection is STRUCTURAL (a `›` prompt +
# a Codex statusline, not busy, not a picker), never Claude's cleared-`❯` check, and a
# Codex submit is confirmed by the pane going BUSY, not by an emptied box (see
# supervisor `_submit_prompt`). Verified live 2026-07-17 (codex-cli 0.144.5).
_CODEX_STATUSLINE_RE = re.compile(r"Context\s+\d+%\s+left")


def codex_prompt_present(capture_text: str) -> bool:
    """True if the pane is a live Codex TUI sitting at its input prompt.

    Structural + glyph-anchored: a ``›`` input line AND a Codex statusline
    (``… · Context N% left · …``) among the visible rows, independent of the rotating
    placeholder wording. It is present whether the box is empty OR holds text (the
    placeholder problem above), so it asserts only "a Codex TUI is here"; idle-ness adds
    not-busy + not-gate (:func:`is_codex_idle_input`).
    """
    text = strip_ansi(capture_text)
    if not _CODEX_STATUSLINE_RE.search(text):
        return False
    return any(line.lstrip().startswith("›") for line in text.splitlines())


def is_codex_idle_input(capture_text: str) -> bool:
    """The Codex analogue of :func:`is_idle_input`: a Codex prompt that is neither busy
    nor a structured gate.

    STRUCTURAL, never the coarse "not busy" — so a Codex approval / directory-trust
    picker (``› 1.``, caught by :func:`is_structured_gate`) or a booting / blank pane is
    NOT read as idle and can never be keystroked into. This matters because a Codex track
    is now a full citizen: an over-loose idle read would paste the wrap-up into a Codex
    gate.
    """
    if is_busy(capture_text):
        return False
    if is_structured_gate(capture_text):
        return False
    return codex_prompt_present(capture_text)


# --------------------------------------------------------------------------- #
# Out-of-band marker certification (see design.md, the certification protocol,
# blockers #1,#3,#4). These read the filesystem but NEVER a subprocess.
# --------------------------------------------------------------------------- #


def marker_dir(repo: str, topic: str) -> Path:
    """``<repo>/tmp/overseer/<topic>/`` — the overseer's per-track TEMP dir.

    The markers live under the repo's ``tmp/`` (gitignored, maintainer-owned
    scratch), NOT under ``plan/``: the overseer NEVER touches files inside a
    session's ``plan/<topic>/`` tree — that is the session's own workflow. The
    daemon validates each watched repo's ``tmp/overseer/`` is gitignored at
    startup (else it refuses to start).
    """
    return Path(repo) / "tmp" / "overseer" / topic


# The values of the SINGLE indicator file. One file with a VALUE — never a set of
# separate presence-markers: two files (`.overseer-ready` + `.overseer-blocked`)
# carried a built-in ambiguity, because nothing stopped BOTH existing and their
# precedence was incidental rather than designed (maintainer 2026-07-14).
#
# `STATE_TOKENS` are the three the SESSION declares (used verbatim in the session-facing
# wrap-up + malformed-token messages). `STATE_IDLE_WITH_CONTEXT_LEFT` is the ONE token the
# DAEMON writes itself — the "I nudged this idle-with-context-left session to keep going
# this episode" marker (single-prompt edge-trigger). It is kept OUT of `STATE_TOKENS` so
# the session-facing text still lists only the three a session should write, but
# `valid_token` accepts it so the daemon's own marker is never surfaced as malformed.
STATE_READY = "ready"
STATE_BLOCKED = "blocked"
STATE_WINDING_DOWN = "winding-down"
STATE_IDLE_WITH_CONTEXT_LEFT = "idle-with-context-left"
STATE_TOKENS = (STATE_READY, STATE_BLOCKED, STATE_WINDING_DOWN)
_DAEMON_TOKENS = (STATE_IDLE_WITH_CONTEXT_LEFT,)


def state_path(repo: str, topic: str) -> Path:
    """``<repo>/tmp/overseer/<topic>/.overseer-state`` — the ONE indicator file."""
    return marker_dir(repo, topic) / ".overseer-state"


@dataclass(frozen=True, kw_only=True)
class TrackState:
    """A tracked session's self-declared state — parsed from the one indicator file.

    ``token`` is the raw lowercased first word (may be INVALID — use
    :func:`valid_token` before trusting it, so a typo'd value is surfaced as
    malformed rather than silently ignored). ``detail`` is the optional free text
    after a ``:`` (e.g. the one-line reason on ``blocked``). ``mtime`` powers the
    this-round freshness check.
    """

    token: str
    detail: str
    mtime: float


def valid_token(token: str) -> bool:
    """True iff ``token`` is a recognized state — a session-declared one
    (:data:`STATE_TOKENS`) OR the daemon-written idle-with-context-left marker.
    Only genuinely unrecognized (typo'd) tokens are surfaced as malformed."""
    return token in STATE_TOKENS or token in _DAEMON_TOKENS


def read_state(repo: str, topic: str) -> TrackState | None:
    """Parse ``.overseer-state``; None when absent or unreadable (fail-closed).

    Format — the first non-empty line is ``<token>`` or ``<token>: <detail>``::

        ready
        blocked: waiting on the schema call
        winding-down

    A file write cannot be forged by prompt-echo, cannot scroll off, and cannot
    line-wrap, so all the pane-text blockers dissolve here. The token is returned
    verbatim (lowercased) even when unknown, so the daemon can SURFACE a malformed
    value instead of silently treating it as "no state".
    """
    path = state_path(repo, topic)
    try:
        if not path.is_file():
            return None
        raw = path.read_text(encoding="utf-8")
        mtime = path.stat().st_mtime
    except OSError:
        return None
    line = next((ln.strip() for ln in raw.splitlines() if ln.strip()), "")
    token, _, detail = line.partition(":")
    return TrackState(token=token.strip().lower(), detail=detail.strip(), mtime=mtime)


def ready_valid(
    repo: str,
    topic: str,
    injection_stamp: float | None,
) -> bool:
    """The restart authorization — the ONLY thing that may restart a session.

    True only when ALL hold:

    1. an injection stamp exists for this round (``injection_stamp`` is not None) —
       without a recorded injection there is no round to certify,
    2. the state file declares exactly ``ready``, AND
    3. its mtime is strictly newer than ``injection_stamp`` (this round, not a
       stale declaration from a prior wrap-up).

    The daemon NEVER infers readiness. A session that is merely idle — however long,
    however low on context — is NOT ready: "idle + settled" is not "safe to kill" (a
    session can be idle while a background build runs, while a sub-agent works, or
    while it waits on a human in another pane). Only the session knows, so only the
    session may say so. Any absent/unreadable/other-valued file → False (fail-closed).
    """
    if injection_stamp is None:
        return False
    state = read_state(repo, topic)
    if state is None or state.token != STATE_READY:
        return False
    return state.mtime > injection_stamp


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


def pane_is_codex(pane_current_command: str | None) -> bool:
    """True if ``#{pane_current_command}`` could be a Codex TUI.

    DELIBERATELY LOOSE, and safe only in combination. tmux reports a codex pane's
    foreground process as `bun` (the launcher; the vendored `codex` binary is its child),
    and `bun` matches ANY bun app — so this must NEVER gate anything on its own. Two
    callers, both safe: `_is_codex_track` pairs it with an exact live-session-map lookup
    (the map proves a real codex session for this topic is in this tmux; this proves the
    PANE is the codex one, not a Claude pane in the same session); and `_do_codex_restart`
    uses it only as the `_await_pane` predicate DIRECTLY AFTER it respawned `codex resume`
    into that exact pane — so "did the codex process come up?" is all it needs to answer,
    and the identity was already established before the restart.
    """
    cmd = (pane_current_command or "").strip().lower()
    return cmd in _CODEX_COMMANDS


_CODEX_COMMANDS = frozenset({"codex", "bun"})


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
