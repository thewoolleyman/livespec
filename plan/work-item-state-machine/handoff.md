# Handoff — work-item-state-machine planning thread

This is the single resumable entry point for this planning thread. A
fresh session can execute the next action from this file alone by
following the read-first chain below — no chat history required.

## What this thread is

The design of livespec's **deterministic work-item lifecycle state
machine** — turning the implicit, scattered lifecycle into ONE explicit
state machine with two human-delegable WIP valves. **No implementation has
started.** The A–H design walk is **COMPLETE** (decisions 1–43): A, B, C,
D (all sub-items), E, F, G, H are all resolved. **Item E (the console
redesign) was DELEGATED to a console-repo plan thread and is itself
complete** (see decision 41). The post-walk **design-doc re-synthesis is
DONE** (`research/02-design.md` §§1–10 reflect decisions 1–43), and the
**slice plan is DRAFTED + APPROVED** (`research/04-slice-plan.md`, decisions
44–46): the cut into dependency-layered per-repo tracks, the spec-routing
reframe (CORE barely touched; the contract lives in the runtime +
orchestrator `SPECIFICATION`s), the 9-tenant migration scope (incl. the
OpenBrain adopter + thin driver/dev-tooling migration tracks), and the
per-repo-`/plan`-session execution model coordinated from core. What remains
is to EXECUTE that rollout, below.

## Status (read from the ledger — never from this file)

- **Core epic anchor:** `livespec-35s3zo` (livespec core tenant). Check live:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-35s3zo
  ```
- **Console epic (item E, delegated):** `livespec-console-beads-fabro-vqh36l`
  (console tenant), cross-linked to `livespec-35s3zo` by prose. Its thread
  `plan/work-item-lifecycle-redesign/` lives in `/data/projects/livespec-console-beads-fabro`
  (E-1..E-4 resolved + on master).
- Neither epic has child work-items yet — slicing/grooming hasn't begun.

## The next action

**EXECUTE the rollout in `research/04-slice-plan.md`, foundation-first.**
This (core) session is the COORDINATOR + anchor, running a lightweight manual
overseer (informed by `.claude/skills/overseer/`, NOT invoking it; status
table printed in this pane; anti-stall discipline; `tmux send-keys` kickoff).
Each repo's slice runs in its OWN tmux session as its OWN
`/livespec-orchestrator-beads-fabro:plan work-item-state-machine` thread
(own epic, own tenant, prose-linked to `livespec-35s3zo`).

Concrete next steps (see `04-slice-plan.md` for the full per-track slices):
1. **Author + land a cold-startable kickoff brief** for the **L0
   `livespec-runtime`** track (its slice: the `WorkItem` schema +
   `lifecycle.py` + the `rank` port + the `:131` drift fix → propose-change
   to `livespec-runtime/SPECIFICATION/contracts.md`, then code), landed in
   the `livespec-runtime` repo via its worktree→PR.
2. **Kick off the `livespec-runtime` tmux session** into its `/plan` thread
   with that brief; validate the per-repo-session + overseer mechanics on
   this one track first.
3. **Fan out** L1a (`livespec-orchestrator-beads-fabro`) + L1b
   (`livespec-orchestrator-git-jsonl`) spec work in parallel once L0 is
   moving; their code + the console + the L2 migration tracks (OpenBrain +
   the thin driver/dev-tooling tracks) gate on the respective releases.

Grooming each track's epic into *ready* slices is that track's own `groom`
operation (maintainer owns the cut). The console's slices belong to its
existing thread/epic, not the core epic.

## Read-first chain (in order)

1. **`research/04-slice-plan.md`** — START HERE for the NEXT ACTION; the
   execution structure (tracks, layers, per-repo routing, the per-repo-session
   model). Decisions 44–46 in the log are its authoritative trail.
2. **`research/03-decision-log.md`** — authoritative on the DESIGN. Decisions
   1–21 = session-1; 22–32 + the item-A transition table = session-2; 33–37 =
   session-3; 38–40 = session-4; 41–43 = session-5 (E-delegation = 41; F = 42;
   H = 43); **44–46 = session-6** (execution structure: reframe, per-repo
   tracks, 9-tenant scope). "Open items" marks **A–H all ✅**.
3. **`research/02-design.md`** — the design of record, re-synthesized from
   decisions 1–43 (current). The decision log still wins on any residual
   discrepancy (it carries the reasoning trail).
4. **`research/01-prior-art.md`** — external grounding, cited.
5. **`conversation/transcript.md`** — verbatim session-1 design discussion;
   sessions 2–6 reasoning lives in the decision-log entries.
6. **Console thread (item E):** `/data/projects/livespec-console-beads-fabro`
   → `plan/work-item-lifecycle-redesign/handoff.md` + `research/decision-log.md`.

## The locked model so far (the spine for everything)

- **Seven stored states:** `backlog · pending-approval · ready · active ·
  acceptance · blocked · done`. Single derived overlay: `ready` + open dep →
  rendered `blocked:dependency` (auto-clears). "Receipt" retired.
- **Grooming = `backlog → pending-approval`**; **approval = `pending-approval →
  ready`**. `defer` → `pending-approval`; `bounce`/`reject(re-groom)` → `backlog`.
- **Acceptance is POST-MERGE / in-production** (decision 33): ship-on-green, then
  AI/human confirm the shipped artifact vs tests + telemetry; `reject` =
  revert/fix-forward. `just check` stays the pre-merge floor; risk dial is at
  admission + reversibility.
- **Ownership = the existing `assignee` field** (decision 35): kept in place, zero
  migration, set by the Dispatcher on `admit`, invariant `active ⟹ assignee`.
- **WIP cap is per-repo** (`.livespec.jsonc`, default 5; fleet total = sum).
- **`rank`** (decisions 38–39): a strictly-required NON-NULL `str` fractional key,
  the sole order. PORT (verbatim CC0 copy) of the rocicorp/httpie fractional-index
  module → `livespec_runtime/work_items/_fractional_indexing.py` behind a `rank.py`
  wrapper. Backfill across all 9 tenants from `priority → captured_at → id` via
  `n_keys_between`, reusing `rebalance-ranks` (legacy-seeded); `priority` dropped
  (no scrub). Store adapter substitutes a bottom-sentinel (`"~"`) for legacy lines;
  doctor invariant: every live item has a real rank. Rebalance is on-demand only
  (decision 38 G-2) with a doctor key-length warning.
- **Beads encoding** (decision 36, vs v1.0.5): 5 custom statuses
  (`backlog`, `pending-approval`, `ready:active`, `active:wip`, `acceptance:wip`)
  + 2 built-in reuses (`blocked`; `done`→`closed`). `bd create` forces `open`, so
  `append_work_item` is a 2-step create+update.
- **`lane_of`** (decisions 40 + 42): `lane_of(*, item, index, manifest) -> Lane`
  (`Lane = {name: LaneName, reason: BlockedReason | None}`), homed in a new
  `livespec_runtime/work_items/lifecycle.py` as the single authority, with
  `is_item_ready` (= `lane_of(...).name == "ready"`) and `ready_sort_key` (keyed on
  `rank`). Per decision 42 the move is **pure-core-relocated + backend-lookup-injected**
  (no runtime→beads back-edge); `lane_of` is net-new. `list-work-items --json` emits
  flat `lane` + `lane_reason`; the console CONSUMES them (item E).
- **Fleet/blast radius** (decisions 37 + 46): all **9** beads tenants migrate in
  lockstep (the 8 fleet tenants + the `openbrain` adopter); spec+code touches
  `livespec-runtime`, both orchestrators, the console; the drivers + dev-tooling
  are migration-only (zero-dep, thin tracks). The contract lands in the runtime +
  orchestrator `SPECIFICATION`s, NOT CORE (decision 44).

## Beads ground-truth (for any further beads research)

- Canonical beads origin is **`github.com/gastownhall/beads`** (`steveyegge/beads`
  redirects to it). Local clone at `/data/projects/beads`, `upstream` repointed to
  canonical, parked at tag **v1.0.5** (the livespec-pinned version). Verified: custom
  statuses + categories are real; 7 built-ins; no status-transition enforcement;
  `bd create` forces `open`/`deferred`.

## Hard exit gate for the epic

`livespec-35s3zo` is NOT done until the local **overseer skill**
(`.claude/skills/overseer/`) is **deleted** — it keeps running until the new system
is dogfooded, then is removed as the final step.

## Resume command

```
/livespec-orchestrator-beads-fabro:plan work-item-state-machine
```
