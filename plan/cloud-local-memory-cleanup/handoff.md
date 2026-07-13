# Cloud-Local Memory Cleanup — Handoff

## Thread Anchor

Ledger epic: `livespec-xei45t`

Owning repo for this plan thread: `livespec`

Plan thread path: `plan/cloud-local-memory-cleanup/`

Purpose: clean up incorrect Claude/Codex local-memory usage across livespec
fleet members and registered adopters, migrate durable guidance to the owning
repo's durable instruction/spec/work-item home, and add mechanical enforcement
so harness-private local memory cannot silently become project memory.

## Read First

Before acting, read these files in this order:

1. `AGENTS.md` §"Agent-instruction `.ai/` convention"
2. `.ai/agent-disciplines.md` §"No local memory" and §"Planning-lane continuation rule"
3. `SPECIFICATION/contracts.md` §"Driver-shipped hooks"
4. `SPECIFICATION/contracts.md` §"Fleet agent-instruction core"
5. `.livespec-fleet-manifest.jsonc`
6. `plan/cloud-local-memory-cleanup/research/initial-inventory.md`
7. `plan/cloud-local-memory-cleanup/research/2026-07-13-inventory-classification.md`

Then refresh the live ledger state through the read-only operation:

```text
/livespec-orchestrator-beads-fabro:list-work-items --json
```

Filter that output for `livespec-xei45t` plus the replacement slice ids listed
below.

## Current State

The epic `livespec-xei45t` has been groomed and regroomed out. Its current
state in the `livespec` ledger is `done` with resolution
`no-longer-applicable`.

The inventory slice `livespec-xhxasg` has now refreshed the host snapshot and
recorded the classification artifact at
`plan/cloud-local-memory-cleanup/research/2026-07-13-inventory-classification.md`.
No Claude or Codex local-memory file was deleted, moved, or edited during this
slice. The slice landed in `livespec` PR #1173, merge
`da9b217028fa64e892bba7f3fd64d818d531aa82`, and `livespec-xhxasg` is now
`done`.

The groomed replacement set is:

| Owning repo | Work item | Current status | Purpose |
|---|---:|---|---|
| `livespec` | `livespec-xhxasg` | `done` | Inventory and classify harness-local memory records for fleet/adopters |
| `livespec-dev-tooling` | `livespec-dev-tooling-2amr6x` | `pending-approval` | Migrate `livespec-dev-tooling` local memory into durable repo homes |
| `livespec-driver-claude` | `livespec-driver-claude-vx6gmo` | `pending-approval` | Migrate `livespec-driver-claude` local memory into durable repo homes |
| `livespec-orchestrator-beads-fabro` | `bd-ib-jz62h3` | `pending-approval` | Migrate `livespec-orchestrator-beads-fabro` local memory into durable repo homes |
| `livespec-runtime` | `livespec-runtime-fsumlo` | `pending-approval` | Migrate `livespec-runtime` local memory into durable repo homes |
| `openbrain` | `ob-j5oend` | `pending-approval` | Migrate `openbrain` adopter local memory into durable repo homes |
| `livespec-driver-claude` | `livespec-driver-claude-vxy7io` | `pending-approval` | Verify and repair Claude Driver auto-memory guard |
| `livespec-driver-codex` | `livespec-driver-codex-ctzk3x` | `pending-approval` | Verify and repair Codex Driver local-memory guard and background-memory audit handling |
| `livespec-dev-tooling` | `livespec-dev-tooling-gcpm3y` | `pending-approval` | Implement consumer-side local-memory drift audit |
| `livespec` | `livespec-eclobt` | `pending-approval` | Quarantine or remove migrated local-memory files after durable destinations land |

The non-inventory slices were filed with a dependency on `livespec-xhxasg`; the
inventory dependency is now satisfied. The next load-bearing action is to drive
the dependent migration slices.

Current evidence from this host:

- `livespec` core has no Claude `memory/*.md` files.
- Claude has 95 markdown memory files across other project slugs.
- Fleet/adopter-relevant Claude memory stores exist for
  `livespec-dev-tooling`, `livespec-driver-claude`,
  `livespec-orchestrator-beads-fabro`, `livespec-runtime`, and `openbrain`.
- No Claude memory markdown files were observed for `livespec-driver-codex`,
  `livespec-orchestrator-git-jsonl`, `livespec-console-beads-fabro`, or
  registered adopter `resume`.
- Codex `~/.codex/memories/` contained no files.
- Codex `~/.codex/memories_1.sqlite` existed, with zero `jobs` and zero
  `stage1_outputs` rows at capture time.
- The 67 fleet/adopter-relevant Claude records are all classified in
  `2026-07-13-inventory-classification.md`. The 28 remaining Claude records are
  adjacent/non-governed or historical and are retained out of scope for this
  slice.

The existing contract already bans durable guidance in harness-local memory and
requires driver guards for Claude plus Codex manual writes. The likely gap is
not prose alone; it is migration of existing local files plus mechanical
verification that driver hooks/config/conformance actually prevent recurrence.

Operational correction from the 2026-07-13 Codex session: the installed
`livespec-orchestrator-beads-fabro` groom prose still says the front-end files
nothing until maintainer approval, but `.ai/agent-disciplines.md`
§"Planning-lane continuation rule" now says a resumed handoff is executable
coordination and explicitly includes chaining to `groom`. For this plan-thread
resume shape, do not stop to ask for a separate groom approval; the handoff's
next-action instruction is the authorization to proceed unless the user asked
only for status/review/analysis.

## Next Action

Drive the dependent migration slices that now have a concrete inventory to work
from:

1. `livespec-dev-tooling-2amr6x`
2. `livespec-driver-claude-vx6gmo`
3. `bd-ib-jz62h3`
4. `livespec-runtime-fsumlo`
5. `ob-j5oend`

Then run the guard/audit slices:

1. `livespec-driver-claude-vxy7io`
2. `livespec-driver-codex-ctzk3x`
3. `livespec-dev-tooling-gcpm3y`

Run `livespec-eclobt` only after durable destinations have landed or each source
file has been explicitly classified as ephemeral.

Do not delete any local-memory file before the groomed child item that owns its
content has landed the durable destination or explicitly classified the file as
ephemeral. Do not add a cross-repo check in `livespec-dev-tooling` that reads
downstream repos; read `.ai/no-circular-dependency.md` before designing any
fleet-wide enforcement surface.

## Resume Path

```text
plan/cloud-local-memory-cleanup/handoff.md
```
