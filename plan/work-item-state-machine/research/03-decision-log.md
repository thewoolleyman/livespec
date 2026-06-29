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

## Locked decisions — session 4 (items G, D-3, B, resolved)

38. **Fractional-index `rank` library = PORT (inline a verbatim copy), and
    rebalance is ON-DEMAND with a `doctor` warning.** *Resolves item G (both
    sub-parts).* Researched against the live code + the library landscape before
    deciding.

    **G-1 (library): PORT, not vendor.** Inline a **verbatim copy** of the
    reference algorithm — `httpie/fractional-indexing-python`, the official Python
    port of **rocicorp/fractional-indexing** (the Figma/David-Greenspan
    fractional-indexing scheme, byte-compatible across JS/Go/Python/Kotlin/Ruby):
    a single self-contained module (~287 lines), **stdlib-only** (`math`,
    `typing`, `decimal`), licensed **CC0-1.0 (public domain)**, public API
    `generate_key_between` / `generate_n_keys_between` / `validate_order_key`. It
    lands at `livespec_runtime/work_items/_fractional_indexing.py` (attribution
    header) behind a thin livespec-facing `rank.py` wrapper (`key_between` /
    `n_keys_between`).
    - **Why PORT over VENDOR — overrides `02-design.md` §5's casual "vendor a small
      pure-Python fractional-indexing implementation" AND the general
      prefer-vendoring rule, for a specific live-code reason:** the `rank` math
      must live in **`livespec_runtime`**, which (a) has **no vendoring machinery**
      — `.vendor.jsonc` + `vendor_update` + the `vendor_manifest` check live only in
      the *consumer* plugin repos, and it carries **zero** vendored libs today
      (sole runtime dep: `typing_extensions`) — and (b) is itself copied
      **source-only** into every consumer's `_vendor/` tree (the copy pulls only the
      `livespec_runtime/` source, **not** its declared deps), while shipped plugins
      run under bare `python3` with `pyproject.toml` stripped (a pip dependency is
      **unreachable** at end-user runtime). So VENDORing would force either standing
      up the vendoring machinery *inside* `livespec_runtime`, or copying the lib
      separately into all **3** consumer plugins and keeping them in sync (cross-repo
      drift). PORTing drops **one file** into the `livespec_runtime` source tree that
      rides along automatically wherever that tree is already vendored — **one source
      of truth, no new machinery, no drift.**
    - **CC0-1.0** is a public-domain dedication → verbatim copy is legally
      frictionless (attribution courteous, not required; still add an attribution
      header + a `NOTICES`/attribution line in `livespec-runtime`).
    - This is **not hand-rolling** — it inlines **the** reference algorithm, honoring
      the project's "use a proven algorithm, don't hand-roll" rule; fractional
      indexing is **finished math**, so the usual port downside (upstream drift) is
      negligible.

    **G-2 (rebalance trigger): ON-DEMAND only.** An explicit `rebalance-ranks`
    command (a deterministic, order-preserving bulk re-key) is the **sole** trigger;
    a key-length threshold drives a **`doctor` WARNING** (discoverability +
    actionable blessed path: "rank keys exceed N chars — run `rebalance-ranks`"),
    **never** an automatic rebalance.
    - **Why:** at the low, append-dominant volume (filing at top/bottom of the
      backlog frontier; tens-to-hundreds of items per repo) long keys are
      essentially a **non-event** (base-62 keys stay <~10 chars for thousands of
      appends). A rebalance is a **churn burst** (N superseding records in git-jsonl
      / N status-metadata updates in beads) best kept **deliberate**. Auto-firing
      would **race concurrent inserts** — the exact hazard **item H** reasons about —
      so keeping rebalance an explicit, non-racing op also de-risks H. The warn
      threshold value is a tunable implementation detail (set generously), not an
      architecture decision.

    **Consequences:** (a) `02-design.md` §5's "vendor … implementation" line is
    **superseded** by the PORT decision (re-synthesized at end of walk); (b) the
    inlined module + `rank.py` wrapper land in `livespec_runtime/work_items/` and
    ride the existing source-only vendoring into all consumers — **no consumer
    `_vendor/` change, no `.vendor.jsonc` entry**; (c) a `NOTICES`/attribution entry
    is added in `livespec-runtime`; (d) `doctor` gains a rank-key-length **warning**
    check; (e) the orchestrator gains a `rebalance-ranks` command; (f) **D-3 is now
    unblocked** — G's `key_between`/`n_keys_between` are the generator D-3's backfill
    uses to assign actual rank VALUES (D-3's pre-agreed ORDER strategy — rank
    existing items by current `priority` → `captured_at`, then drop `priority` — is
    now finalizable; next in the walk).

39. **`rank` is a strictly-required NON-NULL field; `priority` is dropped; the
    backfill is a one-time global re-key reusing `rebalance-ranks`.** *Resolves
    item D-3 — and thereby item D in full.* Grounded in the live store code
    (`livespec_runtime/work_items/reduce.py` + `store.py`) and shaped by the
    maintainer's pushback ("a new field we control doesn't need to be nullable").

    **Type: `rank: str` — required, no default, never `| None`.** *Supersedes the
    nullable proposal floated earlier this session;* re-affirms `02-design.md`
    §6's `+ rank: str`. The maintainer's instinct is correct: a new field we own
    is always set on every record we write going forward. The ONLY records we
    don't control are the pre-`rank` lines already on disk — and because the store
    is **append-only** (a backfill APPENDS superseding records, never rewrites old
    lines) and `reduce.py` **re-parses every historical record** (not just heads)
    to rebuild supersession chains, the read path will forever meet old lines with
    no `rank` key and must answer "what rank does this read as?".

    **That answer is a bottom-sentinel supplied by the STORE ADAPTER, not
    nullability in the type.** When a backend facade (git-jsonl / beads) reads a
    legacy line lacking `rank`, it substitutes a shared **bottom-sentinel** — a
    constant using a char OUTSIDE the lib's base-62 alphabet (`0-9A-Za-z`), e.g.
    `"~"` (0x7E > `z` 0x7A), so it sorts strictly AFTER every real key. The
    domain type stays strict (`rank: str`, every constructor passes a value); the
    legacy read-quirk lives where backend quirks belong (the adapter), kept DRY
    via one shared sentinel constant the two facades import. *(Chosen by the
    maintainer over a type-level `rank: str = "<sentinel>"` default; the strict
    type matches "always required" + the strongest-guardrails Python rule.)* This
    is a deliberate departure from the `= None` blessed-pattern shape used by
    `spec_commitment_hint`/`supersedes`: `rank` has no "absent" meaning (every
    live item HAS a position), so a strict non-null type + an adapter fallback is
    cleaner than a nullable type with None-handling at every sort site.

    **Backfill (the migration, across all 8 tenants — decision 37's blast
    radius).** A rank is NOT a per-record function of one priority (fractional
    keys are assigned relative to neighbors); the backfill sorts the WHOLE set by
    the pre-agreed **`priority → captured_at → id`** order and calls G's
    `n_keys_between(None, None, N)` for evenly-spaced keys. `priority` is required
    (`priority: int`, never null) so there is no null-priority case. Written
    per-backend: git-jsonl = N superseding records each carrying `rank` (and
    omitting `priority`); beads = `metadata.rank`. The backfill produces ONE
    real-ranked head per id, so post-backfill **no live head carries the
    sentinel** (the sentinel only ever surfaces for superseded historical lines).

    **Mechanism = `rebalance-ranks` seeded by the legacy order.** The backfill is
    the SAME deterministic bulk re-key as G's `rebalance-ranks`, just seeded by
    `priority → captured_at → id` instead of by existing-rank order. One command,
    two seed orderings — no separate migration tool.

    **`priority` drop.** Removed from the abstract `WorkItem`;
    `ready_sort_key` (`livespec-orchestrator-beads-fabro` `commands/_cross_repo.py`)
    switches its lead key from `priority` to `rank`. Legacy physical lines keep
    `priority` harmlessly in append-only history; backfilled/new records omit it —
    **no data scrub**.

    **Invariant (doctor-checkable, joins item A's `active ⟹ assignee` family):**
    every live (head, non-superseded) record has a real, non-sentinel `rank`.
    Fail-soft in spirit — a stray sentinel-rank item sorts last and is NAMED by
    doctor, never crashes the listing (the adapter always supplies SOME string, so
    construction never fails). **Consequences:** (a) `02-design.md` §6's `rank`
    row + §5 stand (no nullability); (b) a shared bottom-sentinel constant lands
    in `livespec_runtime.work_items` (imported by both facades); (c) `doctor` gains
    the non-sentinel-rank invariant; (d) the `rebalance-ranks` command gains a
    legacy-seed entry path for the one-time backfill; (e) item D is now **fully
    resolved** (D-1..D-4 all locked).

40. **`lane_of` signature, home, and emitted shape — FULL single-authority
    consolidation into `livespec_runtime`.** *Resolves item B (the
    engineering-signature remainder; the lane TAXONOMY was decision 32).* Grounded
    in the live code: today `is_item_ready`/`ready_sort_key` + the open/closed
    dependency logic live in the orchestrator's `commands/_cross_repo.py`, there is
    **no lane logic anywhere**, and the Rust console does NOT read `list-work-items`
    — it shells `bd ready --json` and re-derives a 3-way lane from the raw status
    string inside `parse_beads_observation` (the drift this retires).

    **Signature + return type:**
    ```python
    def lane_of(*, item: WorkItem, index: dict[str, WorkItem], manifest: CrossRepoManifest) -> Lane

    @dataclass(frozen=True, slots=True, kw_only=True)
    class Lane:
        name: LaneName                  # the 7 rendered lanes
        reason: BlockedReason | None    # non-None iff name == "blocked"
    ```
    `LaneName = Literal["backlog","pending-approval","ready","active","acceptance","blocked","done"]`;
    `BlockedReason = Literal["needs-human","infra-external","dependency"]`. The
    `(item, index, manifest)` triple is EXACTLY what every `is_item_ready` caller
    (`next`, dispatcher, `list-work-items`) already passes — zero new context
    plumbing. Overlay logic: stored `ready` + any open dep → `Lane("blocked",
    "dependency")`; stored `blocked` → `Lane("blocked", <stored blocked_reason>)`;
    every other state → `Lane(<status>, None)`. "Open dep" is the existing
    `is_item_ready` notion (resolve each `depends_on` via `resolve_ref`: a dep
    blocks iff it resolves to `RefStatus.OPEN`, OR the entry is unparseable —
    which fail-closes to blocking; `CLOSED` and `UNKNOWN`/missing-id do NOT block),
    so lane and readiness agree by construction.

    **Home + FULL consolidation (maintainer-chosen over a minimal move).** A new
    module **`livespec_runtime/work_items/lifecycle.py`** (beside `types.py`/
    `reduce.py`/`store.py`) becomes the SINGLE home for the lifecycle logic:
    `lane_of`, the `Lane`/`LaneName`/`BlockedReason` types, `is_item_ready`
    (re-expressed as `lane_of(...).name == "ready"`), `ready_sort_key` (now keyed
    on **`rank`** per decision 39, not `priority`), and the lifted
    open/closed-dependency determination (`parse_entry`/`_entry_blocks`/the
    local-status-lookup — moved out of the orchestrator's `_cross_repo.py`),
    reusing `resolve_ref`/`RefStatus` already in `livespec_runtime.cross_repo`. The
    orchestrator's `next`/`dispatcher`/`list-work-items` IMPORT these from the
    runtime; `_cross_repo.py` shrinks to orchestrator-only bits (`load_manifest`,
    etc.). Rationale: lane_of MUST live in the runtime (decision 15 — Python
    consumers import it, the console consumes its emission), which FORCES the
    dep-logic into the runtime anyway; relocating `is_item_ready`/`ready_sort_key`
    too means "open deps" is computed in exactly ONE place, so the Dispatcher's
    drain order can never diverge from what `next` advertises (the single-authority
    discipline `is_item_ready`/`ready_sort_key` already embody).

    **Emitted shape (the Python ↔ console seam E consumes).** `list-work-items
    --json` adds two computed FLAT keys per item: **`lane`** (rendered lane name,
    one of 7) and **`lane_reason`** (rendered reason: `dependency`/`needs-human`/
    `infra-external`/null). Flat, not nested — matches the existing flat `asdict`
    emitter and the Rust flat-field parser. All other new `WorkItem` fields
    (`rank`, `admission_policy`, `acceptance_policy`, stored `blocked_reason`,
    `assignee`, the 7-state `status`) auto-emit via `asdict`, so only `lane`/
    `lane_reason` are computed additions. **Consequences:** (a) the console (item E)
    switches its source from `bd ready --json` + `parse_beads_observation`'s
    `match status_text` to reading `lane`/`lane_reason` directly; Rust's
    `BeadsWorkItemStatus` 3-way enum + the re-derivation are retired; (b) the new
    cross-repo import edge (orchestrator → `livespec_runtime.work_items.lifecycle`)
    is a fact item **F** must check against the "Driver → orchestrator = zero deps"
    invariant; (c) ride-along cleanup: standardize the `audit` JSON to one
    canonical serializer (the 5-key `reduce.py` form) to kill the current
    3-key-vs-5-key `list-work-items`-vs-`reduce` divergence; (d) item B is fully
    resolved (taxonomy = decision 32; signature/home/shape = here).

## Locked decisions — session 5 (items E, F, H resolved; A–H walk complete)

41. **Item E (the console redesign) is DELEGATED to a console-repo plan thread —
    not designed here.** *Resolves item E.* The boundary: livespec **core** owns the
    CONTRACT (the lifecycle state machine, the `WorkItem` schema in `livespec_runtime`,
    `lane_of` + the `list-work-items --json` emission shape, `rank`, the acceptance
    model); the **console repo** (`livespec-console-beads-fabro`) owns its HOW (the Rust
    redesign, the TUI, ingestion, attention, the conformance test, and any console-LOCAL
    spec invariants). Console-specific design/research/work-items live in the console
    repo, never in livespec core's spec or plan.
    - **Console thread:** `plan/work-item-lifecycle-redesign/` in
      `livespec-console-beads-fabro`, anchored by console-tenant epic
      **`livespec-console-beads-fabro-vqh36l`**, cross-linked to this core epic
      `livespec-35s3zo` as a **prose reference** (NOT a typed cross-tenant `depends_on`:
      that repo's `depends_on` is a flat same-tenant id list, so a cross-tenant id would
      dangle and pollute the `blocked:dependency` derivation).
    - **E resolved there (E-1..E-4), landed on the console repo's master via its PR #60:**
      - **E-1** (source/ingestion): the console switches its work-item source from
        `bd ready --json` (a beads reach-around) → orchestrator **`list-work-items --json`**
        (ALL lanes), parsed as a real JSON array; consumes the emitted `lane`/`lane_reason`
        + new fields; deletes the Rust 3-way `match status_text` lane re-derivation; renames
        the whole `Beads*` cluster to backend-neutral vocabulary; one observed event per item.
      - **E-2** (maintainer): a **hybrid** lane-overview home + full-width per-lane drill-in;
        **Attention = a derived LENS** over the lanes (not a standalone view, not an 8th lane);
        the pseudo-lane tabs Ready/Factory/Manual/Done collapse into the 7 real lanes;
        Spec/Events/Repos stay as orthogonal non-lane views.
      - **E-3** (forced parts): the attention inbox is redefined as a **pure derivation** of
        (`lane`, `lane_reason`, `admission_policy`, `acceptance_policy`); snooze/ack plumbing
        deleted across all 5 console layers; the 3 old triggers accounted for
        (dispatcher-needs-regroom + fabro-human-gate subsumed by the lane; livespec-revise
        relocated to the Spec view); "not now" = defer/re-rank via the orchestrator.
        *(Flagged for impl: confirm the orchestrator/ledger reflects a Fabro human-gate AS
        the work-item's lane.)*
      - **E-4** (maintainer ratified): a **rebuild-from-ledger conformance test** —
        rebuild-determinism (snapshot projections → wipe store → re-backfill from the ledger
        → recompute → assert identical) PLUS a structural "no primary lifecycle state"
        assertion, scoped to work-item projections (lanes + attention lens), **excluding**
        the operator commands table; **DROP** the dead `projections` table; accept
        `commands.status` as console-local operator-command state via a documented carve-out
        (not event-sourced).
    - **Mechanism note:** the console repo's orchestrator pin (v0.2.0) predates the `plan`
      skill, so the thread create-flow was realized manually but conformantly (thread dir +
      epic via the same consented store-writer); forward-compatible with a future `plan`
      resume once that pin bumps (which it must anyway when core ships the lane emission).
    - The console thread's `handoff.md` names its single next action: **groom epic
      `livespec-console-beads-fabro-vqh36l` into dispatchable slices (MAINTAINER-OWNED)**.

42. **The "Driver → orchestrator = zero deps" invariant HOLDS fleet-wide; decision 40's
    lifecycle consolidation uses DEPENDENCY INJECTION, not a verbatim move.** *Resolves item
    F.* Verified the actual dependency edges across all 7 repos against the canonical
    statement (livespec `SPECIFICATION/spec.md` §"Contract + reference implementations
    architecture" — the `zerodep` node; `non-functional-requirements.md` — core
    standalone-installable, "no plane depends on the console").
    - **All four edges HOLD:** (1) **Driver → orchestrator = zero** (both
      `livespec-driver-claude`/`-codex`: empty `[project.dependencies]`, clean `uv.lock`,
      clean manifests, no imports; the only touchpoint is a config-indirected, late-bound
      `revise → capture-impl-gaps` hand-off via `.livespec.jsonc implementation.plugin` — a
      runtime contract, not a build dep). (2) **`livespec_runtime` depends on nothing above
      it** (sole runtime dep `typing_extensions`). (3) **orchestrator → `livespec_runtime`**
      is an existing edge (vendored v0.4.0 + imported). (4) **console → orchestrator-CLI-only**
      (`Cargo.toml` has no beads/fabro/driver/orchestrator crate; the "Beads"/"Fabro" tokens
      in Rust are the console's own observed-domain vocabulary + shell-out strings; zero
      `console → driver` references).
    - **Refinement to decision 40** (the reason F mattered): the `lifecycle.py` consolidation
      is NOT a verbatim move.
      - `ready_sort_key` → **clean move** (and decision 39 already re-keys it on `rank`,
        dropping the old `priority`/gap-tied constants).
      - `is_item_ready` → **cannot move verbatim**: its sibling-lookup reaches beads-specific
        orchestrator code (`resolve_store_config`, the `read_work_items` *free function*,
        `StoreConfig`) that must NOT exist in `livespec_runtime`; moving it as-is creates a
        **back-edge** (runtime → beads). **Fix: move the PURE predicate and INJECT the
        status-lookup callables** (`sibling_status_lookup`/`local_status_lookup` — `resolve_ref`
        already accepts these); the beads store-reading stays in the orchestrator.
      - `lane_of` → **net-new** (exists in no repo today) — a small correction to the
        handoff's "those live in the orchestrator" wording; only `is_item_ready`/`ready_sort_key`
        are relocations.
      - **Net:** decision 40's "FULL single-authority consolidation" stands in spirit
        (`lane_of`/`is_item_ready`/`ready_sort_key` all live in `lifecycle.py` as the one
        authority), but the precise mechanism is **"move the pure core, inject the backend
        I/O,"** which strengthens the runtime's backend-agnosticism. Name-collision caveat:
        runtime's `read_work_items` is a Protocol *method*, not the beads free function.

43. **rebalance-vs-insert race: "never corrupt" CONFIRMED; "off-by-one" CORRECTED to bounded
    benign mispositioning O(cohort size).** *Resolves item H.* Analyzed against the live
    storage/sort/merge model.
    - **NEVER CORRUPT — confirmed:** the append-only, content-addressed supersession reducer
      (`livespec_runtime/work_items/reduce.py`: identity = sha256 of canonical JSON; heads =
      records not named by any sibling's `supersedes`; resolution is content-based and
      order-independent; a concurrently-inserted item is never superseded → no data loss);
      the fractional-index generator only emits valid base-62 keys (never unparseable); the
      sort key ends in `id` (unique tie-break), so even an identical-rank collision yields a
      deterministic total order. **git-jsonl:** a fork is a SURFACED divergent-head finding
      (`no_divergent_heads` check), never silent — and rebalance-vs-insert does not even
      create one (they touch different ids). **beads:** last-write-wins on one SQL row (the
      Dolt server serializes), so no divergence is possible.
    - **"OFF-BY-ONE" CORRECTED → bounded benign mispositioning up to O(cohort size):** because
      a rebalance rewrites the ABSOLUTE key values of the inserted item's old neighbors, the
      item's fixed old-relative key can land several slots away (bounded by the cohort the
      rebalance compressed past it), not just one. It stays fully ordered, parseable, and
      unambiguous, and SELF-HEALS on the next rebalance that observes it.
    - **Mitigation already in place:** decision 38 G-2's **on-demand-only** rebalance (never
      auto-fire) keeps the race rare and deliberate, so the worst case stays academic at the
      stated volume. No new machinery is needed; the `(rank, id)` tie-break + the
      divergent-head check are the safety net. *(Operational note, not a hard requirement:
      prefer running `rebalance-ranks` during quiescence.)*

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
- **B.** ✅ **RESOLVED (session 4, decision 40)** — `lane_of(*, item, index,
  manifest) -> Lane` (a `{name, reason}` dataclass), homed in a new
  `livespec_runtime/work_items/lifecycle.py` with FULL single-authority
  consolidation (`is_item_ready`/`ready_sort_key` + dep-resolution relocate there;
  orchestrator imports them). `list-work-items --json` emits flat `lane` +
  `lane_reason`; the console consumes them directly (retiring its `bd ready`
  re-derivation). Taxonomy was decision 32.
- **C.** ✅ **RESOLVED (session 3)** — acceptance verification is **post-merge /
  in-production (observability-driven)**: ship-on-green, then the AI/human
  confirm the *shipped* artifact against tests + telemetry; `reject` =
  revert/fix-forward. `just check` stays the pre-merge correctness floor. See
  decisions 33–34 (which amend the item-A table's `complete`/`accept`/`reject`
  rows).
- **D.** ✅ **RESOLVED (sessions 3–4)** — sub-questions all locked:
  - **D-1** ✅ owner ≡ existing `assignee` field, kept in place (decision 35).
  - **D-2** ✅ beads status encoding finalized against verified v1.0.5 source
    (decision 36): 5 custom statuses + `blocked`/`done`→`closed` reuse.
  - **D-3** ✅ **(session 4, decision 39)** — `rank` is a strictly-required
    NON-NULL `str` (store adapter supplies a bottom-sentinel for legacy lines, not
    a nullable type); backfill across all 8 tenants from `priority → captured_at →
    id` via G's `n_keys_between`, reusing `rebalance-ranks` (legacy-seeded);
    `priority` dropped (no scrub); doctor invariant = every live item has a real
    rank.
  - **D-4** ✅ fleet repo set = all 8 beads tenants + code blast radius
    (decision 37).
- **E.** ✅ **RESOLVED (session 5, decision 41)** — DELEGATED to the console-repo plan
  thread `plan/work-item-lifecycle-redesign/` (epic `livespec-console-beads-fabro-vqh36l`,
  cross-linked to `livespec-35s3zo`); E-1..E-4 resolved + landed on the console repo's
  master. Core owns the contract; the console repo owns its HOW.
- **F.** ✅ **RESOLVED (session 5, decision 42)** — the invariant HOLDS across all four
  fleet edges; decision 40's `lifecycle.py` consolidation moves the PURE predicate and
  INJECTS the backend status-lookup callables (no runtime→beads back-edge). `lane_of` is
  net-new, not a relocation.
- **G.** ✅ **RESOLVED (session 4, decision 38)** — **PORT** (inline a verbatim
  CC0-1.0 copy of the rocicorp/httpie fractional-indexing reference module into
  `livespec_runtime/work_items/`, behind a thin `rank.py` wrapper), not vendor
  (livespec_runtime has no vendoring machinery and is itself vendored source-only
  into consumers). Rebalance is **on-demand** (explicit `rebalance-ranks` command)
  with a **`doctor` key-length warning** for discoverability; never auto-fires.
- **H.** ✅ **RESOLVED (session 5, decision 43)** — "never corrupt" CONFIRMED
  (content-addressed append-only reduce + always-valid keys + `(rank, id)` tie-break +
  surfaced divergent-head check); "off-by-one" CORRECTED to bounded benign mispositioning
  O(cohort size), self-healing; on-demand-only rebalance keeps it academic.

## Sources

- External grounding + citations: `01-prior-art.md`.
- Current-state ground truth (the five-concept map, the Beads field
  model, the console blast radius) and the full reasoning trail:
  `../conversation/transcript.md`.
