"""Canonical PURE work-item logic: identity, head reduction, id suffix.

This is the order-independent reduction lifted byte-faithfully from
`livespec-impl-git-jsonl`'s store — the canonical reducer of which
beads' historical one-record-per-id collection is the degenerate case.
Per livespec/SPECIFICATION/contracts.md §"Materialized view" /
§"Append-only store disciplines", an entity's materialized view is its
supersession-chain head, computed from the in-record `supersedes`
pointers INDEPENDENTLY of the physical order of records (git may
reorder lines during a merge; a "latest record by file order wins"
reduction is retired).

Public surface:

- `work_item_record_identity(*, item)` — the stable per-record
  identity: `sha256:<hex-digest>` over the record's canonical
  serialization (every schema key explicit, sorted keys, compact
  separators — exactly the line bytes an append path writes, without
  the trailing newline). Derivable from record content alone; the value
  a superseding record carries in its `supersedes` key.
- `reduce_work_item_heads(*, records)` — the canonical order-independent
  reduction: per entity `id`, every record whose identity no sibling
  record's `supersedes` names, ordered ascending by the deterministic
  tie-break (`captured_at`, then per-record identity). Identical records
  (equal identity — e.g. a line duplicated by a `merge=union` merge)
  collapse to one. More than one head for an `id` is concurrent
  divergence, surfaced for detection rather than silently resolved.
- `materialize_work_items(*, records)` — reduce a stream to the
  current-head-per-id dict (the tie-break winner among each entity's
  heads).
- `random_id_suffix()` — a fresh six-character base32 id suffix (the
  `li-<suffix>` body), lifted from git-jsonl's `_random_suffix`.

Every function here is PURE (no filesystem, no network, no backend
state) so the model + reducer can be shared regardless of substrate;
backend I/O lives in the per-impl `WorkItemStore` facades.
"""

import base64
import hashlib
import json
import secrets
from collections.abc import Iterator
from dataclasses import asdict
from typing import Any, Protocol, TypeVar

from livespec_runtime.work_items.types import WorkItem

__all__: list[str] = [
    "materialize_work_items",
    "random_id_suffix",
    "reduce_work_item_heads",
    "work_item_record_identity",
]

_SUFFIX_BYTES = 4  # 4 bytes → 32 bits → base32 yields ~7 chars; trimmed to 6.
_SUFFIX_LENGTH = 6


class _SupersedableRecord(Protocol):
    """Structural shape the canonical head reduction consumes."""

    @property
    def id(self) -> str: ...

    @property
    def captured_at(self) -> str: ...

    @property
    def supersedes(self) -> str | None: ...


_RecordT = TypeVar("_RecordT", bound=_SupersedableRecord)


def work_item_record_identity(*, item: WorkItem) -> str:
    """Return the stable per-record identity of a work-item record.

    `sha256:<hex-digest>` over the record's canonical serialization
    (all sixteen schema keys explicit, sorted, compact separators).
    Legacy records read back from a substrate without the optional keys
    normalize to the same canonical form, so the identity is a pure
    function of record content — no file positions, no external state.
    """
    return _record_identity(payload=_work_item_to_dict(item=item))


def reduce_work_item_heads(
    *,
    records: Iterator[WorkItem],
) -> dict[str, tuple[WorkItem, ...]]:
    """Reduce a WorkItem stream to the un-superseded heads per `id`.

    The canonical order-independent reduction per
    livespec/SPECIFICATION/contracts.md §"Materialized view": each
    entity's heads are the records whose identity no sibling record's
    `supersedes` pointer names, in ascending tie-break order
    (`captured_at`, then per-record identity). A tuple longer than one
    is concurrent divergence — representable and detectable, never
    silently resolved here.
    """
    entries = ((work_item_record_identity(item=record), record) for record in records)
    return _reduce_heads(entries=entries)


def materialize_work_items(*, records: Iterator[WorkItem]) -> dict[str, WorkItem]:
    """Reduce a WorkItem stream to the current-head-per-id dict.

    The current head is the supersession-chain head; when an entity has
    divergent heads the deterministic tie-break winner (greatest
    `captured_at`, then greatest per-record identity) is returned.
    Consumers that must DETECT divergence consume
    `reduce_work_item_heads` directly.
    """
    return {
        entity_id: heads[-1] for entity_id, heads in reduce_work_item_heads(records=records).items()
    }


def random_id_suffix() -> str:
    """Return a fresh six-character lowercase base32 id suffix.

    The `li-<suffix>` body, per livespec/SPECIFICATION/contracts.md
    §"Work-items JSONL record schema" (the upstream `bd` convention
    `li-<6-char-base32-suffix>`). Randomness comes from
    `secrets.token_bytes`, so collision probability is negligible.
    Backend-coupled id MINTING (deciding the `li-` prefix and any
    backend-side uniqueness check) stays in each impl-plugin; only the
    suffix generator is shared.
    """
    raw = secrets.token_bytes(_SUFFIX_BYTES)
    encoded = base64.b32encode(raw).decode("ascii").lower()
    return encoded[:_SUFFIX_LENGTH]


def _record_identity(*, payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _reduce_heads(
    *,
    entries: Iterator[tuple[str, _RecordT]],
) -> dict[str, tuple[_RecordT, ...]]:
    groups: dict[str, dict[str, _RecordT]] = {}
    for identity, record in entries:
        groups.setdefault(record.id, {})[identity] = record
    heads: dict[str, tuple[_RecordT, ...]] = {}
    for entity_id, group in groups.items():
        superseded = frozenset(
            record.supersedes for record in group.values() if record.supersedes is not None
        )
        unsuperseded = {
            identity: record for identity, record in group.items() if identity not in superseded
        }
        tie_break_order = sorted(
            (record.captured_at, identity) for identity, record in unsuperseded.items()
        )
        heads[entity_id] = tuple(unsuperseded[identity] for _, identity in tie_break_order)
    return heads


def _work_item_to_dict(*, item: WorkItem) -> dict[str, Any]:
    payload = asdict(item)
    payload["depends_on"] = list(item.depends_on)
    if item.audit is not None:
        payload["audit"] = {
            "verification_timestamp": item.audit.verification_timestamp,
            "commits": list(item.audit.commits),
            "files_changed": list(item.audit.files_changed),
            "merge_sha": item.audit.merge_sha,
            "pr_number": item.audit.pr_number,
        }
    return payload
