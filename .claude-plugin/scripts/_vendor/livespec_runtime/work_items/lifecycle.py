"""The single lane authority: `lane_of` + `is_item_ready` + `ready_sort_key`.

Codified by this repo's own `### livespec_runtime.work_items.lifecycle`
(SPECIFICATION/contracts.md). The board lane **is** the stored state,
with exactly one derived overlay, so `lane_of` is the one place
"open dependency" is computed and `is_item_ready` /
`ready_sort_key` can never diverge from what the board renders.

`is_item_ready` and the dependency-blocking predicate are RELOCATED from
the beads-fabro orchestrator's `commands/_cross_repo.py`, but as PURE
functions: the only injected status source is the in-memory `index`
(`dict[str, WorkItem]`) the caller already holds, from which the
`local_status_lookup` `resolve_ref` expects is constructed. The beads
store-reading (`resolve_store_config` / the `read_work_items` free
function / `StoreConfig`) does NOT move here — that would be a
`runtime → beads` back-edge. Sibling work-item dependencies therefore
resolve to `UNKNOWN` at this layer UNLESS the caller injects a
`sibling_status_lookup` (the orchestrator's job — it holds the beads
client): with the resolver a genuinely CLOSED sibling is satisfied and
stops blocking, and without it an unresolved sibling BLOCKS (fail-closed)
so a still-open cross-repo blocker cannot be dispatched past. PR /
branch dependencies resolve through the existing
`livespec_runtime.cross_repo` `gh` provider.

`ready_sort_key` is AGING-AWARE: it is a factory both the orchestrator's
`next` and its Dispatcher call to compose ONE ordering, so there is no
second dispatcher-local sort key that could drift. `rank` stays the
primary key; within a rank tier an item that has been ready longer than
the aging bound is ordered ahead of its newer equal-rank siblings. The
ready instant is INJECTED (`ready_since_lookup`), for the same reason the
sibling status is: the durable, clone-independent instant lives in the
consumer's store, and reading it here would be a `runtime → beads`
back-edge.

This module imports NO beads / orchestrator symbol — only the shared
`livespec_runtime.cross_repo` resolution surface and the `WorkItem`
domain type.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, cast

from livespec_runtime.cross_repo.resolve import resolve_ref
from livespec_runtime.cross_repo.types import (
    CrossRepoManifest,
    DependsOnEntry,
    LocalDependency,
    RefStatus,
    parse_depends_on_entry,
)
from livespec_runtime.work_items.types import WorkItem

__all__: list[str] = [
    "BlockedReason",
    "Lane",
    "LaneName",
    "is_item_ready",
    "lane_of",
    "ready_sort_key",
]

# Resolves a work-item id to the durable, clone-independent instant of the
# item's LATEST transition into `ready` — the same `ready_since` source the
# orchestrator's `hygiene:ready-aging:<repo>` surfacing reads, NOT a
# machine-local dispatch journal. `None` means the instant is unknowable
# for that item.
_ReadySinceLookup = Callable[[str], datetime | None]

# `(rank, aging tier, ready-instant order, id)`. See `ready_sort_key`.
_ReadySortKeyTuple = tuple[str, int, float, str]

# The aging bound's default, in hours. It carries the semantics of the
# orchestrator's EXISTING `dispatcher.ready_aging_threshold_hours` config
# key — this is not a new key and there is no per-item override; the
# consumer passes that key's value through as
# `ready_aging_threshold_hours`. These three names stay module-private
# because the ratified public-surface inventory
# (`SPECIFICATION/contracts.md`) enumerates this module's exports and
# `ready_sort_key` is the only one of them the aging tiebreak needs.
_DEFAULT_READY_AGING_THRESHOLD_HOURS = 24.0

# Aging tier: aged items sort BEFORE their equal-rank siblings, so the
# aged tier is the smaller value. The tier is the SECOND component, after
# `rank`, which is what keeps the tiebreak strictly inside a rank tier.
_AGED_TIER = 0
_UNAGED_TIER = 1

# The ready-instant component every un-aged key carries. It is constant
# across the un-aged tier, so `id` alone decides within it.
_NO_AGE_ORDER = 0.0

LaneName = Literal[
    "backlog",
    "pending-approval",
    "ready",
    "active",
    "acceptance",
    "blocked",
    "done",
]
BlockedReason = Literal["needs-human", "infra-external", "dependency"]


@dataclass(frozen=True, slots=True, kw_only=True)
class Lane:
    """The rendered board lane — the stored state with one derived overlay.

    `reason` is non-None iff `name == "blocked"`: either a stored
    `StoredBlockedReason` (`needs-human` / `infra-external`) carried
    straight through from a stored-`blocked` item, or the DERIVED
    `dependency` overlay applied to a stored-`ready` item that still has
    an open dependency. (Note the asymmetry: the rendered `BlockedReason`
    has three values; the stored `StoredBlockedReason` has only two —
    `dependency` is never stored.)
    """

    name: LaneName
    reason: BlockedReason | None = None


def lane_of(
    *,
    item: WorkItem,
    index: dict[str, WorkItem],
    manifest: CrossRepoManifest,
    sibling_status_lookup: Callable[[str, str], RefStatus] | None = None,
) -> Lane:
    """Return the rendered lane for `item` — the single lane authority.

    The board lane IS the stored status, with exactly one derived overlay:

    - stored `blocked` → `Lane("blocked", <stored blocked_reason>)`;
    - stored `ready` + any OPEN dependency → `Lane("blocked", "dependency")`;
    - every other state → `Lane(<status>, None)`.

    "Open dependency": a dependency blocks iff it `resolve_ref`-resolves to
    `OPEN`, is unparseable (fail-closed), or is a `sibling_work_item` that
    did not resolve to `CLOSED` (also fail-closed — see `_entry_blocks`).
    `CLOSED` never blocks, and `UNKNOWN` blocks for a `sibling_work_item`
    entry ONLY, so `lane_of` and `is_item_ready` agree by construction.
    Local dependencies resolve against `index`; sibling work-item
    dependencies resolve via the optional injected `sibling_status_lookup`
    — or to `UNKNOWN` when none is supplied (there is no `runtime → beads`
    back-edge at this layer, so the orchestrator injects the resolver);
    PR / branch dependencies resolve via the `cross_repo` `gh` provider.
    """
    if item.status == "blocked":
        return Lane(name="blocked", reason=item.blocked_reason)
    if item.status == "ready" and _has_open_dependency(
        item=item,
        index=index,
        manifest=manifest,
        sibling_status_lookup=sibling_status_lookup,
    ):
        return Lane(name="blocked", reason="dependency")
    return Lane(name=item.status, reason=None)


def is_item_ready(
    *,
    item: WorkItem,
    index: dict[str, WorkItem],
    manifest: CrossRepoManifest,
    sibling_status_lookup: Callable[[str, str], RefStatus] | None = None,
) -> bool:
    """Return True iff the item renders in the `ready` lane.

    Re-expressed as `lane_of(...).name == "ready"` so readiness can never
    diverge from the rendered board: a stored-`ready` item with an open
    dependency renders `blocked:dependency` and is therefore NOT ready.
    """
    return (
        lane_of(
            item=item,
            index=index,
            manifest=manifest,
            sibling_status_lookup=sibling_status_lookup,
        ).name
        == "ready"
    )


def ready_sort_key(
    *,
    now: datetime,
    ready_since_lookup: _ReadySinceLookup | None = None,
    ready_aging_threshold_hours: float = _DEFAULT_READY_AGING_THRESHOLD_HOURS,
) -> Callable[[WorkItem], _ReadySortKeyTuple]:
    """Build the single canonical ready ordering key, aging-aware.

    This is a FACTORY rather than the key itself: the ordering needs a
    clock and the durable ready instant, and both `next` and the
    Dispatcher must compose the SAME key. They each call this once per
    pass and hand the result to `sorted(..., key=...)`, so there is no
    second dispatcher-local sort key to drift from this one.

    The key is `(rank, aging tier, ready-instant order, id)`:

    - `rank` stays the PRIMARY key, so the aging tiebreak is strictly
      WITHIN a rank tier and can never promote an item across tiers — a
      higher-`rank` item is never overtaken by a lower-`rank` aged one.
    - the aging tier is `_AGED_TIER` for an item that has been ready
      LONGER than `ready_aging_threshold_hours`, and `_UNAGED_TIER`
      otherwise, so an aged item is ordered ahead of its newer
      equal-rank siblings;
    - within the aged tier the ready instant orders ASCENDING, i.e. the
      item that has waited longest goes first;
    - within the un-aged tier that component is the constant
      `_NO_AGE_ORDER`, so the deterministic `id` lexicographic tiebreak
      is retained exactly as before.

    `ready_since_lookup` is the ONLY age input, and it resolves the
    DURABLE, clone-independent `ready_since` instant (see
    `_ReadySinceLookup`). An item whose instant is unknowable — the lookup
    returns `None`, or no lookup was injected at all — lands in the
    un-aged tier and keeps the `id` tiebreak with NO age advantage, which
    is also why omitting the lookup degrades cleanly to the previous
    `(rank, id)` ordering rather than to an arbitrary one.

    Naive datetimes (`now` or a looked-up instant) are read as UTC, the
    durable store's own convention, so a store that hands back naive
    timestamps orders identically to one that hands back aware ones
    instead of failing on mixed-awareness arithmetic.
    """
    return _ReadySortKey(
        now=_as_utc(moment=now),
        ready_since_lookup=ready_since_lookup,
        aging_bound=timedelta(hours=ready_aging_threshold_hours),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class _ReadySortKey:
    """The composed ordering key `ready_sort_key` returns."""

    now: datetime
    ready_since_lookup: _ReadySinceLookup | None
    aging_bound: timedelta

    def __call__(self, item: WorkItem) -> _ReadySortKeyTuple:
        unaged = (item.rank, _UNAGED_TIER, _NO_AGE_ORDER, item.id)
        if self.ready_since_lookup is None:
            return unaged
        ready_since = self.ready_since_lookup(item.id)
        if ready_since is None:
            return unaged
        ready_since_utc = _as_utc(moment=ready_since)
        if self.now - ready_since_utc <= self.aging_bound:
            return unaged
        return (item.rank, _AGED_TIER, ready_since_utc.timestamp(), item.id)


def _as_utc(*, moment: datetime) -> datetime:
    """Return `moment` as a UTC-aware datetime, reading naive input as UTC."""
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def _has_open_dependency(
    *,
    item: WorkItem,
    index: dict[str, WorkItem],
    manifest: CrossRepoManifest,
    sibling_status_lookup: Callable[[str, str], RefStatus] | None = None,
) -> bool:
    return any(
        _entry_blocks(
            raw=raw,
            index=index,
            manifest=manifest,
            sibling_status_lookup=sibling_status_lookup,
        )
        for raw in item.depends_on
    )


def _entry_blocks(
    *,
    raw: object,
    index: dict[str, WorkItem],
    manifest: CrossRepoManifest,
    sibling_status_lookup: Callable[[str, str], RefStatus] | None = None,
) -> bool:
    """Return True iff the raw depends_on entry blocks readiness.

    Three blocking cases:

    - the entry resolves to `OPEN`;
    - the entry is unparseable (`_parse_entry` returning None) — a
      malformed `depends_on` cell must not let a candidate slip through as
      ready (fail-closed);
    - the entry is a `sibling_work_item` that did NOT resolve to `CLOSED`.
      A cross-repo blocker resolves to `UNKNOWN` whenever the caller
      supplies no `sibling_status_lookup`, so treating that `UNKNOWN` as
      non-blocking would dispatch candidates whose cross-repo blockers are
      still open — and would make a WELL-FORMED cross-tenant entry less
      blocking than a malformed one. When a `sibling_status_lookup` IS
      injected (the orchestrator's job — it holds the beads client and the
      manifest), a genuinely CLOSED sibling resolves `CLOSED` and stops
      blocking, an OPEN one blocks via the first case, and an unresolvable
      one stays `UNKNOWN` and keeps failing closed.

    The narrow kind check is deliberate. An unresolved LOCAL reference
    (a missing id) still resolves `UNKNOWN` and still does NOT block:
    orphaned local ids are the doctor's `no-orphan-dependency` invariant's
    business, not the readiness gate's. `pull_request` / `branch` entries
    resolve against a live `gh` view whose `UNKNOWN` means transient query
    failure, and keep their tolerate-partial-visibility semantics.
    """
    entry = _parse_entry(raw=raw)
    if entry is None:
        return True
    status = resolve_ref(
        entry=entry,
        manifest=manifest,
        local_status_lookup=_local_status_lookup_for(index=index),
        sibling_status_lookup=sibling_status_lookup,
    )
    if status == RefStatus.OPEN:
        return True
    return entry.kind == "sibling_work_item" and status == RefStatus.UNKNOWN


def _parse_entry(*, raw: object) -> DependsOnEntry | None:
    """Dispatch a raw `depends_on` entry into a typed `DependsOnEntry`.

    Bare strings become `LocalDependency` (the pre-typed-form store shape).
    A typed dict is parsed via `cross_repo.parse_depends_on_entry`, whose
    failure track collapses to None here. Any other shape — or a dict that
    fails schema validation — returns None, so `_entry_blocks` can fail
    closed.
    """
    if isinstance(raw, str):
        return LocalDependency(work_item_id=raw)
    if isinstance(raw, dict):
        typed_raw = cast(dict[str, Any], raw)
        return parse_depends_on_entry(parsed=typed_raw).value_or(None)
    return None


def _local_status_lookup_for(*, index: dict[str, WorkItem]) -> Callable[[str], RefStatus]:
    """Build the `local_status_lookup` callable `resolve_ref` expects.

    A same-repo dependency is CLEARED iff the target item is `done`
    (`CLOSED`); any other live state is still in-flight (`OPEN`); a missing
    id is `UNKNOWN` (the doctor's orphan-dependency invariant is the right
    surface for that, not the readiness gate — `UNKNOWN` does not block).
    """

    return _LocalStatusLookup(index=index)


@dataclass(frozen=True, slots=True, kw_only=True)
class _LocalStatusLookup:
    index: dict[str, WorkItem]

    def __call__(self, work_item_id: str) -> RefStatus:
        record = self.index.get(work_item_id)
        if record is None:
            return RefStatus.UNKNOWN
        if record.status == "done":
            return RefStatus.CLOSED
        return RefStatus.OPEN
