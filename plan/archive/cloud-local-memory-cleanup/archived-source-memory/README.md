# Archived fleet host-local Claude memory snapshots

These are **verbatim snapshots** (captured **2026-07-14**) of the
harness-private Claude local-memory files
(`~/.claude/projects/<slug>/memory/*.md`) for the FLEET repos listed
below. During the cloud-local-memory cleanup (epic **livespec-xei45t**),
the durable content of these files was reconciled into each repo's proper
homes — `AGENTS.md` and its sibling `.ai/<topic>.md` files, per the
`.ai/` agent-instruction convention — and the harness-private local-memory
copies are being **deleted** from local memory by **livespec-eclobt**.

These snapshots are retained here **for reference ONLY** — they are **NOT
active guidance**. The durable, authoritative guidance for each repo lives
in that repo's `AGENTS.md` / `.ai/` tree, not here. Do not treat anything
in this directory as an instruction to follow; it is a frozen record of
what the local-memory stores held immediately before deletion, kept so the
reconciliation is auditable.

## What was captured

One subdirectory per source repo slug, each holding that repo's
`~/.claude/projects/<slug>/memory/*.md` files exactly as they were on
2026-07-14:

| Subdir | Source local-memory store | Files |
|---|---|---|
| `livespec-dev-tooling/` | `~/.claude/projects/-data-projects-livespec-dev-tooling/memory/` | 9 |
| `livespec-driver-claude/` | `~/.claude/projects/-data-projects-livespec-driver-claude/memory/` | 2 |
| `livespec-runtime/` | `~/.claude/projects/-data-projects-livespec-runtime/memory/` | 7 |
| `livespec-orchestrator-beads-fabro/` | `~/.claude/projects/-data-projects-livespec-orchestrator-beads-fabro/memory/` | 2 |

Each subdir includes that store's `MEMORY.md` index alongside the
individual memory files it pointed at.

## Not included here

- **openbrain** — its host-local memory is archived separately into
  **openbrain's own repo**, not here.
- Fleet repos with **zero** local-memory files at capture time
  (`livespec` core, `livespec-driver-codex`,
  `livespec-orchestrator-git-jsonl`, `livespec-console-beads-fabro`, and
  `livespec-resume`) contribute nothing to this archive.
