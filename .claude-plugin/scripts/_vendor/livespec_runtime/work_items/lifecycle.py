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
resolve to `UNKNOWN` at this layer, and an unresolved sibling BLOCKS
(fail-closed) so a still-open cross-repo blocker cannot be dispatched
past; the orchestrator keeps its own beads-backed sibling reading. PR /
branch dependencies resolve through the existing
`livespec_runtime.cross_repo` `gh` provider.

This module imports NO beads / orchestrator symbol — only the shared
`livespec_runtime.cross_repo` resolution surface and the `WorkItem`
domain type.
"""

from collections.abc import Callable
from dataclasses import dataclass
from operator import attrgetter
from typing import Any, Literal, cast

from livespec_runtime.cross_repo.errors import CrossRepoSchemaError
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

ready_sort_key: Callable[[WorkItem], tuple[str, str]] = cast(
    Callable[[WorkItem], tuple[str, str]],
    attrgetter("rank", "id"),
)

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
    dependencies resolve to `UNKNOWN` (no `runtime → beads` back-edge);
    PR / branch dependencies resolve via the `cross_repo` `gh` provider.
    """
    if item.status == "blocked":
        return Lane(name="blocked", reason=item.blocked_reason)
    if item.status == "ready" and _has_open_dependency(item=item, index=index, manifest=manifest):
        return Lane(name="blocked", reason="dependency")
    return Lane(name=item.status, reason=None)


def is_item_ready(
    *,
    item: WorkItem,
    index: dict[str, WorkItem],
    manifest: CrossRepoManifest,
) -> bool:
    """Return True iff the item renders in the `ready` lane.

    Re-expressed as `lane_of(...).name == "ready"` so readiness can never
    diverge from the rendered board: a stored-`ready` item with an open
    dependency renders `blocked:dependency` and is therefore NOT ready.
    """
    return lane_of(item=item, index=index, manifest=manifest).name == "ready"


def _has_open_dependency(
    *,
    item: WorkItem,
    index: dict[str, WorkItem],
    manifest: CrossRepoManifest,
) -> bool:
    return any(_entry_blocks(raw=raw, index=index, manifest=manifest) for raw in item.depends_on)


def _entry_blocks(
    *,
    raw: object,
    index: dict[str, WorkItem],
    manifest: CrossRepoManifest,
) -> bool:
    """Return True iff the raw depends_on entry blocks readiness.

    Three blocking cases:

    - the entry resolves to `OPEN`;
    - the entry is unparseable (`_parse_entry` returning None) — a
      malformed `depends_on` cell must not let a candidate slip through as
      ready (fail-closed);
    - the entry is a `sibling_work_item` that did NOT resolve to `CLOSED`.
      A cross-repo blocker resolves to `UNKNOWN` whenever the caller
      supplies no `sibling_status_lookup` (which, at this layer, is
      always), so treating that `UNKNOWN` as non-blocking would dispatch
      candidates whose cross-repo blockers are still open — and would make
      a WELL-FORMED cross-tenant entry less blocking than a malformed one.

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
        sibling_status_lookup=None,
    )
    if status == RefStatus.OPEN:
        return True
    return entry.kind == "sibling_work_item" and status == RefStatus.UNKNOWN


def _parse_entry(*, raw: object) -> DependsOnEntry | None:
    """Dispatch a raw `depends_on` entry into a typed `DependsOnEntry`.

    Bare strings become `LocalDependency` (the pre-typed-form store shape).
    A typed dict is parsed via `cross_repo.parse_depends_on_entry`. Any
    other shape — or a dict that fails schema validation — returns None, so
    `_entry_blocks` can fail closed.
    """
    if isinstance(raw, str):
        return LocalDependency(work_item_id=raw)
    if isinstance(raw, dict):
        typed_raw = cast(dict[str, Any], raw)
        try:
            return parse_depends_on_entry(parsed=typed_raw)
        except CrossRepoSchemaError:
            return None
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
