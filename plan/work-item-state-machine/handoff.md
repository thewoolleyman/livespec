# Handoff — work-item-state-machine planning thread

This is the single resumable entry point for this planning thread. A
fresh session can execute the next action from this file alone by
following the read-first chain below — no chat history required.

## What this thread is

The design of livespec's **deterministic work-item lifecycle state
machine** — the next evolution that turns the implicit, scattered
lifecycle (intake tags + the readiness predicate + Dispatcher markers +
the `mode` lever + the janitor gate + the overseer's bash state table)
into ONE explicit state machine with two human-delegable WIP valves.
The **design is converged and captured**; **no implementation has
started.**

## Status (read from the ledger — never from this file)

- **Epic anchor:** `livespec-35s3zo` (livespec core tenant).
  Check it live:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-35s3zo
  ```
  or, for the impl-side ripe action over its children:
  `/livespec-orchestrator-beads-fabro:next`.
- The epic currently has **no child work-items** — slicing hasn't begun.
  This thread holds no parallel `[ ]` checklist; the ledger is the only
  status source.

## Read-first chain (in order)

1. **`research/02-design.md`** — the design of record: the state machine
   + transitions, the two valves (admission/acceptance), the `rank` order
   primitive, the abstract `WorkItem` schema + both backend mappings, the
   console constraints, the overseer fate, the blast radius, and the
   Mermaid diagram set.
2. **`research/03-decision-log.md`** — the 21 locked decisions and the 8
   open items (A–H) to resolve in-thread while slicing.
3. **`research/01-prior-art.md`** — external grounding (Open Engine /
   Gas Town / WIP theory / Linear / agentic state models), cited.
4. **`conversation/transcript.md`** — the full verbatim design session
   (companion lossless `conversation/transcript.jsonl`); consult for the
   reasoning behind any decision.

## The next action (on the maintainer's go)

Decompose epic `livespec-35s3zo` into the first **dependency-layered
slices**, **foundation first**, per `research/02-design.md §6` and `§10`:

1. **Slice 1 — the shared schema + lane authority** (the spine everything
   else depends on): the `livespec_runtime` `WorkItem` field changes
   (`+rank, +admission_policy, +admission_approved, +acceptance_policy,
   +blocked_reason, +owner`; the `status` enum rename to
   `backlog/ready/active/acceptance/blocked/deferred/done`;
   `-priority`, `-groomed`) and the single pure **`lane_of`** function.
2. Then the two backend realizations (Beads mapping + git-jsonl), the
   readers (`next`/`dispatcher`/`doctor`), the `list-work-items` lane
   emission, the Dispatcher valves + WIP, and the console rewrite.

Routing rule (per the plan operation): a slice that **becomes spec /
contract** (e.g. the state-machine contract, the schema, the
`backlog→done` vocabulary) routes through **`/livespec:propose-change`**
(human-accepts via `revise`); a slice that **becomes implementation work**
is filed via **`/livespec-orchestrator-beads-fabro:capture-work-item`** as
a **child of `livespec-35s3zo`** with `depends_on` edges. Use
**`/livespec-orchestrator-beads-fabro:groom`** to cut oversized slices.

Resolve open items **A–H** (`research/03-decision-log.md`) in-thread as
the relevant slice is cut — none are blocking.

## Hard exit gate for the epic

`livespec-35s3zo` is NOT done until the local **overseer skill**
(`.claude/skills/overseer/`) is **deleted** — the overseer keeps running
until the new system is dogfooded, then is removed as the final step.

## Resume command

```
/livespec-orchestrator-beads-fabro:plan work-item-state-machine
```
