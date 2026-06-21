"""The `WorkItemStore` conformance Protocol.

The shared-surface extraction lifts the WorkItem MODEL and the canonical
PURE reduction (see `livespec_runtime.work_items.types` /
`.reduce`), but deliberately does NOT lift backend I/O — the on-disk
JSONL append-only file (git-jsonl) and the per-tenant dolt-server issue
table (beads) have nothing in common at the storage layer. What they DO
share is a contract: a stream of `WorkItem` records out, one `WorkItem`
record in.

`WorkItemStore` is that contract expressed as a `typing.Protocol`
(structural conformance, no inheritance required — mirroring the
`abc`-banned, Protocol-only discipline enforced repo-wide). Each
consumer ships a thin facade class over its EXISTING per-impl store
free functions to satisfy this Protocol; the facades themselves live in
the consumer repos, not here (this module is just the contract).

The Protocol is intentionally narrow — exactly the two operations both
substrates already expose:

- `read_work_items(self)` — stream every record the store holds.
- `append_work_item(self, *, item)` — add one record (the substrate
  decides whether that is a literal append, an in-place mutation, or a
  fresh backend row; the canonical reducer reconciles supersession
  chains afterward, so a substrate that is inherently one-record-per-id
  is the degenerate case).

Note: comments are NOT part of this contract — only one substrate
(beads) carries them, so they stay a per-impl sidecar.
"""

from collections.abc import Iterator
from typing import Protocol

from livespec_runtime.work_items.types import WorkItem

__all__: list[str] = ["WorkItemStore"]


class WorkItemStore(Protocol):
    """Structural contract every impl-plugin's work-item store satisfies.

    A consumer conforms by exposing these two methods over whatever
    backend it owns (a JSONL file, a beads tenant, an in-memory fake).
    Tools that operate over the shared `WorkItem` model — the canonical
    reducer, the `next` ranker, the materialized-view consumers — depend
    on this Protocol rather than on any one substrate, so they work
    UNCHANGED across substrates.
    """

    def read_work_items(self) -> Iterator[WorkItem]:
        """Stream every WorkItem record the store currently holds."""
        ...

    def append_work_item(self, *, item: WorkItem) -> None:
        """Add a single WorkItem record to the store."""
        ...
