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
``/proc``, so nothing here opens one. Keep it that way: if a later need arises (e.g.
the ``token_count`` events that carry Ctx%), read only the specific metadata payloads
and never dump a body.

Stdlib-only, like every module in this folder. Every host coupling (``/proc`` reads)
is injected so the beside-tests run with no codex process and no real ``~/.codex``.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

# `proc_comm` is a GENERIC /proc reader that happens to live in `claude_sessions`,
# which already hosts the runtime-agnostic readers used for Codex (`has_active_subshell`
# — the Codex busy fallback — is built on them). Reusing it beats duplicating a reader
# into a sibling module.
from claude_sessions import proc_comm

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
            out.append(os.readlink(entry))
        except OSError:
            continue  # the fd closed underneath us; skip it
    return out


def proc_cwd(pid: int) -> str | None:
    """``/proc/<pid>/cwd`` resolved, or None if unreadable."""
    try:
        return os.readlink(f"/proc/{pid}/cwd")
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


def read_thread_names(codex_home: str | os.PathLike[str]) -> dict[str, str]:
    """``session_index.jsonl`` as ``{session id: thread_name}``.

    An APPEND log — a renamed thread appends a fresh record for the same id, so the
    LAST record wins. Fail-soft throughout: a missing file, an unparsable line, or a
    record missing a usable id/name is skipped, never raised.
    """
    out: dict[str, str] = {}
    try:
        raw = (Path(codex_home) / "session_index.jsonl").read_text(encoding="utf-8")
    except OSError:
        return out
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict):
            continue
        session_id, name = record.get("id"), record.get("thread_name")
        if isinstance(session_id, str) and isinstance(name, str) and session_id and name:
            out[session_id] = name  # last record for an id wins
    return out


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
