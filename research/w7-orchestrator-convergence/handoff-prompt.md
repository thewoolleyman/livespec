# W7 orchestrator convergence handoff prompt

You are resuming W7 orchestrator-reference convergence in `/data/projects/livespec`.
This handoff owns the active W7 continuation state. Do not put W7 execution
state in `research/codex-support/handoff-prompt.md`; that file is for the
Codex-support track only.

## Current state as of 2026-06-20 (step 3 COMPLETE; steps 4–5 remain)

W7 step 2 (golden-master acceptance) was already done. **Step 3 (the memo kill)
is now COMPLETE across all four repos**, plus the diagram/template remainder
(`livespec-b91b`) is disposed. The remaining W7 work is **step 4 (shared `Store`
extraction)** and **step 5 (container real-work substrate)**, then close
`livespec-zkmn.1` → `livespec-zkmn`.

### Step 3 — memo kill: DONE

Memo is fully retired as a named surface. All in-flight captures now flow to the
work-item ledger (`capture-work-item`), spec input to `/livespec:propose-change`
(`capture-spec-drift`), and durable lessons to the orchestrator's `lessons.md`
(NOT the ledger) — user-confirmed 2026-06-20. The `.ai/` persistent-knowledge
slot + the reflector were preserved. Closed work-items + landed PRs:

- `livespec-gjn4` (core spec) — CLOSED. PR #497 → `SPECIFICATION/history/v123`.
  Retargeted the `block-auto-memory` redirect contract (`contracts.md`
  §"Driver-shipped hooks") `capture-memo` → `capture-work-item`; reworded
  `spec.md` §"Terminology" Transient entry (kept the load-bearing
  transient-vs-durable-pending principle). `contracts.md:142` keeps "memos" as a
  doctor-boundary EXAMPLE intentionally (a contract test pins it).
- `livespec-zkmn.1.3` (Driver `livespec-driver-claude`) — CLOSED. PR #23, merge
  `ac14f9e`, Driver spec → `history/v001`. Retargeted `block-auto-memory.sh` +
  its own SPECIFICATION (contracts hook desc + scenario H2 rename, heading-coverage
  co-edit) + `tests/hooks/test_block_auto_memory.py`. (This Driver item was NOT in
  the original plan — surfaced during the kill; the redirect contract is core's but
  the SCRIPT lives in the Driver repo.)
- `livespec-d4j3` (`livespec-impl-git-jsonl`) — CLOSED. Deletion `9eee8b1` +
  stale-CLAUDE.md-ref cleanup `c169217`. master CI green.
- `livespec-kfiz` (`livespec-impl-beads`) — CLOSED. PR #102 (deletion `ee8eff9`
  + dev-tooling pin bump `b9f29b7`) + PR #103 (stale-CLAUDE.md-ref cleanup
  `80dbf71`). master CI green.

### Gate fix landed this session — `livespec-dev-tooling` v0.14.1

The memo deletion exposed a real bug in dev-tooling's `check_coverage_incremental`:
its no-`--paths` derive used `git diff --name-only origin/master...HEAD` WITHOUT a
deletion filter, so a deletion-only commit fed the DELETED impl `.py` to the
mirror-test resolver and hard-failed (the mirror test is correctly also deleted).
This blocked every deletion-only commit at LOCAL pre-push (CI didn't catch it —
the post-merge diff is empty). Fixed the gate, not the bypass: PR #138 added
`--diff-filter=d` (RGR-tested), released as tag **`v0.14.1`**. `livespec-impl-beads`
now pins `v0.14.1`; other family repos still on their prior pin — the fix is
backward-compatible, so they can bump opportunistically. (NOTE: an earlier
parallel session `--no-verify`'d the git-jsonl deletion during an Anthropic API
overload, before the gate was fixed — that is why git-jsonl `9eee8b1` exists with
the `thewoolleyman` author identity; not a human action.)

### `livespec-b91b` (diagram/template remainder) — DONE (descoped)

Both remainders descoped with rationale (b91b acceptance permits descope):
(1) the built-in template v1→v2 `spec_files` manifest bump is NOT a clean 1-repo
change — `spec.md:55` requires `heading_coverage` (upstream in `livespec-dev-tooling`)
to consult the manifest under v2, and it still uses a hardcoded tuple; relocated
to **`livespec-cuiz`** (P3, post-W7, dev-tooling-first ordering; latent/harmless
until a v2 template exists). (2) the Mermaid syntax lint is descoped —
`spec.md:209` says it is a CI nicety, NOT a contract requirement.

## Remaining W7 work (under `livespec-zkmn.1`)

### Step 4 — shared `Store` extraction (READY)

Work-items: `livespec-4jsi` (extract, in `livespec-runtime`) → blocks
`livespec-6a4n` (impl-beads consume) + `livespec-5g4i` (impl-git-jsonl consume).

Design intent (from `plan.md` §B) — **do a design pass FIRST**:
- Home = **`livespec-runtime`** (both impls already depend on it `v0.3.0` + vendor
  under `_vendor/`). NOT core. NO new package.
- Move (shared once): the `WorkItem` data model (currently duplicated per-repo) +
  a `Store` interface (`typing.Protocol`: `read_work_items` / `append_work_item` /
  `materialize_work_items` / comments) + genuinely-identical pure logic
  (materialize/head-reduction, identity, validation). **No `Memo`** — it's gone now,
  so the extracted protocol is memo-free (this is why step 4 follows step 3).
- Stays per-impl (the "fill"): backend I/O — impl-beads → Beads/Dolt via `bd`;
  impl-git-jsonl → JSONL files. Each just IMPLEMENTS the shared interface.
- **Two real divergences to converge** (scope these before coding): the config/param
  type (`StoreConfig` vs `Path`) and the comments API. Compare the two impls'
  `store.py`/`types.py` (now memo-free) side by side.
- **Atomic version-bump fan-out** — bump `livespec-runtime`, then pin-and-bump BOTH
  consumers together. Watch the **schema-tightening-breaks-shared-wrapper hazard**
  (making a shared key required breaks `list_work_items` on every sibling store until
  each is backfilled — backfill both together). The dev-tooling v0.14.1 deletion-filter
  fix means file-deletion churn in the consumers won't trip pre-push.

### Step 5 — container real-work substrate (READY)

Work-item: `livespec-pe9u` (impl-beads). Promote the containerized Beads/Dolt+Fabro
orchestrator from Tier-2 proof runner to the real-work substrate: real work clones
repos fresh from GitHub; host coupling reduced to secret provisioning + explicitly
injected externals; byte-count-only secret hygiene; gate on `just check` +
`just acceptance`. More self-contained than step 4 (single repo, no fan-out).

### Close-out

Once `4jsi`/`6a4n`/`5g4i` (step 4) and `pe9u` (step 5) land, close
`livespec-zkmn.1` then `livespec-zkmn` — which unblocks the orchestrator rename
wave `livespec-4moata.4` (drop `impl-` → `orchestrator-`; playbook at
`tmp/orchestrator-rename-kickoff-prompt.md`). Do NOT start the rename mid-W7.

## Next action

Step 3 is COMPLETE. Proceed to step 4, starting with a divergence-convergence
design pass (`StoreConfig`-vs-`Path` + comments API) over the two impls' now-memo-free
`store.py`/`types.py`, then extract into `livespec-runtime` and fan the version bump
out to both consumers atomically. Step 5 (`pe9u`) is independent and can go in
parallel (separate repo concern from step 4's runtime extraction, though both touch
impl-beads — sequence impl-beads PRs to avoid worktree collisions).

## Work discipline

Every tracked repo change uses worktree → PR → merge → cleanup. Use
`mise exec -- git ...` so hooks run, never pass `--no-verify` (fix the gate, not the
bypass — see the dev-tooling v0.14.1 fix above for the pattern), and do not leave
dirty primary checkouts or orphaned worktrees. Verify cross-repo state via
`git -C <clone> show origin/master:<path>` / `git grep origin/master` — a parallel
session has touched this epic, so do not trust local working trees or agent idle
pings; confirm merges independently. Spec-side changes (incl. each impl's OWN
SPECIFICATION) are dogfooded via `/livespec:propose-change` → `/livespec:revise`
(drive the core CLIs at `.claude-plugin/scripts/bin/` with `--project-root` pointed
at the worktree; co-edit `tests/heading-coverage.json` on any H2 change). If a future
session must stop, update this file with the active worktree path, branch, PR,
validation state, and next action.
