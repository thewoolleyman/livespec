# Handoff — work-item-state-machine (FLEET COORDINATOR)

This is the single resumable entry point for a fresh session resuming the
**work-item lifecycle epic rollout**. You are the **fleet coordinator +
anchor** for a multi-repo epic whose design is fully locked. A fresh session
can execute the next action from this file alone via the read-first chain —
no chat history required.

## What this thread is

The design of livespec's **deterministic work-item lifecycle state machine**
is **COMPLETE** (decisions 1–46): A–H design walk done; design doc
re-synthesized; the **slice plan + execution structure are persisted**
(`research/04-slice-plan.md`). The epic is now in **ROLLOUT**: it is decomposed
into dependency-layered, per-repo tracks, each run in its OWN tmux session as
its OWN `/livespec-orchestrator-beads-fabro:plan` thread (own epic, own beads
tenant, prose-linked to the core anchor). **L0 (the foundation track) has been
kicked off.**

**Your role (coordinator):** drive the rollout in `research/04-slice-plan.md`,
foundation-first. Run a **lightweight manual overseer** — INFORMED BY
`.claude/skills/overseer/` but do NOT invoke it or stand up its three-pane
dashboard (decision 45; it is the heavy, throwaway part this epic deletes).
Adopt only: the **status table** (`Epic · Track · Status · %Complete`) printed
in THIS pane before any gate/status; the **anti-stall discipline** (never
freeze the coordinator on one track; keep others self-sustaining; never park a
track on a non-blocker; decide-and-inform for reversible/in-intent calls);
`command tmux send-keys` kickoff; and the cross-repo brief discipline (a
cold-startable brief per repo under `briefs/`, status from the ledger, no
shadow queue).

## Status (read from the ledger — never from this file)

- **Core anchor epic:** `livespec-35s3zo` (livespec core tenant). 0 children —
  the per-track epics live in their OWN tenants, prose-linked. Check live:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-35s3zo
  ```
  *(Hygiene TODO: its DESCRIPTION still lists the old state set
  `…/deferred/…` with no `pending-approval`; update it to the 7 locked states
  next time the anchor is touched — a `bd update` on the core tenant.)*
- **L0 — `livespec-runtime` track:** KICKED OFF and wrapped to a clean stop.
  Runtime-tenant epic **`livespec-runtime-l4yojx`** (prose-linked to
  `livespec-35s3zo`). Its full state + exact next action live in **its OWN
  thread handoff** at
  `/data/projects/livespec-runtime/plan/work-item-state-machine/handoff.md`.
  It drafted (NOT authored on disk, NOT coded) the propose-change findings
  (`…/research/02-propose-change-findings.json`) + the code-slice breakdown
  (`…/research/03-code-slices.md`), and is parked at the maintainer-owned
  **revise + groom** gate. Its surfaced next action:
  `/livespec:propose-change work-item-lifecycle-l0 --findings-json …` →
  `/livespec:revise` → `groom` `research/03-code-slices.md` into ready children
  of `livespec-runtime-l4yojx` → implement (red-green-replay) → cut the
  `livespec-runtime` release.
- **Console track (exists):** epic `livespec-console-beads-fabro-vqh36l`
  (console tenant), thread `plan/work-item-lifecycle-redesign/` in
  `/data/projects/livespec-console-beads-fabro` — open, groom-pending.
- **All other tracks: not started** (cleanly unstarted; gated per the layers).

## The next action

**Continue the rollout (foundation-first), in this order:**

1. **L0 maintainer gate (immediate).** The runtime track has drafted its
   propose-change + code-slice breakdown and is parked at the maintainer-owned
   **`revise` (spec ratification) + `groom` (the cut)** gate. Read the runtime
   track's own handoff (above), then drive that gate with the maintainer:
   author the propose-change on disk (`/livespec:propose-change` in the runtime
   repo) → `/livespec:revise` to ratify → `groom` the L0 epic into ready
   slices → implement (the runtime repo's red-green-replay TDD) → **cut a
   `livespec-runtime` release** (the artifact L1 vendors).
2. **Fan out L1 once L0 is releasing.** Author L1a/L1b kickoff briefs under
   `briefs/` (use `briefs/l0-runtime.md` as the template; their slices are in
   `04-slice-plan.md`), land them on master, and kick off the
   `livespec-orchestrator-beads-fabro` and `livespec-orchestrator-git-jsonl`
   sessions. Their SPEC propose-changes can start in parallel with L0; their
   CODE gates on the L0 release.
3. **Then L2 + console.** After L1 releases: author + kick off the `openbrain`
   (adopter), `livespec-dev-tooling`, `livespec-driver-claude`,
   `livespec-driver-codex` thin migration tracks; the console track (existing
   thread) consumes the L1a lane emission.
4. **Exit gate:** delete `.claude/skills/overseer/` once the new system is
   dogfooded — `livespec-35s3zo` is NOT done until this lands.

**Kickoff mechanics** (per track): land a cold-startable brief under `briefs/`
(template: `briefs/l0-runtime.md`), confirm the repo is clean + on master +
the orchestrator plugin enabled + its tenant reachable, then:
```bash
command tmux send-keys -t <session> -l "read /data/projects/livespec/plan/work-item-state-machine/briefs/<brief>.md and follow it. Start now."
sleep 0.6; command tmux send-keys -t <session> Enter
# verify it submitted (capture the pane; re-send Enter if it shows [Pasted text])
```
All required sessions already exist: `livespec-runtime`,
`livespec-orchestrator-beads-fabro`, `livespec-orchestrator-git-jsonl`,
`livespec-console-beads-fabro`, `openbrain`, `livespec-dev-tooling`,
`livespec-driver-claude`, `livespec-driver-codex`.

## Track table (refresh from the ledger before acting)

| Layer | Track (session) | Epic | Status |
|---|---|---|---|
| anchor | livespec (core) | `livespec-35s3zo` | coordinating |
| L0 | livespec-runtime | `livespec-runtime-l4yojx` | kicked off · maintainer revise/groom gate |
| L1a | livespec-orchestrator-beads-fabro | — | not started (spec can start; code gated on L0 release) |
| L1b | livespec-orchestrator-git-jsonl | — | not started (spec can start; code gated on L0 release) |
| console | livespec-console-beads-fabro | `…-vqh36l` | open · groom-pending (gated on L1a lane emission) |
| L2 | openbrain (adopter) | — | not started (gated on L1 releases) |
| L2 | livespec-dev-tooling / driver-claude / driver-codex | — | not started · thin migration-only (gated on L1) |

## Read-first chain (in order)

1. **`research/04-slice-plan.md`** — START HERE; the execution structure
   (tracks, layers, per-repo routing, the per-repo-session model). Its trail
   is decisions 44–46.
2. **`research/03-decision-log.md`** — authoritative on the DESIGN (decisions
   1–46; 44–46 = session-6 execution structure).
3. **`research/02-design.md`** — the design of record (current).
4. **`briefs/l0-runtime.md`** — the L0 kickoff brief + the template for every
   per-repo brief.
5. **`research/01-prior-art.md`** — external grounding.
6. **`conversation/transcript.md`** — verbatim session-1 design discussion.
7. **Per-track handoffs (each track's own state):** the L0 runtime track's
   handoff (`/data/projects/livespec-runtime/plan/work-item-state-machine/handoff.md`);
   the console thread (`/data/projects/livespec-console-beads-fabro/plan/work-item-lifecycle-redesign/handoff.md`).

## The locked model (the spine for every track)

- **Seven stored states:** `backlog · pending-approval · ready · active ·
  acceptance · blocked · done`. Single derived overlay: `ready` + open dep →
  `blocked:dependency` (auto-clears). "Receipt" retired.
- **Grooming = `backlog → pending-approval`**; **approval = `pending-approval →
  ready`**. `defer` → `pending-approval`; `bounce`/`reject(re-groom)` → `backlog`.
- **Acceptance is POST-MERGE / in-production** (decision 33): ship-on-green,
  then AI/human confirm the shipped artifact vs tests + telemetry; `reject` =
  revert/fix-forward. `just check` stays the pre-merge floor.
- **Ownership = the existing `assignee` field** (decision 35): zero migration,
  set by the Dispatcher on `admit`, invariant `active ⟹ assignee`.
- **WIP cap is per-repo** (`.livespec.jsonc`, default 5; fleet total = sum).
- **`rank`** (decisions 38–39): a strictly-required NON-NULL `str` fractional
  key, the sole order. PORT (verbatim CC0 copy) of the rocicorp/httpie
  fractional-index module → `livespec_runtime/work_items/_fractional_indexing.py`
  behind a `rank.py` wrapper. Backfill across all **9** tenants from
  `priority → captured_at → id` via `n_keys_between`, reusing `rebalance-ranks`
  (legacy-seeded); `priority` dropped (no scrub). Store adapter substitutes a
  bottom-sentinel (`"~"`) for legacy lines; doctor invariant: every live item
  has a real rank. Rebalance on-demand only (decision 38 G-2) + a doctor
  key-length warning.
- **Beads encoding** (decision 36, vs v1.0.5): 5 custom statuses
  (`backlog`, `pending-approval`, `ready:active`, `active:wip`, `acceptance:wip`)
  + 2 built-in reuses (`blocked`; `done`→`closed`). `bd create` forces `open`,
  so `append_work_item` is a 2-step create+update.
- **`lane_of`** (decisions 40 + 42): `lane_of(*, item, index, manifest) -> Lane`
  (`Lane = {name, reason}`), net-new in `livespec_runtime/work_items/lifecycle.py`
  as the single authority, with `is_item_ready` + `ready_sort_key` (keyed on
  `rank`) **pure-core-relocated + backend-lookup-injected** (no runtime→beads
  back-edge). `list-work-items --json` emits flat `lane` + `lane_reason`; the
  console CONSUMES them.
- **Spec-routing reframe** (decision 44): the contract lives in the
  `livespec-runtime` + orchestrator `SPECIFICATION`s, **NOT** CORE (CORE's spec
  delegates the whole surface). The epic is anchored in core, but core is the
  anchor, not the work site.
- **Tenant scope = 9** (decision 46): the 8 fleet tenants + the `openbrain`
  adopter; drivers + dev-tooling are migration-only (zero-dep) thin tracks.

## Beads ground-truth (for any further beads research)

- Canonical beads origin is **`github.com/gastownhall/beads`**; local clone at
  `/data/projects/beads`, parked at tag **v1.0.5** (the livespec-pinned
  version). Custom statuses + categories are real; 7 built-ins; no
  status-transition enforcement; `bd create` forces `open`/`deferred`.

## Hard exit gate for the epic

`livespec-35s3zo` is NOT done until the local **overseer skill**
(`.claude/skills/overseer/`) is **deleted** — it keeps running until the new
system is dogfooded, then is removed as the final step.

## Resume command

```
/livespec-orchestrator-beads-fabro:plan work-item-state-machine
```
