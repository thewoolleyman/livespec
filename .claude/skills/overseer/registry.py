"""registry.py — overseer mapping store + discovery ⋈ mapping join.

Pure-logic, stdlib-only. Host-only tooling under ``.claude/skills/overseer/``,
deliberately OUTSIDE the livespec product gates (pyright.include, coverage,
import-linter, and — since PR #1109 — ruff's whole-repo scan). Precedent:
``.claude/hooks/livespec_footgun_guard.py``. See ``design.md`` beside this file.

Vocabulary (see design.md, the discovery-join model):
  - A "track" is one plan topic in one repo the overseer watches this run.
  - "discovery" = scan each watched repo's ``plan/*/`` for a ``handoff.md``.
  - "mapping"   = the durable topic↔tmux rows in ``~/.livespec-overseer.jsonl``,
    which hold ONLY facts that cannot be rederived from the filesystem
    (pinned session id, custom resume line, threshold override).
  - the displayed list = discovery LEFT-JOIN mapping.

The tmux session name is repo-qualified ``<repo-slug>--<topic>`` because tmux
session names are GLOBAL while plan topics are only unique per repo
(adversarial-review blocker #8).
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import re
import sys
import tempfile
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, replace
from pathlib import Path

__all__ = [
    "DEFAULT_CTX_THRESHOLD",
    "DEFAULT_STAMP_PATH",
    "DEFAULT_STORE_PATH",
    "Track",
    "append_mapping",
    "archived_or_gone",
    "clear_injection_stamp",
    "discover_plans",
    "join",
    "read_injection_stamp",
    "read_mapping",
    "remove_mapping",
    "repo_root_present",
    "repo_slug",
    "rewrite_mapping",
    "tmux_id",
    "watch_set",
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


# The default remaining-context threshold at which the wrap-up is injected.
DEFAULT_CTX_THRESHOLD = 50

# The durable mapping store and the injection-stamp sidecar both live beside
# the maintainer's home dir (NOT inside any governed repo — the marker files
# `.overseer-ready`/`.overseer-blocked` are the only overseer state that lives
# inside a governed plan dir). Both paths are parameterizable so tests can point
# them at a tmp_path.
DEFAULT_STORE_PATH = Path.home() / ".livespec-overseer.jsonl"
DEFAULT_STAMP_PATH = Path.home() / ".livespec-overseer-stamps.json"

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
    print(f"overseer.registry: {message}", file=sys.stderr)


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


def tmux_id(repo: str | os.PathLike[str], topic: str) -> str:
    """The repo-qualified tmux session name ``<repo-slug>--<topic>``.

    The separator is ``--`` (NOT ``:``): tmux ≥3.3 SANITIZES ``:`` and ``.`` in a
    ``new-session -s`` name to ``_``, so a session created as ``slug:topic`` is
    actually named ``slug_topic`` and ``-t slug:topic`` then parses as session
    ``slug`` + window ``topic`` and never round-trips — the daemon could not find
    the session it created (verified live 2026-07-13, adversarial code review
    blocker B1). ``--`` is tmux-legal and round-trips exactly.
    """
    return f"{repo_slug(repo)}--{topic}"


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
    ctx_threshold: int = DEFAULT_CTX_THRESHOLD
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
        if not isinstance(obj, dict):
            _warn(f"skipping non-object line {lineno} in {path}")
            continue
        rows.append(obj)
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
                handle.write(body)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        except OSError:
            with contextlib.suppress(OSError):
                os.unlink(tmp_name)
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
    threshold = row.get("ctx_threshold", DEFAULT_CTX_THRESHOLD)
    ctx_threshold = threshold if isinstance(threshold, int) else DEFAULT_CTX_THRESHOLD

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
    return {
        "topic": track.topic,
        "repo": track.repo,
        "tmux": track.tmux,
        "handoff": track.handoff,
        "resume": track.resume,
        "epic": track.epic,
        "ctx_threshold": track.ctx_threshold,
        "pinned_session_id": track.pinned_session_id,
    }


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
                handle.write(json.dumps(row) + "\n")
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


# --------------------------------------------------------------------------- #
# Discovery, join, watch-set, archive-GC.
# --------------------------------------------------------------------------- #


def discover_plans(
    watch_repos: Iterable[str | os.PathLike[str]],
) -> list[tuple[str, str, str]]:
    """Scan each watched repo's ``plan/*/`` for a ``handoff.md``.

    Returns ``(repo, topic, abs-handoff-path)`` triples, sorted for
    determinism. Excludes ``plan/archive/**`` (only direct children of
    ``plan/`` are considered, and the literal ``archive`` dir is skipped).
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
                handoff = child / "handoff.md"
                if handoff.is_file():
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


def _strip_jsonc_comments(text: str) -> str:
    """Strip ``//`` line and ``/* */`` block comments, string-literal-aware.

    A hand-rolled state machine (not a regex) so a ``//`` or ``/*`` inside a
    JSON string value is preserved. Avoids adding a JSONC/TOML/YAML dependency.
    """
    out: list[str] = []
    i = 0
    n = len(text)
    in_string = False
    escape = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            i += 2
            while i < n and text[i] != "\n":
                i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _parse_jsonc(text: str) -> object:
    stripped = _strip_jsonc_comments(text)
    # Tolerate trailing commas before a closing brace/bracket (common in JSONC).
    stripped = re.sub(r",(\s*[}\]])", r"\1", stripped)
    return json.loads(stripped)


def _manifest_repo_names(manifest: object) -> list[str]:
    """Collect ``repo`` names from a parsed manifest's fleet + adopters arrays."""
    names: list[str] = []
    if not isinstance(manifest, dict):
        return names
    for section in ("fleet", "adopters"):
        entries = manifest.get(section)
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict):
                repo = entry.get("repo")
                if isinstance(repo, str):
                    names.append(repo)
    return names


def watch_set(
    fleet_manifest_path: str | os.PathLike[str],
    extra_repos: Iterable[str | os.PathLike[str]] = (),
) -> list[str]:
    """Compute the default watch-set: local-checkout repos that have a ``plan/``.

    Seeded from ``.livespec-fleet-manifest.jsonc`` (fleet members + adopters),
    each name resolved against the projects-root (the parent of the manifest's
    own repo checkout — e.g. a manifest at ``/data/projects/livespec/...``
    resolves siblings under ``/data/projects/``). A manifest repo is included
    only if its checkout exists AND has a ``plan/`` dir. ``extra_repos`` (an
    off-manifest manual override) are included if they exist. Fail-soft on an
    unreadable/unparsable manifest — the extras still apply.
    """
    manifest_path = Path(fleet_manifest_path).expanduser()
    projects_root = manifest_path.resolve().parent.parent

    selected: list[str] = []
    seen: set[str] = set()

    def _add(path: Path) -> None:
        norm = _norm(path)
        if norm not in seen:
            seen.add(norm)
            selected.append(norm)

    try:
        manifest = _parse_jsonc(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _warn(f"unreadable/unparsable manifest {manifest_path}: {exc}")
        manifest = None

    for name in _manifest_repo_names(manifest):
        candidate = projects_root / name
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
# Injection-stamp sidecar: the per-track timestamp the certification check
# compares the `.overseer-ready` marker's mtime against.
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
    if not isinstance(data, dict):
        _warn(f"injection-stamp sidecar {path} is not a JSON object")
        return {}
    return data


def read_injection_stamp(
    repo: str,
    topic: str,
    stamp_path: str | os.PathLike[str] | None = None,
) -> float | None:
    """Read the injection stamp (epoch seconds) for a track, or None if unset."""
    data = _read_stamp_data(_stamp_store(stamp_path))
    value = data.get(_stamp_key(repo, topic))
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        _warn(f"non-numeric injection stamp for {repo}::{topic}")
        return None


def write_injection_stamp(
    repo: str,
    topic: str,
    ts: float,
    stamp_path: str | os.PathLike[str] | None = None,
) -> None:
    """Persist the injection stamp (epoch seconds) for a track.

    Read-modify-write under the stamp-sidecar lock (so a concurrent writer cannot
    lose another track's stamp — B6) and via an atomic replace (so a crash cannot
    truncate the sidecar — B6). Fail-soft on OSError (B7).
    """
    path = _stamp_store(stamp_path)
    with _file_lock(path):
        data = _read_stamp_data(path)
        data[_stamp_key(repo, topic)] = float(ts)
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
