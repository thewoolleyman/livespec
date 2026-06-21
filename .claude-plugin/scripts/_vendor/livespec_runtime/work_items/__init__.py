"""livespec_runtime.work_items — the shared WorkItem model + canonical reducer.

Lifts the genuinely-duplicated work-item surface that every
livespec impl-plugin re-implemented identically into one shared home,
per the W7 "shared Store surface" extraction. The substrate-specific
backend I/O stays per-impl; what lives here is exactly the part that
was byte-identical across `livespec-impl-git-jsonl` and
`livespec-impl-beads`:

- `livespec_runtime.work_items.types` — the unified `WorkItem` (the
  git-jsonl 16-field shape, carrying `supersedes`; beads' WorkItem is
  this minus that one append-only-supersession field), the
  `AuditRecord` sub-object, and the schema enums/aliases
  (`WorkItemStatus`, `WorkItemType`, `Origin`, `Resolution`,
  `DependsOnRaw`). The transitive type closure reachable from
  `WorkItem` bottoms out in primitives + `AuditRecord`; no Spec-Reader
  types (`SpecSnapshot`/`SpecDiff`/`FileDiff`) are reachable, so they
  are NOT lifted here.
- `livespec_runtime.work_items.reduce` — the canonical PURE
  order-independent head reduction (`reduce_work_item_heads`,
  `materialize_work_items`), the stable per-record identity
  (`work_item_record_identity`) over the canonical serialization, and
  the `random_id_suffix` suffix generator. git-jsonl's algorithm is
  preserved byte-faithfully (deterministic `(captured_at, identity)`
  tie-break, divergent-head representation); beads' degenerate
  one-record-per-id input is the trivial case of the same reducer.
- `livespec_runtime.work_items.store` — the `WorkItemStore`
  conformance `typing.Protocol` (`read_work_items` /
  `append_work_item`). Backend I/O is NOT lifted; each consumer ships a
  thin facade over its existing per-impl free functions to satisfy
  this Protocol.

The package namespace itself stays empty (`__all__: list[str] = []`)
so the import contract is explicit at the sub-module level; this
matches the discipline applied throughout `livespec_runtime.cross_repo`
and livespec-core.
"""

__all__: list[str] = []
