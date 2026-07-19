"""Live Codex TUI session discovery — the Codex twin of :mod:`claude_sessions`.

Codex sessions are invisible to the daemon: they are not in Claude's registry
(``~/.claude/sessions/<pid>.json``), so ``adopt_sessions`` cannot map a running Codex
session to its plan. This module supplies the missing join, in the same shape
``claude_sessions`` supplies for Claude — a list of live, NAMED sessions carrying
``pid`` / ``name`` (= the plan topic) / ``cwd`` — so adoption can treat the two
runtimes uniformly and ``claude_sessions.resolve_tmux_session`` (already
runtime-agnostic) joins either to its tmux session.

**The join, and why it is exact rather than a heuristic.** Codex keeps no pid-keyed
registry, which is why this looked hard. But a running codex process **holds its own
rollout file open**, and the rollout FILENAME embeds the session id, which
``session_index.jsonl`` maps to the ``thread_name`` — the plan topic::

    pid  --(comm == "codex")-->            a real Codex TUI process
    pid  --/proc/<pid>/fd/*-->             rollout-<ts>-<session id>.jsonl
    id   --session_index.jsonl-->          thread_name   == THE PLAN TOPIC
    pid  --/proc/<pid>/cwd-->              THE REPO

Verified end-to-end live (2026-07-16) against a real 2-day-old codex TUI: pid 1682090
→ ``rollout-2026-07-12T06-19-39-019f548d-….jsonl`` → cwd ``/data/projects/openbrain``.
See ``plan/overseer-rewrite/research/codex-ctx-and-restart-evidence.md``.

**The one real precondition: only NAMED sessions are indexed** — 67 of 259 rollouts,
live. An unnamed session carries no topic anywhere, so it cannot be joined to a plan
and is dropped. That is a naming convention to adopt, exactly as Claude adoption
depends on ``claude -n <topic>`` — not a defect and not a heuristic to invent around.

**Secrets caution — this module NEVER reads a rollout's contents.** Rollout ``.jsonl``
files are full session transcripts. The join needs only the FILENAME (for the id) and
``/proc``, so nothing here opens one. Keep it that way.

**Ctx% is deliberately NOT read here.** An earlier cut computed it from the rollout's
``token_count`` events and was WRONG by 2-4 points against Codex's own display, because
that reimplements codex-rs's occupancy formula (which subtracts a ~12k baseline and
excludes reasoning tokens from occupancy) — a private internal that can drift with any
Codex release. Codex renders ``Context N% left`` in its statusline; that is its OWN
number, and ``signals.parse_ctx_remaining`` reads it exactly as it reads Claude's
``Ctx: N% left``. Do not reintroduce a local occupancy formula.

Stdlib-only, like every module in this folder. Every host coupling (``/proc`` reads)
is injected so the beside-tests run with no codex process and no real ``~/.codex``.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import jsonio

# `proc_comm` is a GENERIC /proc reader that happens to live in `claude_sessions`,
# which already hosts the runtime-agnostic readers used for Codex (`has_active_subshell`
# — the Codex busy fallback — is built on them). Reusing it beats duplicating a reader
# into a sibling module.
from claude_sessions import proc_comm, proc_ppid, resolve_tmux_session

# `#{pane_current_command}` / `/proc/<pid>/comm` for a real Codex TUI. The launcher is
# `bun` (`~/.bun/bin/codex`), which EXECS the vendored binary; verified live, the `bun`
# process is the codex process's PARENT and holds NO rollout fd, so requiring an open
# rollout (below) excludes it structurally — this name matches only the real thing.
CODEX_COMM = "codex"

# `rollout-<iso-ts>-<uuid>.jsonl`. Anchored on the trailing uuid + extension so a
# rollout is never confused with a sibling file in the same tree.
_ROLLOUT_RE = re.compile(
    r"rollout-.*-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.jsonl$"
)


@dataclass(frozen=True, kw_only=True)
class CodexSession:
    """One live, NAMED Codex TUI session, joined to its plan topic.

    Mirrors :class:`claude_sessions.ClaudeSession` field-for-field where the two
    runtimes agree, so adoption can consume either. ``name`` is the index
    ``thread_name`` and carries the same meaning as Claude's registry ``name``: the
    plan topic. There is no ``status`` twin — Codex self-reports nothing, so busy
    detection falls back to the process-tree shell-walk
    (``claude_sessions.has_active_subshell``), which exists for exactly this case.
    """

    pid: int
    name: str
    cwd: str
    session_id: str


def default_codex_home() -> Path:
    """``~/.codex`` — where Codex writes ``session_index.jsonl`` and ``sessions/``."""
    return Path.home() / ".codex"


# --------------------------------------------------------------------------- #
# Host couplings: /proc readers. Injected into the pure join below.
# --------------------------------------------------------------------------- #


def proc_fd_targets(pid: int) -> list[str]:
    """Every open fd's target path for ``pid`` — fail-soft to [] (dead pid / EPERM)."""
    out: list[str] = []
    try:
        entries = list(Path(f"/proc/{pid}/fd").iterdir())
    except OSError:
        return out
    for entry in entries:
        try:
            out.append(str(entry.readlink()))
        except OSError:
            continue  # the fd closed underneath us; skip it
    return out


def proc_cwd(pid: int) -> str | None:
    """``/proc/<pid>/cwd`` resolved, or None if unreadable."""
    try:
        return str(Path(f"/proc/{pid}/cwd").readlink())
    except OSError:
        return None


def proc_pids_of_comm(comm: str) -> list[int]:
    """Every live pid whose ``/proc/<pid>/comm`` equals ``comm`` — fail-soft to []."""
    out: list[int] = []
    try:
        entries = list(Path("/proc").iterdir())
    except OSError:
        return out
    for entry in entries:
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if proc_comm(pid) == comm:
            out.append(pid)
    return sorted(out)


# --------------------------------------------------------------------------- #
# Pure readers + the join.
# --------------------------------------------------------------------------- #


def rollout_id(path: str) -> str | None:
    """The session id embedded in a rollout FILENAME, or None if not a rollout."""
    match = _ROLLOUT_RE.search(path or "")
    return match.group(1) if match else None


def open_rollout_id(
    pid: int, *, fd_targets_of: Callable[[int], list[str]] = proc_fd_targets
) -> str | None:
    """The session id of the rollout ``pid`` holds OPEN, or None if it holds none.

    This is the pid→session link Codex otherwise lacks. A codex process keeps its own
    rollout open for the session's whole life, so the fd table is an exact, live
    pid→session id map — no cwd+recency guessing.
    """
    for target in fd_targets_of(pid):
        found = rollout_id(target)
        if found is not None:
            return found
    return None


def _read_index_final(codex_home: str | os.PathLike[str]) -> dict[str, tuple[str, str]]:
    """``session_index.jsonl`` folded to ``{session id: (thread_name, updated_at)}``.

    The index is an APPEND log — a renamed thread appends a fresh record for the SAME id, so
    the LAST record for an id gives its final ``thread_name`` + ``updated_at`` (``""`` when
    the field is missing). The one, shared parser behind :func:`read_thread_names` (adoption)
    and :func:`latest_session_for_thread_name` (reboot recovery) so the two cannot drift.
    Fail-soft throughout: a missing file, an unparsable line, or a record missing a usable
    id/name is skipped, never raised.
    """
    out: dict[str, tuple[str, str]] = {}
    try:
        raw = (Path(codex_home) / "session_index.jsonl").read_text(encoding="utf-8")
    except OSError:
        return out
    for line in raw.splitlines():
        record = jsonio.parse_object_line(line)
        if record is None:
            continue
        session_id, name = record.get("id"), record.get("thread_name")
        updated = record.get("updated_at")
        if isinstance(session_id, str) and isinstance(name, str) and session_id and name:
            out[session_id] = (name, updated if isinstance(updated, str) else "")
    return out


def read_thread_names(codex_home: str | os.PathLike[str]) -> dict[str, str]:
    """``session_index.jsonl`` as ``{session id: thread_name}`` (last record per id wins)."""
    return {sid: name for sid, (name, _updated) in _read_index_final(codex_home).items()}


def latest_session_for_thread_name(
    thread_name: str, *, codex_home: str | os.PathLike[str] | None = None
) -> str | None:
    """The session id of the most-recently-updated indexed session named ``thread_name``.

    Reverses ``session_index.jsonl`` — which SURVIVES the session's death, unlike the live
    rollout fd a running codex holds open — so reboot recovery can learn a DEAD codex track's
    session id from its plan topic (the ``thread_name``). Among ids whose final name matches,
    the one with the greatest ``updated_at`` wins (RFC3339 UTC strings, lexicographically
    ordered, and distinct per id in real index data — verified live 2026-07-18, so the pick is
    unambiguous). Returns None when the topic names no indexed session — the caller treats such
    a track as Claude. Fail-soft: a missing/unreadable index yields None.
    """
    home = Path(codex_home) if codex_home is not None else default_codex_home()
    matches = [
        (updated, sid)
        for sid, (name, updated) in _read_index_final(home).items()
        if name == thread_name
    ]
    return max(matches)[1] if matches else None


def rollout_exists(session_id: str, *, codex_home: str | os.PathLike[str] | None = None) -> bool:
    """True if a rollout file for ``session_id`` still exists under ``<codex_home>/sessions``.

    A rollout is ``rollout-<iso-ts>-<session id>.jsonl``, nested under ``sessions/YYYY/MM/DD/``
    (verified live). A dead session's rollout persists on disk, and its presence is what
    ``codex resume`` needs to reattach — so reboot recovery gates option (c) on it: rollout
    present ⇒ ``codex resume <id>`` can reattach the SAME conversation; rollout gone ⇒ recovery
    falls back to skip+surface (option b) rather than mis-recreating the track as Claude
    (which would orphan the rollout). The ``session_id`` is a UUID (no glob metacharacters), so
    it is safe to interpolate into the pattern. Fail-soft to False.
    """
    sessions = (Path(codex_home) if codex_home is not None else default_codex_home()) / "sessions"
    try:
        return any(sessions.rglob(f"rollout-*-{session_id}.jsonl"))
    except OSError:
        return False


def read_live_codex_sessions(
    *,
    codex_home: str | os.PathLike[str] | None = None,
    pids_of_comm: Callable[[str], list[int]] = proc_pids_of_comm,
    cwd_of: Callable[[int], str | None] = proc_cwd,
    fd_targets_of: Callable[[int], list[str]] = proc_fd_targets,
) -> list[CodexSession]:
    """Every live, NAMED Codex TUI session, joined to its topic + repo.

    Liveness is structural: the pid came from a ``/proc`` scan this instant and must
    still hold an open rollout and a readable cwd — so there is no stale-file problem
    to defeat (Claude's registry needs a ``procStart`` check precisely because its
    files outlive their process; a rollout fd cannot).

    Skips, all deliberate and all fail-soft:

    - not ``comm == codex`` — including the ``bun`` launcher (holds no rollout anyway);
    - holds no open rollout — cannot be joined to a session id;
    - **its id is not in the index** — an UNNAMED session, which carries no topic
      anywhere and so cannot belong to a plan;
    - no readable cwd — the pid vanished mid-read.

    ``Codex Companion Task: …`` threads are deliberately NOT filtered here: they fail
    the "is this an ACTIVE plan topic?" test at adoption, so the noise filters itself
    and this stays a pure, dumb join with no policy in it.
    """
    home = Path(codex_home) if codex_home is not None else default_codex_home()
    names = read_thread_names(home)
    out: list[CodexSession] = []
    for pid in pids_of_comm(CODEX_COMM):
        session_id = open_rollout_id(pid, fd_targets_of=fd_targets_of)
        if session_id is None:
            continue
        name = names.get(session_id)
        if not name:
            continue  # unnamed → no topic → not joinable to a plan
        cwd = cwd_of(pid)
        if not cwd:
            continue
        out.append(CodexSession(pid=pid, name=name, cwd=cwd, session_id=session_id))
    return out


def map_codex_sessions(
    pane_pid_to_session: dict[int, str],
    *,
    codex_home: str | os.PathLike[str] | None = None,
    ppid_of: Callable[[int], int | None] = proc_ppid,
    pids_of_comm: Callable[[str], list[int]] = proc_pids_of_comm,
    cwd_of: Callable[[int], str | None] = proc_cwd,
    fd_targets_of: Callable[[int], list[str]] = proc_fd_targets,
) -> list[tuple[str, str, str]]:
    """``[(tmux_session, name, cwd)]`` for every live NAMED codex session held in tmux.

    The exact twin of :func:`claude_sessions.map_named_sessions`, emitting the SAME
    triple on purpose: ``adopt`` can then consume either runtime through ONE code path
    instead of growing a parallel Codex branch that could drift from the Claude one.

    Composes :func:`read_live_codex_sessions` with
    :func:`claude_sessions.resolve_tmux_session` — which is already runtime-agnostic
    (it walks a pid up to a tmux pane pid and cares nothing for what the process is),
    so Codex needs no tmux-joining code of its own. A live session not inside any tmux
    pane is omitted: there is no pane to capture, inject, or respawn. Order follows the
    ``/proc`` pid scan, so the mapping is deterministic.
    """
    mapped: list[tuple[str, str, str]] = []
    for session in read_live_codex_sessions(
        codex_home=codex_home,
        pids_of_comm=pids_of_comm,
        cwd_of=cwd_of,
        fd_targets_of=fd_targets_of,
    ):
        tmux_session = resolve_tmux_session(
            session.pid, pane_pid_to_session=pane_pid_to_session, ppid_of=ppid_of
        )
        if tmux_session is None:
            continue
        mapped.append((tmux_session, session.name, session.cwd))
    return mapped


def codex_by_tmux_session(
    pane_pid_to_session: dict[int, str],
    *,
    codex_home: str | os.PathLike[str] | None = None,
    ppid_of: Callable[[int], int | None] = proc_ppid,
    pids_of_comm: Callable[[str], list[int]] = proc_pids_of_comm,
    cwd_of: Callable[[int], str | None] = proc_cwd,
    fd_targets_of: Callable[[int], list[str]] = proc_fd_targets,
) -> dict[tuple[str, str], CodexSession]:
    """``{(tmux_session, name): CodexSession}`` for every live NAMED codex session in tmux.

    The twin of :func:`claude_sessions.status_by_tmux_session`, and the per-tick map the
    supervisor keys Codex behavior off — recomputed every tick like ``_claude_status``,
    so it is always live and self-correcting.

    **Why a map and not a pane-command predicate.** tmux reports a codex pane's
    ``#{pane_current_command}`` as **`bun`**, NOT `codex`: the pane's foreground process
    is the `bun` launcher and the vendored codex binary is its CHILD (verified live). And
    `bun` is generic — ANY bun app would match it. So "is this pane Codex?" cannot be
    answered honestly from the pane command. Membership in THIS map answers it exactly:
    the session is in it only because a real codex process, holding a real rollout,
    resolved to that tmux session this tick. It also needs no stored ``runtime`` field on
    the mapping (nothing to migrate, nothing to drift).

    **Keyed by ``(tmux_session, name)``, not ``tmux_session`` alone.** Two codex sessions
    can share ONE tmux session — a second split, or a ``codex resume <topic>`` spawned
    from another session's Bash tool — each carrying a DIFFERENT ``name`` (= its plan
    topic). A single value per tmux session would let the second SHADOW the first, so that
    track silently loses its ctx reading, its wrap-up, and its restart — invisible in the
    table. Keying by the ``(tmux_session, name)`` pair keeps BOTH, so the supervisor's
    ``_is_codex_track`` / ``_do_codex_restart`` resolve each track to ITS OWN session by
    ``(tmux, topic)``. This is the codex analogue of the set-valued
    :func:`claude_sessions.names_by_tmux_session` (R2 review SF5). Only a genuine
    same-``(tmux, name)`` collision — two codex processes for the SAME topic in the SAME
    tmux session — keeps the FIRST by pid order (deterministic; the daemon drives one
    session per pane anyway).
    """
    by_key: dict[tuple[str, str], CodexSession] = {}
    for session in read_live_codex_sessions(
        codex_home=codex_home,
        pids_of_comm=pids_of_comm,
        cwd_of=cwd_of,
        fd_targets_of=fd_targets_of,
    ):
        tmux_session = resolve_tmux_session(
            session.pid, pane_pid_to_session=pane_pid_to_session, ppid_of=ppid_of
        )
        if tmux_session is None:
            continue
        key = (tmux_session, session.name)
        if key in by_key:
            continue
        by_key[key] = session
    return by_key
