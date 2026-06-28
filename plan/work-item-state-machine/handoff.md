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
open items **A–H one at a time**. **Locked: A, C, and D (except D-3).
Partly locked: B** (its lane-taxonomy is resolved by decision 32, but its
`lane_of` signature/home + the `list-work-items --json` lane shape are
still open). **Remaining walk order: G → D-3 → B → E → F → H.** (D-3 is
sequenced right after G because it depends on G's output; B is sequenced
just before E because E — the console — consumes B's emitted-lane shape.)

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
   session-1; **22–32 + the "Locked transition table (item A)" are
   session-2; 33–37 are session-3.** All are AUTHORITATIVE wherever they
   touch the design doc. The "Open items" list marks **A, C ✅; B partly
   (taxonomy ✅ via decision 32; signature/home/shape ⬜ open); D 🟡
   (D-1/D-2/D-4 ✅, D-3 ⬜); E/F/G/H open.** Session-3 added: **C** =
   post-merge acceptance (33–34, which AMEND item A's `complete`/`accept`/
   `reject` rows); **D-1** owner≡`assignee` (35); **D-2** beads encoding
   verified vs v1.0.5 (36); **D-4** fleet set (37).
2. **`research/02-design.md`** — the design of record. Heed its top
   banner: **§§2, 4, 6 are partly superseded** by the session-2/3 decisions
   and await a re-synthesis pass (after the A–H walk). In particular §4's
   "Acceptance valve" (which implied a PRE-merge release gate) is
   superseded by decision 33 (acceptance is POST-merge); §6's beads mapping
   table is superseded by decision 36. Read it for the still-current parts
   (the admission valve, `rank`, the console constraints, the blast radius,
   the Mermaid diagrams); defer to the decision log everywhere they differ.
3. **`research/01-prior-art.md`** — external grounding (Open Engine /
   Gas Town / WIP theory / Linear / agentic state models), cited.
4. **`conversation/transcript.md`** — the verbatim session-1 design
   discussion (lossless `.jsonl` companion). Session-2/3 reasoning lives
   inside the decision-log entries themselves.

## The locked model so far (the spine for everything)

- **Seven stored states:** `backlog · pending-approval · ready · active ·
  acceptance · blocked · done`. The single derived overlay: `ready` + any
  open dependency → rendered `blocked:dependency` (auto-clears). "Receipt"
  is retired — just states + transitions + the backend's native history.
- **Grooming = `backlog → pending-approval`**; **approval = `pending-approval
  → ready`** (approval ≡ being in `ready`; `admission_approved` dropped).
  `defer` → `pending-approval`; `bounce`/`reject(re-groom)` → `backlog`.
- **Acceptance is POST-MERGE / in-production (session 3, decision 33).**
  `just check` stays the HARD pre-merge floor; the AI/human fit-and-behavior
  acceptance happens AFTER ship-on-green, against the shipped artifact +
  telemetry. `complete` merges-on-green into the observable `acceptance`
  state; `accept` is a post-ship confirmation (AI for `ai-only`; human from
  the console for `ai-then-human`, item parked on the ledger); `reject` =
  revert/fix-forward. Risk dial is at ADMISSION + reversibility, never a
  pre-merge hold. (Majors/Fong-Jones "verify in production".)
- **Ownership = the existing `assignee` field (decision 35)** — kept in
  place, zero migration, set by the Dispatcher on `admit`, invariant
  `active ⟹ assignee set`. ("owner ≡ assignee"; beads has no native `owner`,
  its native field IS `assignee`.)
- **WIP cap is per-repo** (`.livespec.jsonc`, default 5; fleet total = sum
  of caps). **`rank`** (a fractional key) is the sole order; `priority`
  dropped.
- **Beads encoding (decision 36, verified vs gastownhall/beads v1.0.5):**
  5 custom statuses (`backlog`, `pending-approval`, `ready:active`,
  `active:wip`, `acceptance:wip`) + 2 built-in reuses (`blocked`;
  `done`→`closed` for native closure). Categories: only `ready` = `active`.
  `bd create` forces `open`, so the store's `append_work_item` needs a
  2-step `create`+`update --status`. No transition enforcement in beads
  (livespec's machine enforces in Python). git-jsonl = status-enum update.
- **`lane_of` is one minimal pure function** (lane == status + the one
  `blocked:dependency` overlay), living in the `livespec_runtime.work_items`
  package, imported by `next`/`dispatcher`/`doctor` and **emitted** to the
  console via `list-work-items --json`. NOTE: the exact module, the function
  signature, and the emitted-lane JSON shape are **open item B** — not yet
  locked by any decision (design §3 only says "the `livespec_runtime.work_items`
  package"; no decision has fixed a module name like `lifecycle.py`).
- **Fleet/blast radius (decision 37):** all 8 beads tenants under
  `/data/projects/livespec*` migrate in lockstep; code touches
  `livespec_runtime`, both orchestrators, the console.
- Full detail + guards: the decision log (decisions 22–37 + the item-A
  table, as amended by 34/35).

## Beads ground-truth (for any further beads research)

- Canonical beads origin is **`github.com/gastownhall/beads`**
  (`steveyegge/beads` redirects to it). A local clone at
  `/data/projects/beads` has `upstream` already repointed to canonical and
  is parked at tag **v1.0.5** (the livespec-pinned version) for inspection;
  `origin` is the maintainer's fork. Verified there: custom statuses +
  categories are real (`bd config set status.custom "name:category,…"`),
  7 built-ins (`open,in_progress,blocked,deferred,closed,pinned,hooked`),
  no status-transition enforcement, `bd create` forces `open`/`deferred`.

## The next action — resume the walk at item G, then D-3, then B

The maintainer is resolving open items **one at a time, before slicing the
epic**; A, C, D (except D-3) are locked and B is partly locked. **Resume at
item G** (D-3 depends on it; B follows before E):

- **G.** Fractional-index library choice — **vendor** a small pure-Python
  LexoRank/fractional-indexing impl vs. **port** one (per the project's
  "prefer well-maintained libraries; vendoring small permissive pure-Python
  libs under `scripts/_vendor/` is authorized" rule) — plus the **rebalance
  trigger policy** (on-demand vs. key-length threshold).
- **D-3** (unblocked by G). `rank` backfill for existing items +
  `priority` drop. ORDER strategy is pre-agreed: rank existing items by
  current `priority` → `captured_at` (preserves effective order), then drop
  `priority`; G supplies the key generator for the actual values.
- **B** (the still-open part). Lock the precise `lane_of` signature, its
  exact module home in `livespec_runtime.work_items`, and the
  `list-work-items --json` lane-emitting shape (the Python ↔ console seam
  that E consumes). Decision 32 already fixed the taxonomy (lane == state +
  the one `blocked:dependency` overlay); this is the engineering-signature
  remainder.
- **E.** Console full lane/view redesign + the "zero-primary-state /
  rebuild-from-ledger" conformance test. (Consumes B's emitted-lane shape.)
- **F.** Verify the `core ↔ driver ↔ orchestrator` dependency edges hold
  the "Driver → orchestrator = zero deps" invariant with the console added.
- **H.** `rank` rebalance concurrency edge (rebalance racing a concurrent
  insert) — confirm "off-by-one-position, never corrupt" under the real
  merge model.

Work each with the maintainer **one item / one question per turn**; always
lead with a recommendation; research the live code + beads before gating
(`livespec_runtime`, both orchestrators' `commands/`, and the
`/data/projects/beads` v1.0.5 checkout are the ground truth). Record each
resolution as a new decision-log entry. **After the walk:** re-synthesize
`02-design.md` §§2/4/6 from the decisions, then decompose the epic into
dependency-layered slices (foundation first: the shared `livespec_runtime`
schema + `lane_of`), routing each per the plan operation
(becomes-contract → `/livespec:propose-change`; becomes-work →
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
