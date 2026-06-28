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
| `admit` | ready → active | deps-clear ∧ free WIP slot (per-repo cap) ∧ assignee resolvable | `assignee`←doer |
| `complete` | active → acceptance | the doer (human/LLM/factory) declares the impl done | — |
| `accept` | acceptance → done | `acceptance_policy` satisfied (≥ one AI pass) | `resolution=completed`; `audit` |
| `block` | active → blocked | external wait not auto-detectable | `blocked_reason ∈ {needs-human, infra-external}` |
| `unblock` | blocked → active | stored block explicitly cleared | `blocked_reason=null` |
| `add-dependency` | active → ready | new work-item dep discovered mid-work | `depends_on +=` |
| `reject` (rework) | acceptance → active | reviewer rejects; rework in place | — |
| `reject` (re-groom) | acceptance → backlog | reviewer rejects; re-decompose | — |
| `bounce` | active → backlog | non-convergence needs re-groom | — |

Invariants (doctor-checkable): `active ⟹ assignee` set; stored `blocked ⟹
blocked_reason ∈ {needs-human, infra-external}`; reaching `ready` requires
transiting `pending-approval` (the structural grooming gate); `admission_policy`
governs only the `approve` routing (auto vs. human).

> ⚠️ **Session-3 amendment (item C, decision 34):** the `complete`, `accept`,
> and `reject` rows above are amended for **post-merge acceptance** —
> `complete` merges-on-green into a now-observable `acceptance` state; `accept`
> is a post-ship confirmation; `reject` adds revert/fix-forward since the change
> is already live. Topology unchanged. See decisions 33–34.

## Locked decisions — session 3 (item C: acceptance verification, resolved)

33. **Acceptance verification is POST-MERGE / in-production
    (observability-driven).** *Resolves item C.* The deterministic `just check`
    stays the HARD **pre-merge** floor (the in-sandbox janitor gate); the
    AI/human **acceptance** (fit + real behavior) happens **after** the change
    merges and ships. Rationale: `just check` already gates *correctness*
    pre-merge, so acceptance verifies *fit/behavior*, which is judged better
    against the **shipped** artifact + telemetry (OTel → Honeycomb is already
    plumbed; the OOB reflector already reads `GROUP BY work.item.id`) than
    against a static held diff; it preserves the fleet's existing
    **ship-on-green** fast flow (the Little's-Law value the design rests on);
    and it needs **no held-open ephemeral Fabro sandbox**. This is the Majors /
    Fong-Jones *"verify in production"* model (*Observability Engineering*) and
    the correct reading of the Gas Town cautionary tale: its failure mode was
    **un-observed + un-reversible** autonomous merge, so the remedy is
    **observability + reversibility**, NOT a pre-merge human gate.
    Safe-by-default is preserved at the OTHER valve — risky/irreversible work is
    gated at **admission** (`admission_policy=manual` / `human-gated`), never by
    a pre-merge acceptance hold. There is exactly **one merge model
    (ship-on-green)**; the risk dial is admission + reversibility. *(Chosen by
    the maintainer over a pre-merge gating hold and an inline-in-impl-run gate;
    `02-design.md` §4's "Acceptance valve", which implied a pre-merge release
    gate, is superseded here and re-synthesized at the end of the A–H walk.)*

34. **Item-C amendments to the item-A transition table (compose, don't reopen;
    topology unchanged).** Because acceptance is post-merge, three side-effects
    are amended:
    - **`complete` (active → acceptance):** side-effect now includes
      **merge-on-green**. Entering `acceptance` means the change is **merged +
      live** (the in-sandbox `just check` floor having passed). The Fabro impl
      run keeps today's `gh pr merge --rebase --auto`; what changes is the item
      transitions to the observable `acceptance` **state** instead of straight
      to `done`.
    - **`accept` (acceptance → done):** now a **post-ship confirmation** — the
      AI (`ai-only`) or the human (`ai-then-human`) confirms the *shipped*
      behavior is good (against tests + telemetry). For `ai-then-human` the item
      **parks in `acceptance` on the ledger** (cheap, durable) until the human
      confirms from the console. Other side-effects unchanged
      (`resolution=completed`; `audit`).
    - **`reject` from `acceptance`:** since the change is already live, reject
      carries a **revert-or-fix-forward** corrective side-effect.
      `reject (rework)` → `active` = **fix-forward** (patch on top of the live
      change); `reject (re-groom)` → `backlog` = **revert the merged change +
      re-decompose**. Routing is unchanged from A.
    - **Mechanism (orchestrator-internal beads-fabro realization — NOT core
      contract):** the AI acceptance pass reuses the telemetry-reading reflector
      pattern + a diff/criteria judge against the merged ref; the human leg is a
      console action. Today's in-graph advisory `review` node may stay as a
      pre-merge aid or be retired into the post-merge pass (a slicing detail).
      Default the AI pass to **read-and-judge + watch telemetry** (since
      `just check` already executes the suite); upgrade to a **sandboxed
      exploratory-execution** pass only if a bug class is shown to slip through.

## Locked decisions — session 3 (item D: migration & schema — in progress)

35. **The lifecycle "owner" field IS the existing `assignee` field — kept in
    place, zero migration.** *Resolves the item-A `owner`/`assignee` A-note;
    first of item D's sub-questions.* The abstract `WorkItem` already carries an
    `assignee: str | None` that maps **1:1 to beads' native `assignee` field**
    (and a git-jsonl `assignee` key), is fully plumbed, and is **read by no
    consumer** (`next`, dispatcher, `doctor`, `list-work-items`, console all
    ignore it). beads has **no native `owner` field** — so `02-design.md` §6's
    claim that `owner` maps to a "beads native `owner` field" is **factually
    wrong** and is corrected here. Resolution: **reuse `assignee` in place** as
    the claimed-by/owner field; **adopt `assignee` as the ubiquitous term**
    (retire "owner" as a label — `owner ≡ assignee`). **One field only**
    (decision 14's "owner may be an agent" = the doer, so no separate
    owner + assignee). Rationale: the backend stores it natively as `assignee`
    regardless, so naming the abstract field `assignee` too is perfectly
    cohesive (abstract name = native name = git-jsonl key — **zero adapter
    impedance, zero schema migration**); renaming to `owner` would have been a
    mechanical rename across ~8 repos buying only a doc-term match.
    **Consequences:** (a) every `owner` reference in earlier decisions and the
    item-A transition table now reads `assignee` — the `admit` side-effect is
    `assignee←doer`; the invariant is `active ⟹ assignee set`; (b) the
    Dispatcher sets `assignee` on `admit` (not a file-time human input);
    (c) `capture-work-item`'s obsolete human-typed-at-file-time `assignee` input
    is dropped (the field is set when work starts, not when filed). The blessed
    new-optional-field evolution pattern does **not** apply here — no new field
    is added; an existing one is repurposed and given an invariant.

36. **Beads status encoding (item D, sub-2) — verified against v1.0.5 source +
    finalized.** *Refines decision 31.* Inspecting the canonical
    **gastownhall/beads** (steveyegge/beads redirects to it) at the
    livespec-pinned **v1.0.5** confirmed beads ships real **custom statuses**
    (`bd config set status.custom "name:category,…"`; dedicated `custom_statuses`
    table; max 50; names `^[a-z][a-z0-9_-]*$`, so hyphenated livespec names are
    valid verbatim) and real **status categories**
    (`active/wip/done/frozen/unspecified`; `active` ⇒ surfaces in native
    `bd ready`, `done`/`frozen` ⇒ hidden from default `bd list`). Beads has
    **7 built-ins** (`open, in_progress, blocked, deferred, closed, pinned,
    hooked`), **no transition enforcement** (status is a free assignment —
    livespec's machine enforces transitions in Python), and **`bd create` forces
    `open`/`deferred`** (cannot create directly into a custom status).

    **Encoding principle (maintainer-chosen):** reuse a built-in ONLY where it
    carries native semantics worth keeping, or where collision forces it;
    otherwise a custom status **named verbatim** as livespec names the state.

    | livespec state | beads v1.0.5 | kind | category |
    |---|---|---|---|
    | `backlog` | `backlog` | custom | unspecified |
    | `pending-approval` | `pending-approval` | custom | unspecified |
    | `ready` | `ready` | custom | **active** |
    | `active` | `active` | custom | wip |
    | `acceptance` | `acceptance` | custom | wip |
    | `blocked` | `blocked` | built-in reuse (forced; name already matches) | wip |
    | `done` | `closed` | built-in reuse (native closure: `closed_at`, `bd close`, done-hiding) | done |

    Net: **5 custom statuses** (`backlog`, `pending-approval`, `ready`, `active`,
    `acceptance`) + **2 built-in reuses** (`blocked` name-matched; `done`→`closed`
    for closure). Only `done`↔`closed` needs an adapter name-mapping (the one
    place a livespec term ≠ its beads term — exactly where decision 2 says
    backend terms live); `active` stays **custom** (queryable by its own name
    natively, no `in_progress` mapping, and `in_progress` carries no native
    semantics worth reusing). Only `ready` is category `active`, so native
    `bd ready` shows exactly the admission-eligible set (defense-in-depth —
    livespec computes real readiness in Python regardless).

    **Consequences:** (a) each repo's bootstrap must register the 5 custom
    statuses (`bd config set status.custom "backlog,pending-approval,ready:active,active:wip,acceptance:wip"`)
    — a per-tenant provisioning step; (b) the beads store wrapper's
    `append_work_item` grows a 2-step path (`bd create` lands `open`, then
    `bd update --status <state>`) for every initial state — note `backlog` is
    custom (not `open`), so even a plain `file` is now create+update (a one-time
    wrapper change, flagged for objection if the per-file double-call concerns
    you); (c) `02-design.md` §6's older mapping table (which used
    `status=open`+labels for `ready`/`acceptance`) is **superseded** by this
    custom-status encoding and re-synthesized at the end of the walk; (d)
    git-jsonl needs only its status enum updated to the 7 livespec names (it
    stores status as a free string; the dropped `groomed` field never lands
    there since decision 32 made grooming the `pending-approval` state).

37. **Fleet repo set for the migration (item D, sub-4).** The migration epic spans
    **all 8 live beads tenants** under `/data/projects/livespec*` — `livespec`,
    `livespec-runtime`, `livespec-dev-tooling`, `livespec-console-beads-fabro`,
    `livespec-driver-claude`, `livespec-driver-codex`,
    `livespec-orchestrator-beads-fabro`, and `livespec-orchestrator-git-jsonl`
    (the git-jsonl realization tracks its OWN work-items in beads; only its
    *tests/acceptance* exercise the jsonl backend). Per the standing rule "a
    required-key schema change is a cross-repo epic," the shared validator means
    every sibling store migrates in lockstep or becomes unreadable. Code blast
    radius (beyond the data migration of the 8 tenants): `livespec_runtime` (the
    `WorkItem` schema — status enum, drop `priority`, add `rank`, `assignee`
    invariant), `livespec-orchestrator-beads-fabro` (custom-status registration,
    2-step `append_work_item`, the `done↔closed` mapping, Dispatcher valves/WIP,
    `list-work-items` lane emission), `livespec-orchestrator-git-jsonl` (status
    enum), and `livespec-console-beads-fabro` (consume the new lane/fields). The
    **remaining D sub-question is D-3** (rank backfill for existing items +
    `priority` drop), which is **coupled to item G** (the fractional-index
    library): the backfill's ORDER strategy (rank existing items by current
    `priority` → `captured_at` to preserve effective order, then drop `priority`)
    can be locked now, but the actual key VALUES it assigns need G's key
    generator — so D-3 is best finalized with, or just after, G.

## Open items (resolve-in-thread / author-in-doc — non-blocking)

- **A.** ✅ **RESOLVED (session 2)** — the full transition table + guards
  are locked above ("Locked transition table (item A)"; decisions 22–32).
  Net: **7 stored states**, `deferred` removed, **`groomed` promoted to the
  `pending-approval` state** (structural grooming gate), `admission_approved`
  dropped (approval ≡ `ready`), one derived overlay (`blocked:dependency`),
  beads custom statuses.
- **A-note** ✅ **RESOLVED (session 3, decision 35)** — reuse the existing
  `assignee` field in place as the claimed-by/owner field (zero migration); one
  field only; "owner ≡ assignee". *Correction:* the A-note's claim that "beads
  has a native `owner` field" was wrong — beads' native field is `assignee` (no
  native `owner`), which is exactly why keeping the abstract name `assignee` is
  the cohesive, zero-impedance choice.
- **B.** Precise `lane_of` signature + its exact home in
  `livespec_runtime`, and the `list-work-items --json` lane-emitting
  shape (the Python ↔ console seam).
- **C.** ✅ **RESOLVED (session 3)** — acceptance verification is **post-merge /
  in-production (observability-driven)**: ship-on-green, then the AI/human
  confirm the *shipped* artifact against tests + telemetry; `reject` =
  revert/fix-forward. `just check` stays the pre-merge correctness floor. See
  decisions 33–34 (which amend the item-A table's `complete`/`accept`/`reject`
  rows).
- **D.** 🟡 **PARTLY RESOLVED (session 3)** — sub-questions:
  - **D-1** ✅ owner ≡ existing `assignee` field, kept in place (decision 35).
  - **D-2** ✅ beads status encoding finalized against verified v1.0.5 source
    (decision 36): 5 custom statuses + `blocked`/`done`→`closed` reuse.
  - **D-4** ✅ fleet repo set = all 8 beads tenants + code blast radius
    (decision 37).
  - **D-3** ⬜ OPEN — `rank` backfill order + `priority` drop; **coupled to item
    G** (needs G's fractional-key generator). Finalize with/after G.
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
