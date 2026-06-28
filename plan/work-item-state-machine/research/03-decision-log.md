# Decision log — locked decisions and open items

Captured from the design session (verbatim in `../conversation/transcript.md`).
"Locked" = decided by the maintainer in-session. "Open" = deferred to
author-in-doc or resolve-in-thread while slicing; none are blocking.

## Locked decisions

1. **Extract the implicit lifecycle into one explicit deterministic
   state machine** (livespec's Gas-Town / Open-Engine analog); invert
   operation-centric → state-centric. Skills become transitions/readers.
2. **Ubiquitous vocabulary is livespec's own**, never a backend's:
   `backlog · ready · active · acceptance · blocked · deferred · done`.
   A storage backend (Beads) is one pluggable realization; its terms
   (`open`/`in_progress`/`closed`, `hooked`, etc.) live only inside the
   one adapter, never in the domain language.
3. **Lane ≡ state**, with a single derived overlay (`ready` + open deps
   → `blocked:dependency`, which auto-resolves).
4. **Grooming is the `backlog → ready` transition** (no `groomed`
   boolean); it structurally gates admission. `needs-regroom` = a bounce
   to `backlog`.
5. **`acceptance` (renamed from "review")** is the release/accept gate,
   distinct from Fabro's internal LLM review.
6. **`blocked` (involuntary) vs `deferred` (voluntary)** are distinct
   first-class states. `blocked_reason ∈ {needs-human, infra-external,
   dependency}`; `dependency` is derived, the others stored.
7. **Two human-delegable valves:** admission (`ready → active`) and
   acceptance (`active → acceptance → done`). Per-item, inheritable from
   the epic, blanket-able for low-risk, **safe-by-default**.
8. **`admission_policy ∈ {auto, manual}`** (default `manual`) + a stored
   **`admission_approved`** for manual items (a legitimate primary
   decision, not a shadow), **reset on bounce**. A human can pre-approve
   and walk away.
9. **`acceptance_policy ∈ {ai-only, human-only, ai-then-human}`**
   (default `ai-then-human`). No "release with zero verification."
10. **WIP cap: global, default 5**, in orchestrator config — enforced
    solely by the **Dispatcher**, which pulls the highest-`rank`
    admission-eligible `ready` item when a slot frees. The console only
    commands + observes; it never enforces.
11. **Order is a first-class persisted `rank`** — a fractional/lexicographic
    key (accepted over a linked list for sorted-read + merge-robustness +
    fits-the-supersession-reducer reasons), unified across all states,
    rebalanced by a deterministic order-preserving command.
12. **`priority` (int) is killed** — `rank` is the sole ordering
    authority; `next` ranks by `rank`. (A non-ordering severity *label*
    could be added later if ever wanted, but never a second order.)
13. **Create position is a required parameter** — `{top | bottom |
    before:<id> | after:<id>}`, no default; `capture-work-item` enforces
    it. Console policy: `before:<top-backlog-item>` (else `top`).
14. **`owner`** may be an agent; **required once an item is `active`**
    (another structurally-enforced admission gate).
15. **Schema source of truth = `livespec_runtime`**; Beads + git-jsonl
    are realizations. **`lane_of` is one pure function**, imported by
    Python consumers and **emitted** to the console (consume-don't-recompute).
16. **Console:** zero Beads knowledge (hard negative constraint); only
    interface is the orchestrator CLI (Rust wraps the deterministic
    CLIs); **zero primary lifecycle state** — everything rebuildable
    from the ledger; **snooze/ack killed**; harness abstraction lives in
    the **driver layer**, reached transitively through the orchestrator
    (no direct console→driver dependency). Significant rewrite is fine.
17. **`orchestrate` folds into the console.**
18. **Overseer keeps running** to finish current work; **the epic's exit
    gate deletes the overseer skill once the new system is dogfooded.**
19. **The research doc carries multiple Mermaid diagrams** (state machine
    + valves; lane-derivation seam; plane/API-surface relationship;
    event-sourcing/rebuild dataflow) — drafted in `02-design.md`.
20. **One fleet-wide epic**, anchored in **livespec core**; assume it
    touches core + both orchestrators + readers + console + drivers +
    tooling.
21. **Verbatim capture requirement:** the whole design conversation is
    preserved verbatim as `../conversation/transcript.md` (formatted)
    and `../conversation/transcript.jsonl` (raw), per maintainer request.

## Open items (resolve-in-thread / author-in-doc — non-blocking)

- **A.** The full state-machine **transition table** + exact guard
  conditions (the `02-design.md` diagram is the first cut; formalize for
  the spec).
- **B.** Precise `lane_of` signature + its exact home in
  `livespec_runtime`, and the `list-work-items --json` lane-emitting
  shape (the Python ↔ console seam).
- **C.** The `acceptance` "ai" verification mechanism (headless Fabro run
  vs inline) for `ai-only` / `ai-then-human`.
- **D.** Migration mechanics: `rank` backfill for existing items;
  `priority` drop; `acceptance` label on Beads; the exact fleet repo set.
- **E.** Console full lane/view redesign + the "zero-primary-state /
  rebuild-from-ledger" conformance test.
- **F.** Verify the exact `core ↔ driver ↔ orchestrator` dependency edges
  hold the "Driver → orchestrator = zero" invariant with the console added.
- **G.** Fractional-index library choice (vendor vs port) + rebalance
  trigger policy (on-demand vs length threshold).
- **H.** `rank` rebalancing concurrency edge (a rebalance racing a
  concurrent insert) — confirm the "off-by-one-position, never corrupt"
  reasoning under the real merge model.

## Sources

- External grounding + citations: `01-prior-art.md`.
- Current-state ground truth (the five-concept map, the Beads field
  model, the console blast radius) and the full reasoning trail:
  `../conversation/transcript.md`.
