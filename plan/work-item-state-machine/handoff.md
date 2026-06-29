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
open items **A–H one at a time**. **Locked: A, B, C, D (all sub-items),
and G** (decisions 1–40). **Remaining walk order: E → F → H.** (Session 4
resolved G, D-3, and B — decisions 38–40.) After the walk: re-synthesize
`02-design.md` §§2/4/6 from the decisions, then slice the epic.

## Status (read from the ledger — never from this file)

- **Epic anchor:** `livespec-35s3zo` (livespec core tenant). Check live:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-35s3zo
  ```
- The epic has **no child work-items** — slicing hasn't begun (it begins
  after the A–H walk completes). The ledger is the only status source;
  this file holds no parallel checklist.

## Read-first chain (in order)

1. **`research/03-decision-log.md`** — START HERE. Decisions 1–21 =
   session-1; **22–32 + the "Locked transition table (item A)" = session-2;
   33–37 = session-3; 38–40 = session-4** (G = decision 38; D-3 = decision
   39; B = decision 40). All are AUTHORITATIVE wherever they touch the design
   doc. The "Open items" list now marks **A, B, C, D, G ✅; only E, F, H
   open.** Session-4 added: **G** = PORT the CC0 fractional-index lib +
   on-demand rebalance (38); **D-3** = `rank` non-null + cross-tenant backfill
   + `priority` drop (39); **B** = `lane_of` signature/home/shape + full
   single-authority consolidation (40).
2. **`research/02-design.md`** — the design of record, but now **largely
   superseded by the decision log** and awaiting a re-synthesis pass (after the
   walk; its own top banner only mentions the session-2 revisions). Treat
   **§§2, 3, 4, 5, 6 as partly superseded**: §2/§3 (state set + the `lane_of`
   pseudocode) by decisions 24/32/40 — 7 states (no `deferred`), and the
   signature is `lane_of(*, item, index, manifest) -> Lane`; §4's "Acceptance
   valve" by decision 33 (acceptance is POST-merge) and its `admission_approved`
   by decision 26 (dropped); §5's "vendor … implementation" by decision 38
   (PORT) and rank-nullability by decision 39 (strictly non-null); §6's beads
   mapping + the `owner`/`rank` rows by decisions 36/35/39. Read it for the
   still-current parts (the two-valve framing, the console constraints, the
   blast radius, the Mermaid diagrams) but **defer to the decision log
   everywhere they differ** (the log is START-HERE authoritative).
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
  of caps).
- **`rank` (decisions 38–39)** is the sole order — a strictly-required
  **NON-NULL** `str` fractional key. The algorithm is a **PORT** (a verbatim
  CC0-1.0 copy of the rocicorp/httpie fractional-indexing module →
  `livespec_runtime/work_items/_fractional_indexing.py`, behind a thin
  `rank.py` wrapper), NOT a vendored lib (livespec_runtime has no vendoring
  machinery and is itself vendored source-only into consumers). Existing items
  are backfilled across all 8 tenants from `priority → captured_at → id` via
  `n_keys_between`; **`priority` is dropped** (no scrub; legacy lines keep it
  in append-only history). The **store adapter** substitutes a bottom-sentinel
  (a char outside base-62, e.g. `"~"`) for pre-`rank` legacy lines, so the
  type stays non-null; a doctor invariant asserts every live item has a real
  rank. Rebalance is **on-demand** (`rebalance-ranks`, reused for the one-time
  backfill via a legacy-seed) with a doctor key-length warning — never
  auto-fires.
- **Beads encoding (decision 36, verified vs gastownhall/beads v1.0.5):**
  5 custom statuses (`backlog`, `pending-approval`, `ready:active`,
  `active:wip`, `acceptance:wip`) + 2 built-in reuses (`blocked`;
  `done`→`closed` for native closure). Categories: only `ready` = `active`.
  `bd create` forces `open`, so the store's `append_work_item` needs a
  2-step `create`+`update --status`. No transition enforcement in beads
  (livespec's machine enforces in Python). git-jsonl = status-enum update.
- **`lane_of` (decision 40, item B resolved)** = `lane_of(*, item, index,
  manifest) -> Lane`, where `Lane` is a `{name: LaneName, reason:
  BlockedReason | None}` frozen dataclass (7 rendered lanes; `reason` non-null
  iff `name == "blocked"`). It lives in a new
  **`livespec_runtime/work_items/lifecycle.py`** with FULL single-authority
  consolidation: `is_item_ready` (= `lane_of(...).name == "ready"`),
  `ready_sort_key` (now keyed on `rank`), and the open/closed dep-resolution
  all relocate there (out of the orchestrator's `_cross_repo.py`), reusing
  `resolve_ref`/`RefStatus` from `livespec_runtime.cross_repo`;
  `next`/`dispatcher`/`list-work-items` import them. `list-work-items --json`
  emits flat **`lane` + `lane_reason`** per item (all other new fields
  auto-emit via `asdict`); the console CONSUMES them directly (retiring its
  `bd ready --json` re-derivation).
- **Fleet/blast radius (decision 37):** all 8 beads tenants under
  `/data/projects/livespec*` migrate in lockstep; code touches
  `livespec_runtime`, both orchestrators, the console.
- Full detail + guards: the decision log (decisions 22–40 + the item-A
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

## The next action — resume the walk at item E, then F, then H

The maintainer is resolving open items **one at a time, before slicing the
epic**; A, B, C, D, and G are locked (decisions 1–40). **Resume at item E:**

- **E.** Console full lane/view redesign + the "zero-primary-state /
  rebuild-from-ledger" conformance test. Consumes B's emitted `lane` /
  `lane_reason` shape (decision 40): the console switches its source from
  `bd ready --json` to `list-work-items --json` and retires the Rust
  `BeadsWorkItemStatus` 3-way re-derivation. Ground truth:
  `/data/projects/livespec-console-beads-fabro`
  (`crates/console-application/src/source_adapters.rs` —
  `parse_beads_observation`, `BeadsWorkItemStatus`, `BeadsWorkItemSnapshot`;
  `crates/console-cli/src/lib.rs` — the `bd ready --json` source-observation
  wiring).
- **F.** Verify the `core ↔ driver ↔ orchestrator` dependency edges hold the
  "Driver → orchestrator = zero deps" invariant with the console added — and
  the NEW edge decision 40 introduces (orchestrator →
  `livespec_runtime.work_items.lifecycle`).
- **H.** `rank` rebalance concurrency edge (a rebalance racing a concurrent
  insert) — confirm "off-by-one-position, never corrupt" under the real
  append-only / git-merge model (decisions 38–39's `rebalance-ranks`).

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
