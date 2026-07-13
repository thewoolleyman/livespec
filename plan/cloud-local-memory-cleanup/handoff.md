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

Then refresh the live ledger state through the read-only operation:

```text
/livespec-orchestrator-beads-fabro:list-work-items --json
```

Filter that output for `livespec-xei45t`.

## Current State

The epic `livespec-xei45t` is a backlog planning epic, not a dispatchable
implementation slice. It was captured with `admission_policy=manual` and
`acceptance_policy=ai-then-human`.

Initial evidence from this host:

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

The existing contract already bans durable guidance in harness-local memory and
requires driver guards for Claude plus Codex manual writes. The likely gap is
not prose alone; it is migration of existing local files plus mechanical
verification that driver hooks/config/conformance actually prevent recurrence.

## Next Action

Run `/livespec-orchestrator-beads-fabro:groom livespec-xei45t`.

Recommended groom shape:

- First child: inventory and classify every Claude/Codex local-memory record for
  fleet members and registered adopters, with explicit ownership for adjacent
  non-fleet slugs.
- Second child: migrate durable guidance from each governed repo's local memory
  into that repo's `AGENTS.md` / `.ai/*.md`, spec proposal, or work-item ledger
  through normal worktree to PR to merge flow.
- Third child: verify and repair Claude Driver and Codex Driver local-memory
  guards, including Codex background-memory configuration or audit handling.
- Fourth child: add fleet/adopter conformance so future local-memory drift is
  detected mechanically without introducing upstream-to-downstream circular
  reads.
- Final child: perform host cleanup or quarantine of migrated local-memory files
  and document exactly what was removed, retained, or intentionally ignored.

Do not delete any local-memory file before the groomed child item that owns its
content has landed the durable destination or explicitly classified the file as
ephemeral. Do not add a cross-repo check in `livespec-dev-tooling` that reads
downstream repos; read `.ai/no-circular-dependency.md` before designing any
fleet-wide enforcement surface.

## Resume Path

```text
plan/cloud-local-memory-cleanup/handoff.md
```
