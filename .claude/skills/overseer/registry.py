"""registry.py — overseer mapping store + discovery ⋈ mapping join.

Pure-logic, stdlib-only. Host-only tooling under ``.claude/skills/overseer/``:
LOCAL-ONLY and unsynced, but no longer outside the product gates — the folder's
beside-tests and ruff both gate it (``just check-overseer`` / ``just
check-lint``). It remains outside pyright.include, coverage, and import-linter;
those are tracked separately in ``plan/overseer-productization/``. See
``design.md`` beside this file.

Vocabulary (see design.md, the discovery-join model):
  - A "track" is one plan topic in one repo the overseer watches this run.
  - "discovery" = scan each watched repo's ``plan/*/`` for a ``handoff.md``.
  - "mapping"   = the durable topic↔tmux rows in ``~/.livespec-overseer.jsonl``,
    which hold ONLY facts that cannot be rederived from the filesystem
    (pinned session id, custom resume line, threshold override).
  - the displayed list = discovery LEFT-JOIN mapping.

The tmux session name is the BARE plan ``<topic>`` (maintainer-declared 2026-07-19);
it is repo-qualified as ``<repo-slug>-<topic>`` (single dash) ONLY when that topic
collides across watched repos, because tmux session names are GLOBAL while plan topics
are only unique per repo (adversarial-review blocker #8). See :func:`tmux_id` /
:func:`colliding_topics`.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import re
import tempfile
from collections.abc import Callable, Collection, Iterable, Iterator
from dataclasses import dataclass, replace
from pathlib import Path

import jsonio
import streams

__all__ = [
    "DEFAULT_CTX_THRESHOLD",
    "DEFAULT_STAMP_PATH",
    "DEFAULT_STORE_PATH",
    "DEFAULT_WATCH_SET_PATH",
    "Track",
    "add_notified_band",
    "append_mapping",
    "archived_or_gone",
    "clear_injection_stamp",
    "colliding_topics",
    "discover_plans",
    "join",
    "read_injection_stamp",
    "read_mapping",
    "read_notified_bands",
    "read_resume_pending",
    "remove_mapping",
    "repo_root_present",
    "repo_slug",
    "repoint_tmux",
    "rewrite_mapping",
    "set_resume_pending",
    "tmux_id",
    "watch_set_from_config",
    "write_injection_stamp",
]


@contextlib.contextmanager
def _file_lock(target: str | os.PathLike[str]) -> Iterator[None]:
    """Hold an exclusive advisory lock spanning a read-modify-write of ``target``.

    The mapping store and the injection-stamp sidecar are read-modify-written by
    the daemon AND — per the shipped two-pane topology — the bottom-pane CLI
    (`add`/`remove`/`start`) at the same time; without a lock an interleaving
    silently drops a freshly-added live row or a pending track's stamp
    (adversarial code review 2026-07-13, blocker B6). A ``<target>.lock`` sidecar
    is flock'd LOCK_EX for the whole critical section. Fail-soft: if the lock file
    cannot be created/locked (e.g. an unwritable dir), proceed unlocked rather
    than crash — losing the race is better than losing the daemon.
    """
    lock_path = Path(str(target) + ".lock")
    handle = None
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = lock_path.open("w", encoding="utf-8")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    except OSError as exc:
        _warn(f"could not acquire lock {lock_path}: {exc}; proceeding unlocked")
        if handle is not None:
            handle.close()
            handle = None
    try:
        yield
    finally:
        if handle is not None:
            with contextlib.suppress(OSError):
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()


# The default remaining-context threshold (percent LEFT) at which the first
# wrap-up is injected. Overridable per-daemon via `overseerd --warn-percent` and
# per-track via a mapping-store override.
DEFAULT_CTX_THRESHOLD = 50

# The durable mapping store and the injection-stamp sidecar both live beside
# the maintainer's home dir (NOT inside any governed repo — the single
# `.overseer-state` file, under the repo's gitignored `tmp/`, is the only overseer
# state that lives inside a governed repo). Both paths are parameterizable so tests can point
# them at a tmp_path.
DEFAULT_STORE_PATH = Path.home() / ".livespec-overseer.jsonl"
DEFAULT_STAMP_PATH = Path.home() / ".livespec-overseer-stamps.json"
# The watch-set declaration: which repo checkouts this host supervises. It sits
# beside the two sidecars above for one reason beyond tidiness — it is what lets
# a relocated overseer learn its watch-set WITHOUT reading
# `.livespec-fleet-manifest.jsonc`, which decision D5 forbids a shipped overseer
# from depending on (that manifest is fleet self-application infrastructure, not
# a contract a governed consumer inherits). Keeping the declaration in `$HOME`
# also keeps the daemon's invocation surface knob-free, honoring the deliberate
# de-gold-plating that removed `--repos` / `--manifest` / `--store` / `--stamp`.
DEFAULT_WATCH_SET_PATH = Path.home() / ".livespec-overseer-repos.json"

# The durable keys serialized to a mapping row. `added_at` is written on append
# but is not a Track field (it is bookkeeping only).
_ROW_KEYS = (
    "topic",
    "repo",
    "tmux",
    "handoff",
    "resume",
    "epic",
    "ctx_threshold",
    "pinned_session_id",
)


def _warn(message: str) -> None:
    """Emit a fail-soft diagnostic to stderr (never crash the caller)."""
    streams.write_stderr(text=f"overseer.registry: {message}\n")


def _norm(repo: str | os.PathLike[str]) -> str:
    """Normalize a repo path for join/index keys (no filesystem access).

    ``os.path.normpath`` collapses ``..`` and trailing slashes and does NOT
    follow symlinks, so it is a pure, deterministic key derivation. Both sides
    of the discovery ⋈ mapping join must normalize identically or the join
    silently drops rows.
    """
    return os.path.normpath(str(repo))


def repo_slug(repo: str | os.PathLike[str]) -> str:
    """The repo-slug used to repo-qualify a tmux session id — the basename."""
    return Path(repo).name


def colliding_topics(
    discovered: Iterable[tuple[str, str, str]],
) -> frozenset[str]:
    """Topics that appear in >=2 DISTINCT watched repos.

    ``discovered`` is the ``(repo, topic, handoff)`` triple list from
    :func:`discover_plans`. A topic in this set would collide on its bare tmux
    name if two of its repos ran at once (tmux session names are global), so
    :func:`tmux_id` repo-qualifies exactly these — and nothing else. Repos are
    de-duplicated via :func:`_norm` (the same key both sides of the join use), so
    the SAME repo discovered twice never counts as a collision.
    """
    repos_by_topic: dict[str, set[str]] = {}
    for repo, topic, _ in discovered:
        repos_by_topic.setdefault(topic, set()).add(_norm(repo))
    return frozenset(t for t, repos in repos_by_topic.items() if len(repos) > 1)


def tmux_id(
    repo: str | os.PathLike[str],
    topic: str,
    colliding: Collection[str] = frozenset(),
) -> str:
    """The tmux session name for a plan ``topic``.

    Default is the **bare plan topic** (maintainer-declared 2026-07-19): a session
    is named after the plan topic the operator reads and navigates by, NOT
    repo-qualified. A repo prefix is added ONLY on a real cross-repo collision —
    when the SAME topic exists in more than one watched repo (``topic in
    colliding``) — as ``<repo-slug>-<topic>`` with a **single** dash. tmux session
    names are global, so two live sessions cannot both be named ``<topic>``; the
    single-dash prefix disambiguates exactly those clashes and nothing else.

    ``colliding`` is the set of topics appearing in >=2 watched repos, from
    :func:`colliding_topics` over the discovery set. The default (empty) means "no
    known collisions" and yields the bare topic; a caller holding the discovery
    set SHOULD pass the real collision set so a genuine clash is prefixed.

    Both forms are tmux-legal and round-trip: the separator is ``-`` (NOT ``:`` or
    ``.``, which tmux ≥3.3 SANITIZES to ``_`` in a ``new-session -s`` name, breaking
    ``-t`` lookup — adversarial code review blocker B1, 2026-07-13). A plan topic
    itself may contain dashes (e.g. ``autonomous-mode``); that is fine, a dash is
    never sanitized. The predecessor ``<repo-slug>--<topic>`` (double-dash, ALWAYS
    prefixed) form is retired.
    """
    if topic in colliding:
        return f"{repo_slug(repo)}-{topic}"
    return topic


@dataclass(frozen=True, kw_only=True)
class Track:
    """One overseer row: a plan topic in a repo, possibly mapped to a session.

    Frozen + keyword-only. A *mapped* track (``assigned=True``) carries the
    durable facts from a ``~/.livespec-overseer.jsonl`` row. An *unassigned*
    track (``assigned=False``, blank ``tmux``) is a discovered plan with no
    mapping row — build it via :meth:`make_unassigned`.
    """

    topic: str
    repo: str
    tmux: str | None = None
    handoff: str | None = None
    resume: str | None = None
    epic: str | None = None
    # None = NO per-track override → inherit the daemon-wide default warn
    # threshold (``Supervisor.warn_percent``, itself defaulting to
    # ``DEFAULT_CTX_THRESHOLD``). An int is an explicit per-track override that
    # wins over the daemon default. Serialized only when set (the row omits the
    # key when None) so a bare row means "no override".
    ctx_threshold: int | None = None
    pinned_session_id: str | None = None
    assigned: bool = True

    @property
    def is_unassigned(self) -> bool:
        return not self.assigned

    @classmethod
    def make_unassigned(
        cls,
        *,
        repo: str,
        topic: str,
        handoff: str | None = None,
    ) -> Track:
        """A discovered-but-unmapped track: blank tmux, status `unassigned`."""
        return cls(
            topic=topic,
            repo=repo,
            tmux=None,
            handoff=handoff,
            assigned=False,
        )


# --------------------------------------------------------------------------- #
# Mapping store: read / append / remove-by-(repo,topic) / rewrite-filter.
# JSONL = one JSON object per line. Fail SOFT on a malformed line.
# --------------------------------------------------------------------------- #


def _store(store_path: str | os.PathLike[str] | None) -> Path:
    return Path(store_path) if store_path is not None else DEFAULT_STORE_PATH


def _read_rows(store_path: str | os.PathLike[str] | None = None) -> list[dict[str, object]]:
    """Read the mapping store as raw dicts, skipping (and naming) bad lines.

    Operating on raw dicts (not Tracks) for rewrite/remove preserves unknown
    keys such as ``added_at`` on the surviving rows.
    """
    path = _store(store_path)
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:  # PermissionError, NFS hiccup, mid-move — fail-soft (B7)
        _warn(f"unreadable mapping store {path}: {exc}")
        return []
    rows: list[dict[str, object]] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            _warn(f"skipping malformed line {lineno} in {path}: {exc}")
            continue
        record = jsonio.as_object(obj)
        if record is None:
            _warn(f"skipping non-object line {lineno} in {path}")
            continue
        rows.append(record)
    return rows


def _atomic_write(path: Path, body: str) -> None:
    """Write ``body`` to ``path`` atomically: temp file in the same dir + os.replace.

    A bare truncate-then-write (the old ``path.write_text``) leaves a
    truncated/partial store if the process dies mid-write — and this store is
    rewritten every ~10s tick, so that window recurs constantly (adversarial code
    review 2026-07-13, blocker B6). ``os.replace`` is atomic on POSIX, so a reader
    always sees either the old or the new complete file, never a partial one.
    Fail-soft: an OSError is warned, not raised (B7).
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                _ = handle.write(body)
                handle.flush()
                os.fsync(handle.fileno())
            _ = Path(tmp_name).replace(path)
        except OSError:
            with contextlib.suppress(OSError):
                Path(tmp_name).unlink()
            raise
    except OSError as exc:
        _warn(f"could not write {path}: {exc}")


def _write_rows(
    rows: Iterable[dict[str, object]],
    store_path: str | os.PathLike[str] | None = None,
) -> None:
    body = "".join(json.dumps(row) + "\n" for row in rows)
    _atomic_write(_store(store_path), body)


def _track_from_row(row: dict[str, object]) -> Track | None:
    """Build a mapped Track from a raw row, or None (naming the offender)."""
    topic = row.get("topic")
    repo = row.get("repo")
    if not isinstance(topic, str) or not isinstance(repo, str):
        _warn(f"skipping row missing topic/repo: {row!r}")
        return None
    # A per-track override is present ONLY if the row carries an int
    # ``ctx_threshold``; a missing (or non-int) value means "no override" → None,
    # so the daemon-wide default applies. Do NOT default to DEFAULT_CTX_THRESHOLD
    # at read time — that would make a bare row indistinguishable from a row that
    # pinned the current default, defeating the daemon-wide ``--warn-percent``.
    threshold = row.get("ctx_threshold")
    ctx_threshold = threshold if isinstance(threshold, int) else None

    def _opt_str(key: str) -> str | None:
        value = row.get(key)
        return value if isinstance(value, str) else None

    return Track(
        topic=topic,
        repo=repo,
        tmux=_opt_str("tmux"),
        handoff=_opt_str("handoff"),
        resume=_opt_str("resume"),
        epic=_opt_str("epic"),
        ctx_threshold=ctx_threshold,
        pinned_session_id=_opt_str("pinned_session_id"),
        assigned=True,
    )


def read_mapping(store_path: str | os.PathLike[str] | None = None) -> list[Track]:
    """Read the mapping store into typed Tracks (fail-soft on bad rows)."""
    tracks: list[Track] = []
    for row in _read_rows(store_path):
        track = _track_from_row(row)
        if track is not None:
            tracks.append(track)
    return tracks


def _track_to_row(track: Track) -> dict[str, object]:
    row: dict[str, object] = {
        "topic": track.topic,
        "repo": track.repo,
        "tmux": track.tmux,
        "handoff": track.handoff,
        "resume": track.resume,
        "epic": track.epic,
        "pinned_session_id": track.pinned_session_id,
    }
    # OMIT ``ctx_threshold`` when there is no per-track override (None): a row
    # WITHOUT the key means "inherit the daemon default"; include it only for an
    # explicit int override.
    if track.ctx_threshold is not None:
        row["ctx_threshold"] = track.ctx_threshold
    return row


def append_mapping(
    track: Track,
    store_path: str | os.PathLike[str] | None = None,
    *,
    added_at: str | None = None,
) -> None:
    """Append one mapping row (durable keys + optional ``added_at`` stamp).

    Under a store lock so a concurrent :func:`rewrite_mapping` cannot read a
    snapshot that predates this append and write it back, silently dropping the
    freshly-added live row (B6). Fail-soft on an OSError (B7).
    """
    path = _store(store_path)
    row = _track_to_row(track)
    if added_at is not None:
        row["added_at"] = added_at
    with _file_lock(path):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                _ = handle.write(json.dumps(row) + "\n")
        except OSError as exc:
            _warn(f"could not append to {path}: {exc}")


def rewrite_mapping(
    keep: Callable[[dict[str, object]], bool],
    store_path: str | os.PathLike[str] | None = None,
) -> int:
    """Rewrite the store keeping only rows where ``keep(row)`` is true.

    Returns the number of rows dropped. Operates on raw dicts so unknown keys
    survive. The daemon's archive-GC uses this with a predicate built from
    :func:`archived_or_gone`. Held under a store lock so the read-modify-write is
    atomic against a concurrent append (B6); SKIPS the write entirely when no row
    is dropped, so a steady-state tick does not rewrite (and risk truncating) the
    store on every pass.
    """
    with _file_lock(_store(store_path)):
        rows = _read_rows(store_path)
        kept = [row for row in rows if keep(row)]
        if len(kept) != len(rows):
            _write_rows(kept, store_path)
        return len(rows) - len(kept)


def remove_mapping(
    repo: str,
    topic: str,
    store_path: str | os.PathLike[str] | None = None,
) -> int:
    """Remove the mapping row(s) matching ``(repo, topic)``; return the count."""
    norm = _norm(repo)

    def _keep(row: dict[str, object]) -> bool:
        row_repo = row.get("repo")
        return not (
            isinstance(row_repo, str) and _norm(row_repo) == norm and row.get("topic") == topic
        )

    return rewrite_mapping(_keep, store_path)


def repoint_tmux(
    repo: str,
    topic: str,
    new_tmux: str,
    store_path: str | os.PathLike[str] | None = None,
) -> bool:
    """Rewrite the ``(repo, topic)`` mapping row's ``tmux`` field to ``new_tmux``.

    The daemon uses this to RE-POINT a stale mapping: a topic's live named session that
    moved to a DIFFERENT tmux session than the store records (generic reused windows
    ``livespec1``… drift across topics), so the frozen binding would otherwise let an act
    target the wrong pane (R2, 2026-07-18). Operates on raw dicts under the store lock so
    unknown keys (``added_at``) survive and a concurrent append cannot clobber the update.

    Idempotent: returns False and SKIPS the write when no matching row needs changing (the
    stored ``tmux`` already equals ``new_tmux``, or there is no such row), so a steady-state
    tick where nothing moved never rewrites (and never risks truncating) the store. Returns
    True when at least one row was re-pointed. Fail-soft on OSError (inherited from
    :func:`_write_rows`).
    """
    norm = _norm(repo)
    with _file_lock(_store(store_path)):
        rows = _read_rows(store_path)
        changed = False
        for row in rows:
            row_repo = row.get("repo")
            if (
                isinstance(row_repo, str)
                and _norm(row_repo) == norm
                and row.get("topic") == topic
                and row.get("tmux") != new_tmux
            ):
                row["tmux"] = new_tmux
                changed = True
        if changed:
            _write_rows(rows, store_path)
        return changed


# --------------------------------------------------------------------------- #
# Discovery, join, watch-set, archive-GC.
# --------------------------------------------------------------------------- #


def discover_plans(
    watch_repos: Iterable[str | os.PathLike[str]],
) -> list[tuple[str, str, str]]:
    """Enumerate each watched repo's ``plan/*/`` DIRECTORIES (a track per dir).

    Returns ``(repo, topic, abs-handoff-path)`` triples, sorted for
    determinism. Discovery keys on the ``plan/<topic>/`` DIRECTORY existing — it
    does NOT read or stat any FILE inside it, because the overseer never touches
    a session's ``plan/`` files (the handoff and its contents are the session's
    own workflow). The returned handoff path (``plan/<topic>/handoff.md``) is a
    CONVENTIONAL pointer the resume line hands to the session; the overseer never
    opens it. Excludes ``plan/archive/**`` (only direct children of ``plan/`` are
    considered, and the literal ``archive`` dir is skipped).
    Fail-soft: a repo with no ``plan/`` dir contributes nothing, and an OSError
    on ONE repo (a ``plan/`` that becomes unreadable between the ``is_dir`` check
    and ``iterdir`` — chmod, NFS hiccup, mid-clone) is warned and skipped rather
    than propagated out to crash the daemon that supervises ALL tracks
    (adversarial code review 2026-07-13, blocker B7).
    """
    triples: list[tuple[str, str, str]] = []
    for repo in watch_repos:
        repo_norm = _norm(repo)
        plan_dir = Path(repo_norm) / "plan"
        try:
            if not plan_dir.is_dir():
                continue
            children = list(plan_dir.iterdir())
        except OSError as exc:
            _warn(f"unreadable plan dir {plan_dir}: {exc}")
            continue
        for child in children:
            try:
                if not child.is_dir() or child.name == "archive":
                    continue
                # Directory existence IS the track; the handoff path is only a
                # conventional pointer for the resume line (never opened here).
                handoff = child / "handoff.md"
                triples.append((repo_norm, child.name, str(handoff)))
            except OSError as exc:
                _warn(f"unreadable plan child {child}: {exc}")
                continue
    triples.sort(key=lambda t: (t[0], t[1]))
    return triples


def join(
    discovered: Iterable[tuple[str, str, str]],
    mapping: Iterable[Track],
) -> list[Track]:
    """LEFT JOIN discovered plans with mapping rows on ``(repo, topic)``.

    Discovery is the left side: one Track per discovered triple. A discovered
    plan with a mapping row yields the mapped Track (its ``handoff`` filled from
    discovery if the row lacked one); a discovered-but-unmapped plan yields an
    ``unassigned`` Track. Mapping rows with no discovered plan do NOT appear
    here — those are dropped by the daemon's archive-GC, not the join.
    """
    index: dict[tuple[str, str], Track] = {}
    for track in mapping:
        index[(_norm(track.repo), track.topic)] = track

    result: list[Track] = []
    for repo, topic, handoff in discovered:
        mapped = index.get((_norm(repo), topic))
        if mapped is None:
            result.append(Track.make_unassigned(repo=repo, topic=topic, handoff=handoff))
        elif mapped.handoff:
            result.append(mapped)
        else:
            result.append(replace(mapped, handoff=handoff))
    result.sort(key=lambda t: (_norm(t.repo), t.topic))
    return result


def _scan_string_literal(text: str, start: int) -> int:
    """Index just past the JSON string literal opening at ``start``.

    ``text[start]`` is the opening quote. Backslash escapes are honored, so an
    escaped quote does not end the literal. An UNTERMINATED literal consumes to
    the end of the input rather than raising: this is a comment stripper, not a
    validator, and reporting malformed JSON is :func:`json.loads`'s job.
    """
    n = len(text)
    i = start + 1
    escape = False
    while i < n:
        ch = text[i]
        if escape:
            escape = False
        elif ch == "\\":
            escape = True
        elif ch == '"':
            return i + 1
        i += 1
    return n


def _scan_line_comment(text: str, start: int) -> int:
    """Index of the newline ending the ``//`` comment at ``start``.

    The newline itself is NOT consumed, so stripping preserves line structure
    (and therefore the line numbers in any downstream parse error).
    """
    end = text.find("\n", start)
    return len(text) if end == -1 else end


def _scan_block_comment(text: str, start: int) -> int:
    """Index just past the ``/* */`` comment opening at ``start``.

    An unterminated block comment consumes to the end of the input, matching
    :func:`_scan_string_literal`'s fail-soft posture.
    """
    end = text.find("*/", start + 2)
    return len(text) if end == -1 else end + 2


def _strip_jsonc_comments(text: str) -> str:
    """Strip ``//`` line and ``/* */`` block comments, string-literal-aware.

    A hand-rolled scanner (not a regex) so a ``//`` or ``/*`` inside a JSON
    string value is preserved. Avoids adding a JSONC/TOML/YAML dependency.

    Each ``_scan_*`` helper takes the index where its construct begins and
    returns the index just past it, so this loop stays a flat dispatch over
    "what starts here?" rather than an interleaved multi-flag state machine.
    """
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '"':
            end = _scan_string_literal(text, i)
            out.append(text[i:end])
            i = end
        elif text.startswith("//", i):
            i = _scan_line_comment(text, i)
        elif text.startswith("/*", i):
            i = _scan_block_comment(text, i)
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _parse_jsonc(text: str) -> object:
    stripped = _strip_jsonc_comments(text)
    # Tolerate trailing commas before a closing brace/bracket (common in JSONC).
    stripped = re.sub(r",(\s*[}\]])", r"\1", stripped)
    return json.loads(stripped)


def watch_set_from_config(
    config_path: str | os.PathLike[str],
    extra_repos: Iterable[str | os.PathLike[str]] = (),
) -> list[str]:
    """Compute the watch-set from the ``$HOME`` declaration rather than a manifest.

    This is the manifest-free counterpart to :func:`watch_set`, and it is what
    makes the overseer relocatable: :func:`watch_set` seeds from
    ``.livespec-fleet-manifest.jsonc`` resolved by walking UP from this file,
    which breaks the moment the package moves out of ``<core>/.claude/skills/``.
    Reading an absolute ``$HOME`` path instead is position-independent, and it
    drops the manifest dependency D5 forbids a shipped overseer from carrying.

    The document is ``{"repos": ["<checkout>", ...]}``, parsed as JSONC rather
    than strict JSON: this is a HAND-EDITED operator file, so ``//`` comments
    beside an entry ("paused while the migration lands") are worth more than
    format purity, and the repo already carries the lenient parser.

    Each entry is included only if the checkout exists AND has a ``plan/`` dir —
    the SAME admission rule the superseded manifest seeding applied, so
    relocating does not quietly widen or narrow what gets supervised.

    Listing a repo that has no assigned track yet is the POINT, not an edge
    case: discovery has to scan repos with zero mapping rows in order to surface
    their unassigned plans at all. That is why the watch-set cannot be derived
    from the mapping store's own rows — doing so would make a brand-new plan
    invisible until someone had already assigned it.

    Fail-soft in the same shape as the rest of this module: an absent,
    unreadable, or malformed declaration warns and yields just the ``extra_repos``,
    rather than taking the daemon down. An absent file is the ordinary
    first-run state, so it warns without ceremony.
    """
    path = Path(config_path).expanduser()

    selected: list[str] = []
    seen: set[str] = set()

    def _add(candidate: Path) -> None:
        norm = _norm(candidate)
        if norm not in seen:
            seen.add(norm)
            selected.append(norm)

    declared: list[str] = []
    try:
        document = jsonio.as_object(_parse_jsonc(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        _warn(f"unreadable/unparsable watch-set {path}: {exc}")
        document = None
    if document is not None:
        entries = jsonio.as_list(document.get("repos"))
        if entries is None:
            _warn(f"watch-set {path}: 'repos' is missing or not a list")
        else:
            declared = [entry for entry in entries if isinstance(entry, str)]

    for name in declared:
        candidate = Path(name).expanduser()
        if candidate.is_dir() and (candidate / "plan").is_dir():
            _add(candidate)

    for extra in extra_repos:
        candidate = Path(extra).expanduser()
        if candidate.is_dir():
            _add(candidate)

    return selected


def repo_root_present(repo: str) -> bool:
    """True if the repo checkout root itself exists as a directory.

    The daemon's GC preconditions on this so a TRANSIENTLY-unreachable repo (an
    unmounted volume, a repo mid-move) is not mistaken for "plan deleted" and its
    mapping row permanently dropped + later re-created with DEFAULT overrides
    (adversarial code review 2026-07-13, blocker B6). A missing root ⇒ keep the
    row and surface; only a plan gone UNDER an existing root is a real deletion.
    """
    try:
        return Path(repo).is_dir()
    except OSError:
        return False


def archived_or_gone(repo: str, topic: str) -> bool:
    """True if ``<repo>/plan/<topic>/`` is archived or deleted (ACTIVE wins).

    Used by the daemon's GC to drop a mapping row whose plan has been archived or
    deleted. The ACTIVE ``plan/<topic>`` is checked FIRST and wins: a live plan
    whose topic name ALSO happens to exist under ``plan/archive/`` (a new plan
    reusing a retired topic slug) must NOT be treated as archived — the old code
    checked the archive path first and would GC-drop the active plan's row every
    tick (adversarial code review 2026-07-13, blocker B6). Callers should
    precondition on :func:`repo_root_present` so a missing repo ROOT (transient
    unmount) is not read here as a gone plan.
    """
    base = Path(repo) / "plan"
    if (base / topic).is_dir():
        return False  # active plan present — wins over any same-named archive copy
    if (base / "archive" / topic).is_dir():
        return True  # archived
    return True  # plan dir gone under an existing repo root ⇒ deleted


# --------------------------------------------------------------------------- #
# Injection-stamp sidecar: the per-track timestamp the restart-authorization check
# compares the `.overseer-state` file's mtime against (a `ready` must be THIS round's).
# --------------------------------------------------------------------------- #


def _stamp_store(stamp_path: str | os.PathLike[str] | None) -> Path:
    return Path(stamp_path) if stamp_path is not None else DEFAULT_STAMP_PATH


def _stamp_key(repo: str, topic: str) -> str:
    return f"{_norm(repo)}\t{topic}"


def _read_stamp_data(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _warn(f"unreadable injection-stamp sidecar {path}: {exc}")
        return {}
    stamp = jsonio.as_object(data)
    if stamp is None:
        _warn(f"injection-stamp sidecar {path} is not a JSON object")
        return {}
    return stamp


def read_injection_stamp(
    repo: str,
    topic: str,
    stamp_path: str | os.PathLike[str] | None = None,
) -> float | None:
    """Read a track's injection-round timestamp (epoch seconds), or None if unset.

    The per-key sidecar value is the dict shape ``{"at": <float>, "bands": [...]}``
    — this returns the ``at`` member (the round-open timestamp the certification
    check compares a ready marker's mtime against). BACK-COMPAT: a legacy bare
    float value (the pre-escalation shape) is still accepted and returned as-is.
    None if the key is absent, the dict lacks an ``at``, or the value is unusable.
    """
    data = _read_stamp_data(_stamp_store(stamp_path))
    value = data.get(_stamp_key(repo, topic))
    if value is None:
        return None
    entry = jsonio.as_object(value)
    if entry is not None:
        at = entry.get("at")
        if at is None:
            return None
        stamped = jsonio.as_float(at)
        if stamped is None:
            _warn(f"non-numeric injection stamp for {repo}::{topic}")
        return stamped
    # Legacy bare-float value, from before the sidecar grew its dict shape.
    stamped = jsonio.as_float(value)
    if stamped is None:
        _warn(f"non-numeric injection stamp for {repo}::{topic}")
    return stamped


def write_injection_stamp(
    repo: str,
    topic: str,
    ts: float,
    stamp_path: str | os.PathLike[str] | None = None,
) -> None:
    """Open a fresh injection round for a track: stamp ``at`` and RESET its bands.

    Sets the per-key value to ``{"at": float(ts), "bands": []}`` — a NEW round, so
    any previously-notified escalation bands are cleared (a genuinely fresh round
    must be able to re-warn every band). Read-modify-write under the stamp-sidecar
    lock (so a concurrent writer cannot lose another track's value — B6) and via an
    atomic replace (so a crash cannot truncate the sidecar — B6). Fail-soft on
    OSError (B7).
    """
    path = _stamp_store(stamp_path)
    with _file_lock(path):
        data = _read_stamp_data(path)
        data[_stamp_key(repo, topic)] = {"at": float(ts), "bands": []}
        _atomic_write(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def read_notified_bands(
    repo: str,
    topic: str,
    stamp_path: str | os.PathLike[str] | None = None,
) -> list[int]:
    """The escalation bands already notified this round for a track.

    Reads the ``bands`` member of the dict-shaped sidecar value. Empty for a
    legacy bare-float value, an absent key, or an unusable value — so a track with
    no recorded bands is treated as "nothing notified yet".
    """
    data = _read_stamp_data(_stamp_store(stamp_path))
    value = data.get(_stamp_key(repo, topic))
    entry = jsonio.as_object(value)
    if entry is None:
        return []
    bands = jsonio.as_list(entry.get("bands"))
    if bands is None:
        return []
    return [b for b in bands if isinstance(b, int)]


def add_notified_band(
    repo: str,
    topic: str,
    band: int,
    stamp_path: str | os.PathLike[str] | None = None,
) -> None:
    """Record ``band`` as notified this round (idempotent; preserves ``at``).

    Read-modify-write under the same stamp-sidecar lock + atomic replace as
    :func:`write_injection_stamp`. If the current value is a legacy bare float, it
    is upgraded to the dict shape with that float preserved as ``at``; if it is
    already a dict, its ``at`` (and any existing bands) are preserved. Appending an
    already-recorded band is a no-op (idempotent). Fail-soft on OSError (B7).
    """
    path = _stamp_store(stamp_path)
    with _file_lock(path):
        data = _read_stamp_data(path)
        key = _stamp_key(repo, topic)
        value = data.get(key)
        existing = jsonio.as_object(value)
        if existing is not None:
            entry: dict[str, object] = dict(existing)  # preserve at + existing bands
        elif value is None:
            entry = {}
        else:
            # Legacy bare-float value: upgrade it to the dict shape, keeping `at`.
            legacy = jsonio.as_float(value)
            entry = {} if legacy is None else {"at": legacy}
        bands_raw = jsonio.as_list(entry.get("bands"))
        bands = [b for b in bands_raw if isinstance(b, int)] if bands_raw is not None else []
        if band not in bands:
            bands.append(band)
        entry["bands"] = bands
        data[key] = entry
        _atomic_write(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def clear_injection_stamp(
    repo: str,
    topic: str,
    stamp_path: str | os.PathLike[str] | None = None,
) -> None:
    """Delete a track's injection stamp, closing out its certification round.

    Called by the daemon when it restarts a track: without this the persisted
    stamp OUTLIVES the round, degrading the "marker mtime > injection stamp"
    interlock to "marker newer than the FIRST-EVER injection" — so a later,
    round-less marker (a handoff convention, or a forged one) would spuriously
    certify (adversarial code review 2026-07-13, blocker B4). Same lock + atomic
    write as :func:`write_injection_stamp`; a no-op if the stamp is absent.
    """
    path = _stamp_store(stamp_path)
    with _file_lock(path):
        data = _read_stamp_data(path)
        if _stamp_key(repo, topic) in data:
            del data[_stamp_key(repo, topic)]
            _atomic_write(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def read_resume_pending(
    repo: str,
    topic: str,
    stamp_path: str | os.PathLike[str] | None = None,
) -> bool:
    """True if a restart RESPAWNED the fresh session but its resume line never SUBMITTED.

    The daemon's restart respawns the pane and pastes the ``read <handoff> and follow
    it`` resume line, but a freshly-respawned TUI can DROP the Enter while still drawing
    its welcome screen — leaving the fresh session live but idle with the resume line
    un-submitted (proven live 2026-07-17: fabro / autonomous-mode / overseer-rewrite all
    stranded this way in one day). ``set_resume_pending`` records that state as a
    round-scoped member of the injection-stamp dict so the NEXT tick retries the SUBMIT
    ONLY (re-send Enter, never a re-respawn — a fresh ``ready`` is the sole respawn
    trigger). Reads the ``resume_pending`` member; anything else ⇒ False.

    Round-scoped by construction: :func:`clear_injection_stamp` (restart closed) deletes
    the whole key and :func:`write_injection_stamp` (a fresh round) overwrites the dict, so
    the flag can never outlive the round it belongs to. Fail-soft: an unusable value ⇒ False.
    """
    data = _read_stamp_data(_stamp_store(stamp_path))
    value = data.get(_stamp_key(repo, topic))
    entry = jsonio.as_object(value)
    if entry is None:
        return False
    return entry.get("resume_pending") is True


def set_resume_pending(
    repo: str,
    topic: str,
    stamp_path: str | os.PathLike[str] | None = None,
) -> None:
    """Record that a restart respawned the fresh session but its resume did not submit.

    Sets the ``resume_pending`` member on the track's injection-stamp dict, PRESERVING
    ``at`` (so the ``ready`` marker still certifies — ``mtime > at``) and any notified
    ``bands``. Same lock + atomic replace as :func:`write_injection_stamp`. If the current
    value is a legacy bare float, it is upgraded to the dict shape with that float as
    ``at``; if the key is absent, a bare ``{"resume_pending": True}`` is written (the
    retry still fires — it keys on this flag, not on ``at``). Fail-soft on OSError (B7).
    """
    path = _stamp_store(stamp_path)
    with _file_lock(path):
        data = _read_stamp_data(path)
        key = _stamp_key(repo, topic)
        value = data.get(key)
        existing = jsonio.as_object(value)
        if existing is not None:
            entry: dict[str, object] = dict(existing)  # preserve at + bands
        elif value is None:
            entry = {}
        else:
            # Legacy bare-float value: upgrade it to the dict shape, keeping `at`.
            legacy = jsonio.as_float(value)
            entry = {} if legacy is None else {"at": legacy}
        entry["resume_pending"] = True
        data[key] = entry
        _atomic_write(path, json.dumps(data, indent=2, sort_keys=True) + "\n")
