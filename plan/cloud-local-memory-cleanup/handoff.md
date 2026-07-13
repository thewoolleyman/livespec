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
| `livespec-dev-tooling` | `livespec-dev-tooling-2amr6x` | `backlog` | Regroom before redispatch; the first factory run used committed repo `.claude/` files as source evidence and was reverted |
| `livespec-driver-claude` | `livespec-driver-claude-vx6gmo` | `pending-approval` | Migrate `livespec-driver-claude` local memory into durable repo homes |
| `livespec-orchestrator-beads-fabro` | `bd-ib-jz62h3` | `pending-approval` | Migrate `livespec-orchestrator-beads-fabro` local memory into durable repo homes |
| `livespec-runtime` | `livespec-runtime-fsumlo` | `pending-approval` | Migrate `livespec-runtime` local memory into durable repo homes |
| `openbrain` | `ob-j5oend` | `pending-approval` | Migrate `openbrain` adopter local memory into durable repo homes |
| `livespec-driver-claude` | `livespec-driver-claude-vxy7io` | `pending-approval` | Verify and repair Claude Driver auto-memory guard |
| `livespec-driver-codex` | `livespec-driver-codex-ctzk3x` | `pending-approval` | Verify and repair Codex Driver local-memory guard and background-memory audit handling |
| `livespec-dev-tooling` | `livespec-dev-tooling-dgin5n` | `backlog` | Regroom source-evidence guard work; first dispatch produced an unwired helper and was not published |
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

## 2026-07-13 Wrong-Scope Migration Incident

`livespec-dev-tooling-2amr6x` was dispatched once before the source-evidence
guard existed. That factory run opened and merged `livespec-dev-tooling` PR
#364 (`2bdeb2cd6546e0baadad36171a73a536ee69ebc1`) and incorrectly treated
committed repo `.claude/` files as if they were host-local Claude memory source
records. That was wrong: committed `.claude/CLAUDE.md`, `.claude/settings.json`,
and `.claude/hooks/*` are repo-owned runtime/config files and were already in
their correct committed location. The cleanup scope is only harness-private
local-memory stores such as `~/.claude/projects/<slug>/memory/*.md` and Codex
local/background memory surfaces.

The bad `livespec-dev-tooling` change was reverted by PR #365, merge
`a5e7a33622780276c814bd4deef8b759a8b98d09`. The `livespec-dev-tooling`
primary checkout was refreshed to that merge and the revert worktree was
removed.

The same session audited current-day history across these repos:
`livespec`, `livespec-dev-tooling`, `livespec-driver-claude`,
`livespec-driver-codex`, `livespec-orchestrator-beads-fabro`,
`livespec-orchestrator-git-jsonl`, `livespec-runtime`,
`livespec-console-beads-fabro`, `openbrain`, and `resume`. The searched paths
were `AGENTS.md`, `.ai`, `plan/cloud-local-memory-cleanup`,
`.claude/CLAUDE.md`, `.claude/settings.json`, and `.claude/hooks`. The only
wrong-scope migration commit found was `livespec-dev-tooling` PR #364; no other
fleet or adopter repo showed the same bad committed `.claude/` migration.

Root-cause status:

- Existing Driver guards prevent new writes into Claude/Codex local-memory
  stores. They do not prevent this incident by themselves, because this incident
  was a wrong-source migration decision and committed repo `.claude/` files are
  legitimate tracked files.
- `livespec-dev-tooling-dgin5n` was filed and dispatched to add source-evidence
  validation. The dispatch produced a useful predicate and tests in its sandbox,
  but the Fabro wrapper wedged after green validation and no PR was opened. More
  importantly, that output was only a helper, not an enforced conformance or
  acceptance path. The item was moved back to `backlog` with a note to fold the
  predicate into the real guard.
- `livespec-dev-tooling-gcpm3y` now carries the root-cause prevention
  requirement: the consumer-side drift/acceptance audit must accept only
  explicit host-local Claude memory records under
  `~/.claude/projects/<slug>/memory/*.md` or explicit Codex memory/database
  audit surfaces; committed checkout `.claude/*` files must not count; empty or
  unavailable source evidence must fail closed or route to regroom with an
  attached source bundle. Keep this local-vantage only, with no
  `livespec-dev-tooling` upstream-to-downstream repo reads.

## Next Action

Do not dispatch any remaining migration slice until the root-cause guard is
landed or the slice has been regroomed with an explicit source bundle. A factory
or sandbox worker that cannot see the host-local source records must fail closed;
it must not infer source content from committed repo `.claude/` files.

Immediate next actions:

1. Drive or regroom `livespec-dev-tooling-gcpm3y` so the consumer-side
   local-memory drift/acceptance audit mechanically enforces the source-evidence
   rule above.
2. Regroom `livespec-dev-tooling-2amr6x` with explicit source evidence from
   `~/.claude/projects/-data-projects-livespec-dev-tooling/memory/*.md`; do not
   redispatch the old item text.
3. Regroom the remaining migration slices
   (`livespec-driver-claude-vx6gmo`, `bd-ib-jz62h3`,
   `livespec-runtime-fsumlo`, `ob-j5oend`) so each carries either an attached
   host-local source bundle or an explicit fail-closed instruction.
4. Then run the Driver hook/audit slices:
   `livespec-driver-claude-vxy7io`,
   `livespec-driver-codex-ctzk3x`, and the landed form of
   `livespec-dev-tooling-gcpm3y`.

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
