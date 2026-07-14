# Cloud-Local Memory Cleanup — Initial Inventory

Snapshot captured from `/data/projects/livespec` on 2026-07-13 while opening
the `plan/cloud-local-memory-cleanup/` planning thread.

## Scope

The maintainer asked for a side-quest plan to clean up incorrect local-memory
files for all livespec fleet family members and registered adopters, then ensure
future durable guidance is mechanically routed away from Claude- or
Codex-specific local memory.

The governing contract is:

- `AGENTS.md` §"Agent-instruction `.ai/` convention"
- `.ai/agent-disciplines.md` §"No local memory"
- `SPECIFICATION/contracts.md` §"Driver-shipped hooks"
- `SPECIFICATION/contracts.md` §"Fleet agent-instruction core"
- `.livespec-fleet-manifest.jsonc`

## Fleet And Registered Adopter Set

From `.livespec-fleet-manifest.jsonc` at capture time:

Fleet members:

- `livespec`
- `livespec-dev-tooling`
- `livespec-driver-claude`
- `livespec-driver-codex`
- `livespec-orchestrator-beads-fabro`
- `livespec-orchestrator-git-jsonl`
- `livespec-runtime`
- `livespec-console-beads-fabro`

Registered adopters:

- `openbrain`
- `resume`

## Claude Local-Memory Snapshot

Command:

```bash
find /home/ubuntu/.claude/projects -maxdepth 3 -type f -path '*/memory/*.md' -print | sort
```

Result: 95 markdown files under Claude project-local memory stores.

Grouped counts:

- 3 files under `-data-projects-beads`
- 3 files under `-data-projects-kilroy`
- 9 files under `-data-projects-livespec-dev-tooling`
- 2 files under `-data-projects-livespec-driver-claude`
- 8 files under `-data-projects-livespec-impl-plaintext`
- 2 files under `-data-projects-livespec-orchestrator-beads-fabro`
- 7 files under `-data-projects-livespec-runtime`
- 47 files under `-data-projects-openbrain`
- 10 files under `-data-projects-vps-info`
- 1 file under `-home-ubuntu-gt-personal-knowledge-base-polecats-quartz-personal-knowledge-base`
- 2 files under `-home-ubuntu-gt-personal-knowledge-base-refinery-rig`
- 1 file under `-home-ubuntu-tmp`

Important finding: `/home/ubuntu/.claude/projects/-data-projects-livespec/`
exists, but no `memory/*.md` files were present for `livespec` core at capture
time. The proof against the earlier root-cause claim is therefore local and
concrete: Claude was not relying on a hidden `livespec` memory file to behave
better in this repo.

Fleet/adopter-owned Claude memory stores that need audit first:

- `livespec-dev-tooling`
- `livespec-driver-claude`
- `livespec-orchestrator-beads-fabro`
- `livespec-runtime`
- `openbrain`

Possibly adjacent or historical stores that need classification before cleanup:

- `livespec-impl-plaintext`
- `beads`
- `kilroy`
- `vps-info`
- personal-knowledge-base slugs
- `/home/ubuntu/tmp`

The missing fleet/adopter stores at capture time are as important as the present
ones: no Claude memory markdown files were observed for `livespec`,
`livespec-driver-codex`, `livespec-orchestrator-git-jsonl`,
`livespec-console-beads-fabro`, or registered adopter `resume`.

## Codex Local-Memory Snapshot

Commands:

```bash
find /home/ubuntu/.codex/memories -maxdepth 3 -type f -print
sqlite3 /home/ubuntu/.codex/memories_1.sqlite '.tables'
sqlite3 /home/ubuntu/.codex/memories_1.sqlite 'select count(*) from jobs; select count(*) from stage1_outputs;'
```

Result:

- `/home/ubuntu/.codex/memories/` existed but contained no files.
- `/home/ubuntu/.codex/memories_1.sqlite` existed.
- SQLite tables present: `_sqlx_migrations`, `jobs`, `stage1_outputs`.
- `jobs` row count: 0.
- `stage1_outputs` row count: 0.

This matches `SPECIFICATION/contracts.md` §"Codex auto-memory-write guard
(required)": the manual-write guard can block explicit writes under
`~/.codex/memories/`, but Codex background-generated memories are outside
`pre_tool_use`. On this host the database was empty at capture time, but the
enforcement design still needs to account for that runtime limitation.

## Current Contract Baseline

Current `SPECIFICATION/contracts.md` already requires:

- Claude Driver `block-auto-memory.sh` to deny writes to
  `~/.claude/projects/<slug>/memory/*.md` in livespec-governed projects and
  intent-route the content to `capture-work-item`, `/livespec:propose-change`,
  or `AGENTS.md` / `.ai/<topic>.md`.
- Codex Driver auto-memory-write guard to deny manual writes under
  `~/.codex/memories/` in livespec-governed projects and intent-route the same
  way.
- The known Codex limitation that background-generated memories are outside the
  hook lifecycle.
- Durable guidance belongs in `AGENTS.md` and referenced `.ai/<topic>.md`, not
  in harness-private local memory.

The cleanup plan therefore must not merely add another prose rule. It needs to
verify driver hook implementations and add a mechanical fleet/adopter audit path
for already-existing local-memory stores.

## Open Design Questions For Grooming

- Which files are durable guidance that should migrate to each owning repo's
  `AGENTS.md` or `.ai/*.md`, versus trackable work that belongs in that repo's
  ledger, versus genuinely ephemeral scratch?
- Which non-livespec slugs are governed adopters, historical fleet repos, or
  unrelated local projects that should stay outside livespec enforcement?
- Should stale harness-local memory be deleted directly after migration, moved
  to a quarantine path, or left in place with a dated cleanup marker until the
  owning repo PR lands?
- What is the right mechanical guard for Codex background-generated memories:
  host-level config, a livespec doctor/conformance check that reports the store
  as contaminated, or both?
- Which repository owns each enforcement change: `livespec` core for contract,
  `livespec-driver-claude` and `livespec-driver-codex` for runtime hooks, and
  `livespec-dev-tooling` or consumer-side checks for fleet/adopter conformance?
