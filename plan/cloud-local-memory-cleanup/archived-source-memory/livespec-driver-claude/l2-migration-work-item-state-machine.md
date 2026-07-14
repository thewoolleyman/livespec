---
name: l2-migration-work-item-state-machine
description: The work-item-state-machine L2 beads-tenant migration is DONE (statuses + rank backfill); records the 1Password wrapper used for tenant-touching bd commands.
metadata: 
  node_type: memory
  type: project
  originSessionId: 82f7ca7d-c140-4114-a25f-ba9591e12c3d
---

The **work-item-state-machine L2 migration** of this repo's beads tenant is
**COMPLETE** (landed on master via PR #69, merge `2bf1cf47`, 2026-06-29).

What was done (thin migration-only track; Driver→orchestrator zero-deps, so
no repo code/spec change — decisions 42/46):
- Registered the 5 custom livespec statuses (decision 36):
  `backlog,pending-approval,ready:active,active:wip,acceptance:wip`.
- Backfilled the required `rank` field across the 6 pre-migration items via
  the orchestrator `rebalance-ranks` legacy-seed (`priority→captured_at→id`,
  decision 39) → ranks `a0..a5`; all 8 tenant items now carry a real,
  non-sentinel rank; zero sentinel violations.
- Ledger anchors (in the `livespec-driver-claude` tenant): epic
  **`livespec-driver-claude-wqyfbj`** (open, `backlog`) ← typed-`--parent`
  child task **`livespec-driver-claude-3sunx4`** (now `closed`/`done`,
  `resolution:completed`, audit carries merge_sha + pr_number=69).
- Captured in repo history as the `plan/work-item-state-machine/` thread
  (record + handoff). Prose-linked to fleet anchor `livespec-35s3zo` (never
  a typed cross-tenant `depends_on`, decision 45).
- The parent epic is left OPEN; closing it + archiving the thread is a
  FLEET-level action the overseer performs at the epic's exit gate.

**Credential sourcing (non-obvious; reference):** `BEADS_DOLT_PASSWORD` is
NOT in the session env. Every tenant-touching command (bd,
register_custom_statuses, rebalance-ranks) MUST be prefixed with the fleet
1Password env wrapper:
`source /data/projects/1password-env-wrapper/with-livespec-env.sh <command>`,
e.g. `source …/with-livespec-env.sh bd -C /data/projects/livespec-driver-claude list`.
The wrapper injects the tenant password from 1Password. PROBE-ONLY — never
echo it (`printenv NAME | wc -c` at most). The tenant is selected by
`bd -C <this-repo>` via `.beads/config.yaml`. Pass `-C <path>` literally
(a shell variable mis-splits through the wrapper).

**Orchestrator tooling:** the migration was driven against
`livespec-orchestrator-beads-fabro` **v0.3.0** directly from the source repo
(`/data/projects/livespec-orchestrator-beads-fabro/.claude-plugin/scripts`
+ `_vendor` on sys.path) — no committed orchestrator version pin exists in
this repo (the marketplace ref is untagged). NOTE the shipped
`capture-work-item`/`plan` prose is STALE for v0.3.0 (still shows
`status="open"` + `priority=…`, no `rank`); construct work-items against the
real `types.WorkItem` schema instead (the console precedent, decision 41).
