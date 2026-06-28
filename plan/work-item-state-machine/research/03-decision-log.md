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

## Locked decisions — session 2 (item A: the state machine, resolved)

These refine/supersede earlier decisions where noted. `02-design.md`
(§2/§4/§6) is re-synthesized from these at the end of the A–H walk; until
then this section is authoritative for the deltas.

22. **WIP cap is PER-REPO**, sourced from each repo's `.livespec.jsonc`,
    default **5** — NOT a single fleet-wide number. Total fleet concurrency
    = the sum of per-repo caps; no separate fleet ceiling (a later knob if
    ever wanted). *Sharpens decision 10's ambiguous "global".*
23. **Retire the word "receipt."** The model has only: **state**,
    **transition** (`from --trigger [guard] / side-effect--> to`), and the
    backend's native history as the audit trail. "Receipt" was a synonym
    for "named transition" (Open-Engine import) and added nothing. All
    transition names are lowercase verbs (the earlier UPPER/lower split was
    sloppiness, no semantics).
24. **Six STORED states:** `backlog · ready · active · acceptance ·
    blocked · done`. **`deferred` is removed as a state.** *Supersedes the
    7-state set in decisions 2 & 6.*
25. **`groomed` is a first-class stored PROPERTY** (a boolean), not a
    state-implied flag — because it must **survive a defer** (a parked item
    is still groomed; resuming must not force a re-groom). *Supersedes
    decision 4 ("grooming is the transition, no boolean").* Consistent with
    how decision 8 already treated approval as legitimate primary info.
26. **`admission_approved` (the field) is DROPPED; approval ≡ `ready`
    membership.** Entering `ready` *is* approving; leaving `ready` →
    `backlog` *is* un-approving (deferring). A separate boolean would be
    redundant with the state. *Supersedes decision 8's stored
    `admission_approved`.* `admission_policy` (`auto`/`manual`/inherit)
    stays: `manual` → `groom` lands in `backlog` (groomed=true) awaiting a
    human's approve; `auto` → `groom` auto-advances to `ready` (the opt-in
    *is* the auto policy; default `manual` preserves safe-by-default). The
    auto-defer hole is closed: `auto` = auto-approve **at groom**
    (one-time), so a deferred auto item stays parked until resumed.
27. **No `deferred` state, no park/resume vocabulary.** "Defer" = leave
    `ready` → `backlog`; "resume/approve" = re-enter `ready`. A
    **never-approved** item and a **deferred-after-work** item are the SAME
    stored shape (`backlog` + `groomed`); they are told apart by
    **activity**, never a stored flag (see #30).
28. **Two kinds of blocked, split by auto-detectability.** Stored
    `blocked_reason ∈ {needs-human, infra-external}` — the system cannot
    detect resolution, so it needs an explicit `unblock`. **`dependency` is
    the ONLY derived overlay** (`ready` + any open dep → rendered
    `blocked:dependency`; auto-clears when the blocker closes). *Supersedes
    decision 6's listing `dependency` as a stored `blocked_reason`.* Adds an
    **`active → ready` (`add-dependency`)** transition for a dependency
    discovered mid-work (records the edge, preserves `groomed`, then derives
    to `blocked:dependency`).
29. **`ready` stays a STORED state** (resolves open item **A**'s
    stored-vs-derived question; rejects the "derive everything" path).
    Criterion: *a state is stored when it is a meaningful node the workflow
    branches on; a thing is derived only when it depends on OTHER items'
    asynchronous changes (where a stored copy would silently go stale).*
    Only the dependency overlay meets the derived bar. *Reaffirms decision
    3.*
30. **Activity is first-class in BOTH backends**, so "was this previously
    worked on / approved" is derived, never stored. Beads: `bd history`
    (native status timeline; `status` is in every history snapshot) plus the
    optional `set-state` event-bead mechanism. git-jsonl: the append-only
    supersession chain *is* the event log. The distinguishing signal is
    "was the item ever `active`."
31. **Beads realization = CUSTOM STATUSES (1:1).** Beads supports custom
    statuses (`bd config set status.custom`), so each livespec state maps to
    its own native beads status — native `--status <name>` queries and
    native `bd history`. The four beads **categories** (`active/wip/done/
    frozen`) are an orthogonal coarse display tag, **not** a status-collapsing
    mechanism: you query by status *name*, and livespec filters on the
    *abstract* status in Python regardless. git-jsonl needs only a **schema
    update** (new `status` enum values + the `groomed` field); its chain
    gives activity natively. The exact beads encoding (which states reuse a
    built-in vs. a custom status) finalizes in item **D**.
32. **`groomed` is promoted from a property to a STATE: `pending-approval`**
    (*supersedes #25; amends #24 to SEVEN states*). The grooming gate becomes
    **structural** — you cannot reach `ready` without transiting
    `pending-approval` — rather than a guard on a boolean. This deletes the
    `groomed` property, the `ready ⟹ groomed` invariant, AND the derived
    backlog-split. The state holds BOTH never-approved and deferred/parked
    items (still told apart by activity, #30). A **pre-groomed** item files
    straight INTO `pending-approval` (never skips to `ready`), so the approval
    gate is universal. The seven stored states are now:
    `backlog · pending-approval · ready · active · acceptance · blocked ·
    done`. Key transition deltas: `groom`: backlog → pending-approval;
    `approve`: pending-approval → ready (manual: a human; auto: automatic);
    `defer`: {ready, active, blocked} → **pending-approval** (still
    decomposed, just un-approved — distinct from `bounce` / `reject(re-groom)`
    → **backlog**, which need re-decomposition); "resume" is just `approve`
    again. *Also resolves item B's lane-taxonomy question: lane == state, so
    `lane_of` stays minimal — the only overlay is `ready` + open deps →
    `blocked:dependency`.*

### Locked transition table (item A)

Derived overlay (not a stored transition): `ready` + any open dep →
rendered `blocked:dependency`.

| Trigger | From → To | Guard | Side-effects |
|---|---|---|---|
| `file` | ∅ → backlog | `position` supplied; not pre-groomed | `rank`←position |
| `file` (pre-groomed) | ∅ → pending-approval | `position` supplied; pre-groomed | `rank`←position |
| `groom` | backlog → pending-approval | human judges decomposed | — |
| `approve` | pending-approval → ready | manual: a human; auto: automatic | (in `ready` = approved) |
| `defer` | {ready, active, blocked} → pending-approval | human parks / un-approves | — |
| `admit` | ready → active | deps-clear ∧ free WIP slot (per-repo cap) ∧ owner resolvable | `owner`←doer |
| `complete` | active → acceptance | the doer (human/LLM/factory) declares the impl done | — |
| `accept` | acceptance → done | `acceptance_policy` satisfied (≥ one AI pass) | `resolution=completed`; `audit` |
| `block` | active → blocked | external wait not auto-detectable | `blocked_reason ∈ {needs-human, infra-external}` |
| `unblock` | blocked → active | stored block explicitly cleared | `blocked_reason=null` |
| `add-dependency` | active → ready | new work-item dep discovered mid-work | `depends_on +=` |
| `reject` (rework) | acceptance → active | reviewer rejects; rework in place | — |
| `reject` (re-groom) | acceptance → backlog | reviewer rejects; re-decompose | — |
| `bounce` | active → backlog | non-convergence needs re-groom | — |

Invariants (doctor-checkable): `active ⟹ owner` set; stored `blocked ⟹
blocked_reason ∈ {needs-human, infra-external}`; reaching `ready` requires
transiting `pending-approval` (the structural grooming gate); `admission_policy`
governs only the `approve` routing (auto vs. human).

## Open items (resolve-in-thread / author-in-doc — non-blocking)

- **A.** ✅ **RESOLVED (session 2)** — the full transition table + guards
  are locked above ("Locked transition table (item A)"; decisions 22–32).
  Net: **7 stored states**, `deferred` removed, **`groomed` promoted to the
  `pending-approval` state** (structural grooming gate), `admission_approved`
  dropped (approval ≡ `ready`), one derived overlay (`blocked:dependency`),
  beads custom statuses.
- **A-note (surfaced, → item B/D):** the abstract `WorkItem` already has a
  dormant `assignee: str | None` (every filing site hardcodes `None`, no
  reader consults it); beads has a native `owner` field too. Decide whether
  the new "claimed-by" `owner` **reuses `assignee`** (rename) or is additive
  — resolve when settling the schema (B) and the beads mapping (D).
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
