# Handoff — work-item-state-machine planning thread

This is the single resumable entry point for this planning thread. A
fresh session can execute the next action from this file alone by
following the read-first chain below — no chat history required.

## What this thread is

The design of livespec's **deterministic work-item lifecycle state
machine** — turning the implicit, scattered lifecycle (intake tags + the
readiness predicate + Dispatcher markers + the `mode` lever + the janitor
gate + the overseer's bash state table) into ONE explicit state machine
with two human-delegable WIP valves. **No implementation has started.**
The design is being driven to a locked, sliceable state by resolving the
open items **A–H one at a time**; **A and B are now locked (session 2);
C–H remain.**

## Status (read from the ledger — never from this file)

- **Epic anchor:** `livespec-35s3zo` (livespec core tenant). Check live:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-35s3zo
  ```
- The epic has **no child work-items** — slicing hasn't begun (it begins
  after the A–H walk completes). The ledger is the only status source;
  this file holds no parallel checklist.

## Read-first chain (in order)

1. **`research/03-decision-log.md`** — START HERE. Decisions 1–21 are
   session-1; **decisions 22–32 + the "Locked transition table (item A)"
   are the session-2 refinements and are AUTHORITATIVE wherever they touch
   the design doc.** The "Open items" list marks **A and B ✅ resolved;
   C–H open.**
2. **`research/02-design.md`** — the design of record. Heed its top
   banner: §§2/4/6 are **partly superseded** by the session-2 decisions
   and await a re-synthesis pass (after the A–H walk). Read it for the
   still-current parts (the two valves, `rank`, the console constraints,
   the blast radius, the Mermaid diagrams); defer to the decision log for
   the state-machine specifics.
3. **`research/01-prior-art.md`** — external grounding (Open Engine /
   Gas Town / WIP theory / Linear / agentic state models), cited.
4. **`conversation/transcript.md`** — the verbatim session-1 design
   discussion (lossless `.jsonl` companion). Session-2 reasoning lives
   inside the decision-log entries themselves.

## The locked model so far (session 2 — the spine for everything)

- **Seven stored states:** `backlog · pending-approval · ready · active ·
  acceptance · blocked · done`. The single derived overlay: `ready` + any
  open dependency → rendered `blocked:dependency` (auto-clears when the
  blocker closes). The word "receipt" is retired — the model is just
  states + transitions + the backend's native history.
- **Grooming is the `backlog → pending-approval` transition** (a state,
  not a boolean); **approval is the `pending-approval → ready` transition**
  (approval ≡ being in `ready`; the `admission_approved` field is dropped).
  `defer` → `pending-approval`; `bounce`/`reject(re-groom)` → `backlog`.
  "Deferred vs never-approved" is one stored shape, told apart by activity.
- **WIP cap is per-repo** (`.livespec.jsonc`, default 5; fleet total =
  sum of caps, no fleet ceiling). **`rank`** (a fractional key) is the
  sole order; `priority` is dropped. **beads realization = custom statuses
  (1:1)**; git-jsonl = a schema-only update; both get activity natively.
- **`lane_of` is one minimal pure function** (lane == status, plus the one
  `blocked:dependency` overlay), lifted into `livespec_runtime`
  (new `work_items/lifecycle.py`) as the single authority imported by
  `next`/`dispatcher`/`doctor`, and **emitted** to the console via
  `list-work-items --json` (console consumes, never re-derives).
- Full table + field/guard details: decision log, "Locked transition
  table (item A)" + decisions 22–32.

## The next action — resume the A–H walk at item C

The maintainer chose to **resolve the open items A–H first, one at a
time, before slicing the epic.** A and B are locked. **Resume at item C**
(see `research/03-decision-log.md` "Open items"):

- **C.** the `acceptance` "ai" verification mechanism (headless run vs.
  inline) for `ai-only` / `ai-then-human`.
- **D.** migration mechanics + the exact beads custom-status encoding +
  the **`owner`-vs-`assignee`** reconciliation (see the A-note in the
  decision log) + the exact fleet repo set.
- **E.** console redesign + the zero-primary-state conformance test.
- **F.** the `core ↔ driver ↔ orchestrator` dependency-edge check (the
  "Driver → orchestrator = zero deps" invariant with the console added).
- **G.** fractional-index library choice (vendor vs. port) + rebalance
  trigger policy.
- **H.** `rank` rebalance concurrency edge.

Work each with the maintainer **one item / one question per turn**; always
lead with a recommendation; research the live code + beads before gating
(the `livespec_runtime` package, both orchestrators' `commands/`, and
`bd` itself are the ground truth). Record each resolution as a new
decision-log entry. **After A–H:** re-synthesize `02-design.md` §§2/4/6
from the session-2 decisions, then decompose the epic into
dependency-layered slices (foundation first: the shared `livespec_runtime`
schema + the `lifecycle.py` single authority), routing each per the plan
operation (becomes-contract → `/livespec:propose-change`; becomes-work →
`/livespec-orchestrator-beads-fabro:capture-work-item` as a child of
`livespec-35s3zo`).

## Hard exit gate for the epic

`livespec-35s3zo` is NOT done until the local **overseer skill**
(`.claude/skills/overseer/`) is **deleted** — it keeps running until the
new system is dogfooded, then is removed as the final step.

## Resume command

```
/livespec-orchestrator-beads-fabro:plan work-item-state-machine
```
