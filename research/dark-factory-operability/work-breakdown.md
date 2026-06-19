# Human-led work breakdown for the dark factory (research / OPEN)

**STATUS: OPEN RESEARCH — actively iterating; NOT ratified, NOT spec.**
This is a living deliberation, expected to span multiple sessions. No
work-items are filed by this document. Nothing here is load-bearing;
ratified decisions later flow into ledger work-items and, where durable,
into the spec via `/livespec:propose-change` → `/livespec:revise`
(per `research/CLAUDE.md`).

**The question, framed by the user (2026-06-16):** now that the family has
cut over to **Fabro**, what is the standardized, *human-involved* way to
**break down and split work items into manageable chunks that can be fed
into the factory**? This is the maintainer's judgment layer that sits
BEFORE autonomous dispatch. It can happen at work-item **capture** time or
in a later **grooming** pass — *both will happen and both matter*. The user
named this "the key unknown part and the largest hole and unknown in this
whole ecosystem and project." This document is deliberately scoped to the
**front-end human decomposition step** — NOT the downstream
queue/prioritize/drain mechanics (which are comparatively well understood;
see the "Downstream — parked" appendix for what we already concluded there
so we don't re-derive it).

**Reading order:** the 2026-06-16 *research findings* below are durable and
unchanged; a **2026-06-19 round-2 pass** then resolves the named-but-absent
shops from round 1. The **2026-06-19 reframe** (after the research) **supersedes
the earlier synthesis** wherever they conflict, and the **slice cut-line**, the
**grooming ritual**, and **slice-size calibration** carry the current state.

---

## Why this is the hard part (and the honest headline)

Deep multi-source research (2026-06-16, adversarially verified; see
§Research findings) produced a blunt result that *validates the user's
instinct*: **the field has converged on a repeatable PATTERN for the human
breakdown step, but nobody has actually solved the SIZING question.** There
are essentially **no documented quantitative "agent-sized" cut-points** in
the verified record — max diff, max files, blast-radius, context-window-fit,
"one-PR" sizing all turn out to be folklore that did not survive scrutiny.
The closest thing to a verified sizing rule is qualitative: **one
independently-testable vertical slice (a user story / scenario).** So on the
specific thing the user called the biggest hole, the field confirms it is
unsolved — **we will be partly inventing this**, and that is why careful
thought matters more than speed here. (Round 2 below re-confirmed this across
six more shops: still nobody publishes a numeric cut-point.)

---

## Research findings (2026-06-16)

Method: 5-angle fan-out web research → 21 sources fetched → 104 claims
extracted → top 25 adversarially verified (3-vote, need 2/3 to refute).
**Caveat on confidence:** the verification pass was partially rate-limited
(many votes failed with transient API errors and abstained), so "did not
survive" sometimes means "unconfirmed this pass," not "disproven." The
items below are the ones that held at **3-0**.

### Verified patterns (high confidence)

1. **Agent-DRAFTS, human-APPROVES — not human-authors-unaided.**
   Devin 2.0 "Interactive Planning": the agent researches the codebase and
   proposes a plan (relevant files, key findings, implementation questions)
   in seconds; the human edits/approves before autonomous execution. The
   load-bearing rationale for *us*: Cognition states *"scoping a task in
   detail and clarifying what to do can consume just as much time as actual
   execution."* The decomposition itself is the expensive part — which is
   why the draft is offloaded to an agent and the human stays editor/gate.
   *Caveat:* Devin's gate is opt-in with a ~30 s auto-proceed (a capability,
   not an enforced step). [cognition.ai/blog/devin-2; docs.devin.ai]

2. **Decomposition is a distinct, LATER phase — not done at capture.**
   GitHub Spec-Kit runs `constitution → specify → (clarify) → plan → tasks
   → implement`. Breakdown into units happens only at `/tasks`, *after* spec
   + plan exist ("you cannot implement before you have tasks"). Multi-step
   refinement, not one-shot. [github/spec-kit; developer.microsoft.com]

3. **The one verified sizing primitive: unit = an independently-testable
   vertical slice (a user story).** Spec-Kit maps the spec hierarchy onto
   units *by user story* — each story becomes its own implementation phase
   with its own task set and a *checkpoint that validates independent
   functionality*, designed to be "independently completable and testable."
   The cut-line that held up: **if a slice has exactly one acceptance you can
   verify on its own, it's a chunk; if it needs several independent ones,
   split.** [github/spec-kit]

4. **Dependencies ARE the parallelism model.** Beads' `bd graph` layers the
   dependency graph: Layer 0 = no blockers (start immediately), same layer =
   parallel, higher layers wait. This is a planning/visualization output,
   not a runtime enforcer. [steveyegge/beads DEPENDENCIES.md; ianbull.com]

5. **"Ready" is mechanical — but is NOT a full definition-of-ready.**
   A Beads item is "ready" precisely when ALL blocking dependencies are
   closed (`bd ready`, filterable by priority/label/assignee). Crucially the
   research flagged: **dependency-readiness carries no acceptance criteria** —
   the "is it verifiable?" dimension must come from the spec/scenario layer.
   [steveyegge/beads DEPENDENCIES.md]

6. **Spec + scenarios as the driving unit; human effort relocates to spec
   authoring.** StrongDM's Software Factory: *"specs + scenarios drive agents
   that write code, run harnesses, and converge without human review"*; "code
   must not be written by humans / reviewed by humans." Human role = author /
   curate the spec + scenario hierarchy and watch the scores. (Stanford CodeX
   corroboration: "humans design specifications, curate test scenarios, and
   watch the scores.") [factory.strongdm.ai; simonwillison.net first-hand]

7. **The acceptance reframe: "satisfaction," not green/red.** StrongDM
   replaced boolean "tests green" with **satisfaction** — *of all observed
   agent trajectories through all scenarios, what fraction likely satisfy the
   user* — judged by LLM-as-judge, "because tests can be reward-hacked." The
   loop runs until holdout scenarios pass and stay passing.
   [factory.strongdm.ai]

### What did NOT survive verification (do NOT re-tread these as fact)

Future sessions: these are intuitively attractive and widely repeated, but
the evidence did not hold them up under three-vote scrutiny. Treat as
**unconfirmed**, not established:
- Quantitative sizing rules generally (max-diff / max-files / blast-radius /
  context-window-fit / "one-PR"). **None verified.**
- "Single-responsibility / minimal-side-effects" as a stated agent-sizing
  heuristic (arxiv 2606.05391) — unconfirmed (0-0).
- Beads' own rationale that *hierarchical-markdown plans fail under
  compaction* and *fine-grained issues keep the agent at context-window
  start / run quadratically cheaper* — unconfirmed (0-0). (Cite the *layering
  model*, not these rationales.)
- StrongDM's *"scenario stored OUTSIDE the codebase as an ML-style holdout,
  immune to reward-hacking"* decoupling mechanism — refuted/unconfirmed
  (1-0/0-0). Cite "scenarios drive + satisfaction metric," not the holdout
  mechanism.
- Spec-Kit's `[P]` parallel-marker-as-dispatch-tag and the
  models→services→endpoints ordering — unconfirmed (1-0/0-0).

### Named-but-absent

These were named in the research brief but produced **no claims that
survived verification**, so we have no documented breakdown ritual for them
(they don't publish one, or this pass couldn't confirm it): **Fabro
workflows, Cursor's software-factory-at-scale, Stripe's ~1,300-PR/week
"minions" harness, Factory.ai, MindStudio Remy, Dan Shapiro's "five
levels."** Worth a targeted follow-up pass (see §Open questions).

**→ This list was RESOLVED by a targeted round-2 pass — see "Research
findings — round 2 (2026-06-19)" immediately below.**

### Primary sources (for future re-reading)
- Devin 2.0 Interactive Planning — cognition.ai/blog/devin-2, docs.devin.ai
- GitHub Spec-Kit — github.com/github/spec-kit (v0.10.3, Jun 2026)
- Beads — github.com/steveyegge/beads/blob/main/docs/DEPENDENCIES.md
- StrongDM Software Factory — factory.strongdm.ai (+ simonwillison.net first-hand, Feb 2026)
- Fabro (execution layer, for context) — github.com/fabro-sh/fabro, docs.fabro.sh

---

## Research findings — round 2 (2026-06-19): the named-but-absent shops, resolved

A targeted second pass (deep-research harness: 6 angles → 25 sources → 123
claims → top 25 adversarially verified, **23 confirmed / 2 killed**) resolved
the round-1 "named-but-absent" list. **Headline: across all six shops the
human-led front-end breakdown layer this doc is about is either ABSENT or
DELEGATED TO THE AGENT — none documents a human-*authored* decompose-and-size
ritual.** The field's only published breakdown ritual is **agent-drafts /
human-approves** (the Devin / Spec-Kit pattern), which endorses our direction.
And the load-bearing confirmation: **not one of the six publishes any
quantitative agent-sizing cut-point**, re-confirming round 1's "all folklore"
result and making our learn-from-run-data calibration genuinely net-new.

### Verified (high confidence)

- **Stripe "minions" — named-but-absent for breakdown.** A run goes from a
  Slack message to a CI-passing PR "with no interaction in between"; there is
  no decomposition/sizing step between trigger and dispatch. "Blueprints" are
  code-authored *execution* workflows, not a per-task human breakdown. The
  human gate is POST-generation PR review, not pre-dispatch. No quantitative
  cut-point — the "2 CI iterations maximum" is a downstream retry bail-out,
  not a sizing rule. [stripe.dev/blog/minions-… parts 1–2; corrob. ByteByteGo,
  InfoQ, ChatPRD]
- **Cursor scaling-agents — agent-only, zero humans in the breakdown loop.**
  "Planner" agents continuously explore the codebase and create tasks (and
  spawn recursive sub-planners); "worker" agents execute; a "judge" agent
  decides completion. No per-task sizing rule (only aggregate throughput
  numbers). **Caveat (load-bearing for use):** this is an internal
  long-running-autonomy RESEARCH demo — only one sub-task was actually merged
  to production — NOT a battle-tested production grooming ritual.
  [cursor.com/blog/scaling-agents; corrob. Willison, ZenML]
- **Factory.ai — the one shop with an explicit ritual, and it's
  agent-drafts/human-approves.** TWO documented forms:
  - *Missions:* `/enter-mission` opens an interactive scoping conversation
    ("clarifying questions, probing for constraints, iterating on the plan…
    a conversation, not a one-shot prompt. The planning phase is where most
    of the value comes from"); the orchestrator then DRAFTS a
    milestone→feature decomposition that the human can inspect / edit /
    override / approve before execution.
  - *Specification Mode:* a 4–6-sentence human outcome description → the droid
    DRAFTS a full spec + acceptance criteria + implementation plan +
    file-by-file breakdown, **hard-gated read-only (cannot mutate anything)
    until the human approves** (approve / iterate / approve-and-set-autonomy).
  - NO quantitative sizing rule; Factory **explicitly lists "worker scope
    (narrow vs broad)" as an UNRESOLVED open question** and admits "the
    orchestrator still scopes too broadly sometimes."
    [factory.ai/news/missions(-architecture); docs.factory.ai/…/specification-mode]
- **Fabro — pure execution/topology layer, no breakdown at all.** Its DOT
  language reference and workflow-authoring skill cover only runtime
  control-flow (agent / prompt / command / human-gate / parallel-fan-out /
  fan-in / manager-loop nodes; "pick the simplest topology"); it explicitly
  *assumes the human has already decomposed work into agent-feedable tasks.*
  Its canonical plan-approve-implement uses an AGENT-drafted plan + a human
  gate. Its only numeric ceilings are runtime governors (`max_parallel`
  default 4; `max_node_visits`; retries) — not work sizing. The "50-file
  diff" line is a marketing analogy. [docs.fabro.sh/reference/dot-language;
  fabro README; fabro-create-workflow SKILL.md]
- **Dan Shapiro "five levels" — named-but-absent (qualitative only).** The
  Level-4 human is a PM who "writes a spec… plans schedules… reviews plans";
  no ritual, no checklist, no number. Level 5 NAMES "ability to scope tasks
  well" as the limiting skill but attaches no metric.
  [danshapiro.com/…/the-five-levels; simonwillison.net]

### Refuted / unresolved (do NOT assert as fact)

- **"Cursor explicitly rejected upfront/static planning as too rigid"** —
  REFUTED 0-3 (overreach; the post describes recursive agent planning, not a
  rejection of upfront planning).
- **"Factory Code Droid does agent-side decomposition with no human gate"** —
  REFUTED 1-2 (the Code-Droid technical report is superseded by Missions +
  Specification Mode, which DO gate on a human).
- **MindStudio "Remy" — UNRESOLVED.** Produced no surviving verified claim
  this pass. Treat as *unknown*, not "absent" — needs a direct re-research
  before being relied on (see §Open questions).

### What round 2 changes for our design

1. **Agent-drafts / human-approves is vindicated as THE ritual** — it is the
   only breakdown ritual anyone publishes (Factory ×2; Fabro's canonical
   workflow; the Devin / Spec-Kit lineage), and no shop uses pure
   human-authored breakdown. Our "agent drafts the split, human owns the cut
   + the acceptance" is the field consensus, not a bet.
2. **Concrete patterns to borrow for the regroom gate:** keep the draft
   **read-only until the human approves** (Factory Specification Mode), and
   anchor each slice on **the acceptance / assertion it claims to fulfill**
   (Factory: "a feature is a bounded piece that claims which assertions it
   will fulfill" + a per-milestone validation checkpoint) — which is exactly
   our two-mode cut-line seen from the outside.
3. **There is NO published intake-readiness CHECKLIST to copy.** Ours stays
   net-new; the closest analog is Factory's "bounded piece + finite validation
   contract." Anchor the checklist on the acceptance the slice claims.
4. **Borrow Factory's dependency-layering as the reference model:**
   milestone → feature, with a FRESH-CONTEXT worker per feature and a
   validation checkpoint per milestone. It maps cleanly onto our Beads
   dependency layers (Layer-0 parallelism) + per-slice acceptance + the
   Fabro-sandbox-per-work-item model (fresh context per slice already holds
   for us).

### Round-2 primary sources
- Stripe minions — stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents (+ part-2)
- Cursor — cursor.com/blog/scaling-agents
- Factory.ai — factory.ai/news/missions, /news/missions-architecture, docs.factory.ai/cli/user-guides/specification-mode
- Fabro — docs.fabro.sh/reference/dot-language, github.com/fabro-sh/fabro
- Dan Shapiro — danshapiro.com/blog/2026/01/the-five-levels-…

---

## The 2026-06-19 reframe (supersedes the earlier synthesis)

The prior sessions kept snagging on cross-repo. This session's unlock:
**cross-repo is a category error for this design.** Strip it out and the
general pattern becomes clean.

### Dependency note — a spec relocation this reasoning leans on

A `/livespec:critique` → `/livespec:revise` pass **moved livespec's own
family-infrastructure sections out of the *functional*
`SPECIFICATION/contracts.md` and into `non-functional-requirements.md`** (the
five sections: Cross-repo coordination — pin-and-bump; Shared content sync —
copier template; Shared code sync — livespec-dev-tooling; Shared runtime —
livespec-runtime; Sibling spec ownership). The doctor check
`wiring-completeness-cross-repo` stays a standalone entry under contracts.md
§"Doctor cross-boundary invariants" (the doctor *mechanism* stays functional;
the family roster it reads moved to NFR). A root-cause rule was codified in
NFR §"Boundary": functional files describe only what *any* livespec consumer
inherits; livespec's own family infrastructure is self-application and lives
in NFR.

**Status as of 2026-06-19: MERGED.** The relocation landed on master
(critique `71f9e6c` → revise `c9f3434` → doctor-narration fix `1832eb9`); the
five sections are now `###` subsections in `non-functional-requirements.md`.
So NFR is now literally — not just conceptually — grooming guidance's home.

### The functional / non-functional split is the spine

- livespec's spec separates user-facing **FUNCTIONAL** files (`spec.md` /
  `contracts.md` / `constraints.md` / `scenarios.md`) from
  `non-functional-requirements.md` ("how the project is built / tested /
  maintained" — internal-facing, NOT visible at the user-facing CLI/API
  surface, per its §"Boundary").
- **The grooming pattern is GENERAL.** It must work for *any* project
  governed by livespec, single-repo or many. Multi-repo / cross-repo is
  **livespec's own family self-application** — a non-functional,
  self-application concern — NOT a functional requirement of
  livespec-the-general-system.
- **The ONLY functional connection between multi-repo and core is the CLI
  delegation seam** — the orchestrator-side and spec-side CLIs named in
  `.livespec.jsonc`. Everything else about multi-repo is non-functional.
- Therefore **cross-repo drops out of the general grooming pattern
  entirely.** A single-repo project grooms identically; cross-repo
  coordination is a separate concern layered on top by whoever needs it.

### Terminology correction (use these words)

- It is the **Orchestrator** — the pluggable *producer role* that consumes
  the spec and produces the implementation (`spec.md` §"Contract + reference
  implementations architecture"). NOT "impl plugin" — a plugin is merely how
  one reference orchestrator is *packaged*. The reference orchestrators are
  **git-jsonl** (serial) and **Beads/Dolt + Fabro** (parallel; the family's
  dogfood default).
- The orchestrator decomposes (guidance, NOT contract) into **Ledger**
  (private work-item store + dep graph), **Loop** (produces one work-item),
  **Dispatcher** (polls + parallelizes). Core's contract never names these.

### Where grooming lives (resolved)

- Grooming operates on the **Ledger → it is orchestrator-internal → NOT core
  functional contract.** It never becomes a core CLI or doctor invariant.
- The grooming **pattern / guidance is non-functional** — it belongs in
  core's `non-functional-requirements.md` as orchestrator guidance, alongside
  the existing §"Orchestrator-internal Dispatcher guidance". Repo-agnostic.
- The **concrete realization** (a groom front-end / skill, ready-layering,
  convergence feedback) lives in the **reference orchestrator's OWN spec**
  (e.g. `livespec-impl-beads`'s `SPECIFICATION/`); cf. spec.md's
  "orchestrator-shipped SKILL.md front-ends … in-repo for now".
- The cut-line **PRINCIPLE** reaches down to exactly ONE core functional
  concept: the **scenario / acceptance**.

### What core's cross-repo surface actually is (so we don't re-confuse it)

Verified against the spec this session — core has DELIBERATELY shed
cross-repo *mechanism*, keeping only *consistency-checking + scaffolding*:
- Doctor's whole cross-boundary job = wiring soundness
  (`config-named-cli-callability`) + repo-tier structural invariants. It MUST
  NOT inspect work-items / gaps / dep-graphs / memos (orchestrator-private).
- Relocated OUT of core: pin-and-bump / `compat` (→ dev-tooling); work-item
  dep machinery (→ orchestrator Ledger); the cross-repo loop driver
  (→ retired, now the orchestrator Dispatcher).
- So a cross-repo fan-out (like `livespec-gy21`'s) is something core
  **checks**, never **coordinates** — which is why grooming sits in the
  orchestrator.

### The two schools livespec is both of (durable bridge, now reframed)

The wider field splits into two schools; livespec is *uniquely both*, and
the functional/non-functional split tells us which layer each lands in:

| School | Unit of work | Where human judgment goes | livespec layer | Exemplar |
|---|---|---|---|---|
| **A — Spec-hierarchy-as-source** | a vertical slice / scenario of the spec | authoring + curating spec + scenarios + acceptance | **functional core** (`SPECIFICATION/`, the scenario concept) | StrongDM, Spec-Kit |
| **B — Dependency-graph-issue** | a dependency-linked work-item | the decomposition + the dependency links | **orchestrator-internal** (the Ledger; non-functional) | Beads |

They compose: **the functional spec/scenario layer supplies the cut-line and
the acceptance; the orchestrator's Ledger supplies the unit, the dependency
links, and mechanical readiness.** That composition is the spine of the
three pieces below.

---

## The three pieces — the slice cut-line, the grooming ritual, slice-size calibration

The slice cut-line is largely settled; the grooming ritual has its structure
but open details; slice-size calibration has an approach but no design yet.

### The slice cut-line — where to split — *largely settled*

Pressure-tested "one independently-testable scenario = one slice" against
the real recent epic **`livespec-gy21`** (the project-scoping epic).
Findings:

- gy21 was ONE epic, an internal 5-step checklist, **zero child slices**,
  landed in CORE as 2 commits, and added **zero behavioral scenarios** — yet
  it was real factory work. So the verified "one scenario" rule is a
  **special case**, not the general rule.
- **General cut-line:** *a slice is the smallest unit with exactly ONE
  coherent "done"; two independent "done"s → split.* "Done" is either:
  - **scenario-verified** (one scenario passes) — behavioral feature work; or
  - **gate-verified** (`just check` + `/livespec:doctor` pass, **no
    scenario**) — config / spec-text / refactor / cross-repo-bump work, which
    is what gy21 was.
- The five "archetypes" (feature / spec-change / config / refactor / bump)
  are **worked examples of these two modes, NOT a schema.** (Deliberately
  resisted over-taxonomizing.)
- **New finding — there must be a slice-size FLOOR, not just a ceiling.**
  gy21 bundled a config change + a hook relocation with the *same blast
  radius*; the strict rule would over-split them. Don't split below the point
  where two slices cost more coordination than they save. The floor is an
  input to slice-size calibration (below).
- **Autonomy-tier finding (routing, not cut-line):** spec-change slices are
  **human-gated** (they go through propose-change / revise); everything else
  is **factory-dispatchable**. This feeds where the grooming gate sits (the
  grooming ritual, below).
- **Round-2 corroboration (2026-06-19):** Factory.ai independently frames a
  unit as "a bounded piece that *claims which assertions it will fulfill*"
  with a validation checkpoint — the same "one coherent, independently
  verifiable 'done'" cut-line, arrived at from outside.

### The grooming ritual — how the split gets drafted + approved — *intake checklist + regroom flow drafted; calibration + state-model open*

- **Two touchpoints, gated by a size test (both matter, not competitors):**
  1. **Intake cut at work-item creation** — a cheap readiness check: *is
     this already one actionable slice (one coherent "done", deps known)?* If
     yes → ready. If no → mark not-yet-actionable. The frictionless common
     case.
  2. **Regroom pass (optional, later)** — the heavier draft-decompose that
     actually splits the not-yet-actionable items (epics / too-big) into
     slices. This is the verified "agent drafts, human approves" pattern
     (Devin planner / Spec-Kit `/tasks` / Factory Missions).
- **Per-slice fields the aid drafts** (the cut-line fills most of them):
  - *acceptance* — one scenario (behavioral) OR standing gates (gate-verified).
  - *governance scope* — autonomy tier (spec-change = human-gated; rest = auto).
  - *dependency links* — Beads blockers → Layer-0/1 parallelism.
  - *repo target* — which ledger (cross-repo coordination is NOT grooming's
    job in the general pattern).
  - *scope* — smallest coherent acceptance, respecting the FLOOR.
- **Skill vs. checklist (tentative, in the corrected frame):** intake
  readiness = a **checklist** folded into the existing capture front-ends (no
  new machinery); regroom pass = (tentative) **one orchestrator-shipped groom
  front-end**. Crucially: this is **orchestrator-internal** — the *guidance*
  is non-functional core content; the *front-end realization* is the
  reference orchestrator's own spec — **NOT a core skill / CLI / doctor
  invariant.**
- **Round-2 prior art (2026-06-19):** agent-drafts/human-approves is the
  field's ONLY published breakdown ritual (Factory Missions + Specification
  Mode; Fabro's canonical plan-approve-implement; the Devin/Spec-Kit lineage)
  — our shape is the consensus, not a bet. Two concrete patterns to borrow:
  (a) keep the regroom draft **read-only until the human approves** (Factory
  Specification Mode hard-gates the droid to read-only during analysis); and
  (b) there is **no published intake-readiness *checklist*** anywhere — ours
  is net-new.
- **The earlier cross-repo fork is DISSOLVED.** The old "where does
  cross-repo grooming live — impl-layer vs livespec-layer?" question
  evaporates: grooming is orchestrator-internal; core only ever *checks*
  cross-repo consistency (structural doctor invariants) and *defines the
  scenario concept*.
**The intake-readiness checklist (Definition of Ready) — DRAFTED (2026-06-19).**
Applied by the EXISTING capture front-ends (`capture-work-item`,
`capture-impl-gaps`, …) at creation; cheap by construction — the drafting aid
auto-answers what it can and prompts the human only on the rest. An item is
`ready` only when ALL of these hold; otherwise it is ROUTED, not filed-as-ready:

1. **One coherent "done."** Exactly one acceptance — either ONE named scenario
   (*scenario-verified*) OR "the standing gates fully define done, no scenario"
   (*gate-verified*). Can't name exactly one → it's an epic → `needs-regroom`.
2. **Acceptance is autonomously verifiable.** An agent can confirm done with no
   human judgement call (the scenario passes, or `just check` + `/livespec:doctor`
   pass). If "done" needs human taste → add a verifiable acceptance, or mark it
   human-gated.
3. **Autonomy tier assigned.** spec-change → **human-gated** (routes to
   propose-change / revise; never auto-dispatched); everything else →
   **factory-dispatchable**.
4. **Dependencies linked.** Blockers identified + linked (Beads `blocked-by`).
   Ready = blockers closed (`bd ready`) **AND** an acceptance exists — never
   deps alone (round-1 finding #5).
5. **Repo target named.** One slice → one ledger/repo (cross-repo coordination
   is a separate concern, not grooming's job in the general pattern).
6. **Above the floor.** Big enough to deserve its own slice, else ride along
   with a blast-radius sibling (anti-over-split). The floor is uncalibrated
   until slice-size calibration — human judgement for now.

Routing on failure: gate 1 fails → `needs-regroom`; gate 2 or 4 fails →
`not-yet-actionable`; all pass → `ready` (Layer-0 if no open blockers). This is
a checklist folded into the capture front-ends — **NOT new machinery.**

**The regroom pass (agent-drafts / human-approves) — DRAFTED (2026-06-19).**
Triggered by (a) an intake `needs-regroom` / epic, or (b) **factory
non-convergence** — a dispatched slice that won't converge IS the "too big"
signal; it routes back here, it never infinite-retries:

1. **Read-only draft.** The groom front-end reads the epic + the relevant
   spec/scenarios + the ledger and DRAFTS candidate slices, each with the
   per-slice fields above filled. It proposes; it files NOTHING yet — read-only
   until approved (the Factory Specification Mode pattern).
2. **Layer.** Arrange the drafted slices into dependency layers (Beads blockers
   → Layer-0 dispatches immediately, same layer parallelizes) — the Factory
   milestone→feature model, each slice a fresh Fabro sandbox (fresh context per
   slice already holds for us).
3. **Human approves the cut.** The human edits the cut / acceptance / deps /
   tiers and approves, or sends it back to re-draft (the revise loop). **The
   human OWNS the cut and the acceptance; the aid only drafts.**
4. **File on approval.** Approved slices are filed via the existing
   `capture-work-item` machinery with deps linked; spec-change slices route to
   propose-change / revise, not the factory.
5. **Validation checkpoint per layer.** After a layer converges, re-run
   `just check` + `/livespec:doctor` + the named scenarios before the next layer
   dispatches (Factory's per-milestone validation).

In the dark factory this is the ONE human-in-the-loop step in an otherwise
autonomous loop: the Dispatcher SURFACES `needs-regroom` items
(escalate-don't-drop), a human runs the groom front-end, approves, and the
factory drains the resulting `ready` slices.

**Homes + restraint (anti-over-spec).** The *pattern* above is non-functional
core guidance (NFR, beside §"Orchestrator-internal Dispatcher guidance"); the
*realization* is the reference orchestrator's own spec (`livespec-impl-beads`).
Deliberately few new artifacts: the intake DoR is a checklist on EXISTING
capture front-ends; layering / ready / labels reuse Beads; only the **regroom
front-end** is genuinely new, plus one **`needs-regroom`** ledger state. If
this ever grew past ~one new front-end + one state, stop and reconsider.

**STILL OPEN:** the floor value (blocks gate 6 — needs slice-size calibration);
whether the intake DoR is a HARD refuse-to-file gate or advisory-with-override;
the exact `needs-regroom` state model in the orchestrator's ledger; and whether
intake + regroom are better framed as one mechanism (the DoR gate, and what you
do when it fails) rather than two.

### Slice-size calibration — discovering the limits from real run data — *design drafted; floor-measurement + sample-size open*

- The field has **no quantitative agent-sizing rules** (all refuted as
  folklore — and round 2 re-confirmed it across six more shops). The honest
  move is to **invent + instrument**: pick provisional limits, instrument
  Fabro runs (converged? fix-loop count? wall-clock / cost), and correlate
  with slice-size proxies to discover *our* cut-points empirically rather than
  guess them. Ties to the journal → Honeycomb leg already designed in
  `preconditions.md`.
- **Now also calibrate a FLOOR** (minimum viable slice), not just a ceiling
  — driven by the cut-line's over-split finding.
- **Round 2 (2026-06-19) confirmed there is no field precedent for either a
  ceiling or a floor** — none of six surveyed shops publishes one, and
  Factory.ai openly lists scope (narrow vs broad) as unsolved. Learning both
  from real run data is a genuine net-new contribution, not a codification of
  existing practice — which raises the value of the instrumentation work and
  lowers the chance we're missing an existing answer.
- **Re-decomposition trigger = the agent fails to converge.** Devin re-plans
  per session; StrongDM iterates the spec until scenarios pass.
  Non-convergence *is the signal* the slice was too big — it routes back to a
  human grooming pass (the regroom step above), not an infinite retry.
**The two halves — DRAFTED (2026-06-19).** Don't guess thresholds; emit an
outcome signal + several size proxies into the EXISTING Dispatcher journal →
Honeycomb leg, then correlate to discover which proxies predict trouble.

*Half 1 — the outcome signal (the dependent variable), per Fabro run /
work-item* (most already in the journal; calibration adds the explicit tags):
- **converged?** — reached a merged PR through the janitor gate with no human
  rescue.
- **fix-loop count** — verify→fix iterations before green (the graded signal;
  Stripe's "2 CI iterations max → bail to human" is the analog).
- **outcome class** — converged-clean / converged-hard / non-converged→regroom
  / non-converged→human-rescue.
- **wall-clock + token/cost** — the economic axis.
- **bounced-to-regroom?** — the strongest "too big" label.

*Half 2 — the size proxies (candidate predictors; correlation picks the
winners), all mechanical, no human judgement:*
- **acceptance count** (should be 1 by the cut-line; >1 ⇒ mis-cut),
- **diff size** (files / lines in the merged PR),
- **dependency fan-out** (blocker / blocked-by degree),
- **spec surface touched** (# spec sections / scenarios referenced),
- **dispatch context size** (goal description + referenced-file bytes —
  "scoping consumes as much as execution", Cognition),
- **archetype** (feature / spec-change / config / refactor / bump — a
  categorical to stratify by), **repo** (stratify; ceilings may differ).

**Ceiling vs floor are asymmetric — be honest about it.** The ceiling has a
direct outcome signal (non-convergence / rising fix-loops), so it calibrates
straightforwardly: the proxy value(s) above which trouble spikes. The **floor
has no direct signal** — over-splitting's cost is a *counterfactual* ("the
merge you didn't bundle"), which the data never shows. So the floor needs a
different method: detect retrospective **bundling candidates** (sibling slices,
same layer + same file-set + no real independence) and measure their aggregate
*fixed* overhead (sandbox spin-up + dispatch + review not spent on actual
change). Floor work is harder and lags the ceiling.

**Two ways to use the ceiling (the key insight):**
- **Reactive** — bail after N fix-loops → route to regroom. Doable TODAY,
  no calibration needed (it's already the non-convergence trigger above).
- **Predictive** — flag oversized at intake (cut-line gate 6's ceiling).
  Needs calibration — and **the reactive bail-out is its training signal.**

**Cold-start phasing** (calibration needs runs, but dispatch needs a rule):
1. **Phase 0** — dispatch on the cut-line's qualitative "one coherent done" +
   a generous human-guessed ceiling + floor = human judgement; reactive
   bail-out ON; instrument everything.
2. **Phase 1** — once runs accrue, the analysis pass proposes data-backed
   thresholds; a human reviews + adopts them into the intake checklist.
3. **Phase 2** — thresholds become **advisory** inputs to gate 6 + regroom;
   re-calibrate periodically (model + codebase drift; the field moves fast).

**This resolves the grooming ritual's hard-vs-advisory question, by gate
type:** the *size* gate (gate 6) is **advisory** (data-derived, uncertain);
the *structural* gates (one coherent done, acceptance exists, deps linked) can
be **hard**.

**Homes + restraint.** Orchestrator-internal: the *pattern/guidance* →
non-functional core (NFR, beside §"Orchestrator-internal Dispatcher guidance"
and the telemetry precondition in `preconditions.md`); the *realization*
(journal fields, Honeycomb queries, the analysis pass, the adopted thresholds)
→ the reference orchestrator's spec + its telemetry leg. New artifacts are few:
outcome + size FIELDS on the EXISTING journal + ONE periodic analysis pass (a
query + correlation, not an always-on service).

**The honest risk.** We're inventing what the field hasn't solved; messy run
data with confounders (model version, code area, flakiness) may not yield clean
thresholds fast. Mitigation: thresholds stay provisional + advisory — the
cut-line's qualitative "one coherent done" remains the primary rule, the
numbers a secondary safety net the data calibrates.

**STILL OPEN:** the floor's counterfactual measurement method; the minimum
sample size before a threshold is trustworthy; the re-calibration cadence
against model/codebase drift.

---

## Realization & UX (draft — lands in the orchestrator's spec when ratified)

The three pieces above are repo-agnostic PRINCIPLE. This section sketches the
concrete REALIZATION for the reference Beads/Dolt + Fabro orchestrator — what
the maintainer actually does, which skills change, and what (if anything)
touches Fabro. Per the reframe, this realization belongs in
`livespec-impl-beads`'s OWN spec when ratified; it is captured here as draft
thinking, not core contract.

### The maintainer's experience — four touchpoints, one new

1. **Capture (intake) — augmented, frictionless.** File work as today via
   `capture-work-item` / `capture-impl-gaps`. The skill now runs the
   Definition-of-Ready checklist in-dialogue, auto-answering what it can and
   asking only the rest, and tags the item `ready` / `needs-regroom` /
   `not-yet-actionable`. Most small items pass with one confirmation.
2. **Groom (regroom) — the one new surface.** For `needs-regroom` items run
   `groom <id>` *(name provisional)*: a read-only scoping conversation that
   DRAFTS a layered decomposition (slices pre-filled with acceptance / tier /
   deps / repo / scope); you edit + approve (or send back); on approval it
   files the slices via `capture-work-item`. Spec-change slices route to
   `/livespec:propose-change`.
3. **Dispatch — unattended, exceptions only.** The Dispatcher drains `ready`
   slices into Fabro sandboxes by dependency layer, gates each on `just check`
   + `/livespec:doctor`, merges, closes. It pulls you in only to SURFACE a
   `human-gated` (spec-change) item or a `needs-regroom` bounce
   (escalate-don't-drop → back to touchpoint 2).
4. **Calibration — mostly invisible.** A periodic report correlates run
   outcomes against size proxies and proposes ceiling thresholds; adopting
   them makes the intake size-gate flag oversized items advisorily.

### Skills: augmented vs new

**Augmented** (existing impl-plugin skills):
- `capture-work-item`, `capture-impl-gaps` — run the intake DoR + readiness tag.
- `process-memos` — route impl-bound memos through the same DoR.

**New** (exactly one): `groom` *(name provisional)* — the
agent-drafts/human-approves regroom front-end.

**Not skills** (orchestrator machinery):
- The **Dispatcher** — refuse to auto-dispatch `human-gated`; on
  non-convergence → mark `needs-regroom` + surface (not infinite-retry); emit
  calibration telemetry. (The Dispatcher SURFACES `needs-regroom`; `next` is
  the pull-based ranker and would merely gain "regroom this epic" as an action
  — and per work-item `livespec-impl-beads-i3jiny`, the Dispatcher should
  *compose* `next`'s ranking rather than re-rank inline.)
- One new ledger state `needs-regroom`.
- The calibration analysis pass (a periodic report over the journal — not a
  skill).

Core gets NONE of this — only the non-functional GUIDANCE in NFR. The skills,
ledger state, and analysis are the reference orchestrator's own.

### Fabro changes — almost none

Breakdown is entirely UPSTREAM of Fabro (ledger + Dispatcher + skills); Fabro
"assumes the human has already decomposed work into agent-feedable tasks"
(round 2). So **no Fabro platform/setup change.** Only two touchpoints:
1. **Capture run outcomes (Dispatcher-side, no Fabro change):** the Dispatcher
   already reads Fabro run state (Working→Pending→Verify→Merge) and writes the
   journal; calibration just records the outcome signal + size proxies there.
2. **One Fabro workflow-DOT tweak (the reactive ceiling):** Fabro's graph
   already has verify→fix-loop nodes + a `max_node_visits` governor; set a
   fix-loop cap + a "non-converged" exit edge that routes back to the
   Dispatcher (→ `needs-regroom`). Within Fabro's existing DOT vocabulary.

Per-slice sandboxing (fresh context per work-item) is already how the
Dispatcher uses Fabro — unchanged.

### Open realization choices
- **Hard vs advisory gate** — resolved by gate type: structural gates (one
  done / acceptance / deps) hard; size gate advisory (data-derived).
- **`groom` as a separate skill** (recommended) vs. an "epic mode" of
  `capture-work-item`.
- The exact **`needs-regroom` ledger representation** (label vs. status).

---

## Open questions / unknowns (carry forward)

1. **Quantitative sizing** — what numeric proxies actually predict
   "agent-one-shottable" *for our work* (mostly spec-governed Python +
   cross-repo config)? Unsolved in the field (round 2 confirmed); slice-size
   calibration is our path to an answer — and it now must yield both a ceiling
   and a floor.
2. **Capture vs. grooming trigger rituals** — who/what triggers
   re-decomposition? Tentative: non-convergence routes to a human regroom
   pass. Needs a concrete state model in the Ledger (a `needs-regroom`
   state?), which is orchestrator-internal — so it belongs in the reference
   orchestrator's spec, not core.
3. **Does "satisfaction" (probabilistic LLM-judge acceptance) generalize**
   beyond StrongDM's agentic-software domain to our mostly-deterministic
   spec-governed code? Or is `just check` + `/livespec:doctor` + one scenario
   already our sufficient, deterministic acceptance? Lean: deterministic-first
   is fine for us; satisfaction is a fallback for genuinely agentic slices.
4. **The School-A → School-B handoff seam.** How does spec decomposition
   (propose-change → revise producing scenarios) hand off to impl
   decomposition (orchestrator Ledger slices)? In the reframe this is the
   functional/non-functional seam: the functional scenario concept supplies
   the cut-line; the orchestrator's Ledger consumes it. Under-specified — the
   exact handoff mechanics are the grooming ritual's remaining work.
5. **MindStudio "Remy" stays unresolved.** Round 2 found no verifiable Remy
   breakdown/grooming step — unknown whether none exists or it wasn't sourced.
   Re-research directly before relying on it as "named-but-absent."
6. **Has anyone since published empirical scope-calibration data?**
   Factory.ai openly admits scope (narrow vs broad) is unsolved; if Factory
   (or another shop) later ships a granularity heuristic or post-hoc data, it
   could seed our ceiling/floor.
7. **Do any shops tune decomposition from REAL RUN DATA** (merge rate, retry
   count, CI-iteration count, successful-one-shot diff size) — even
   informally? That would validate our learn-from-run-data calibration against
   practice, not just doctrine.

---

## Decision log

- **2026-06-16** — Scope locked to the *human front-end breakdown* step;
  downstream prioritize/drain explicitly parked (appendix). (User direction.)
- **2026-06-16** — Tentative direction: unit = vertical slice anchored to one
  scenario; agent-drafts/human-approves; dependency-layer for parallelism;
  DoR = deps + acceptance + governance; re-decomposition on non-convergence.
  **NOT ratified** — pending the three pieces below.
- **2026-06-16** — "Skill?" answer evolved: a *drafting* grooming aid is
  justified for breakdown (was "probably not"); downstream stays policy, not
  skill. Skill-vs-checklist deferred to the grooming-ritual work.
- **2026-06-19** — **Reframe: cross-repo is a category error here.** The
  functional / non-functional split is the spine; the grooming pattern is
  GENERAL (single- or multi-repo identical); cross-repo is livespec's own
  *self-application* (non-functional), and its only functional tie to core is
  the `.livespec.jsonc` CLI delegation seam. **Cross-repo drops out of the
  general pattern.**
- **2026-06-19** — **Terminology fixed:** it is the **Orchestrator** (the
  producer role), not "impl plugin"; references **Ledger / Loop / Dispatcher**
  (orchestrator-internal decomposition; core's contract never names them).
- **2026-06-19** — **Where grooming lives, resolved:** grooming is
  orchestrator-internal (operates on the Ledger) → NOT core functional
  contract; the *pattern/guidance* is non-functional core content; the
  *concrete front-end* is the reference orchestrator's own spec; the cut-line
  principle reaches exactly ONE core functional concept — the scenario /
  acceptance. The earlier impl-layer-vs-livespec-layer cross-repo fork is
  **dissolved**.
- **2026-06-19** — **The slice cut-line, two modes:** a slice has exactly one
  coherent "done," either *scenario-verified* OR *gate-verified*; the
  verified "one scenario" rule is the scenario-verified special case. The five
  archetypes are worked examples, not a schema. Added a slice-size **FLOOR**
  (anti-over-split), calibrated under slice-size calibration. Autonomy tier:
  spec-change = human-gated, rest = factory-dispatchable.
- **2026-06-19** — **The grooming ritual, structure:** two touchpoints
  (intake checklist at creation + optional later regroom pass); per-slice
  fields enumerated; intake = checklist folded into capture front-ends,
  regroom = a single orchestrator-shipped groom front-end (tentative). Exact
  draft/gates still open. **NOT ratified.**
- **2026-06-19** — **The grooming ritual, concrete draft:** the intake
  Definition-of-Ready checklist (6 gates → `ready` / `needs-regroom` /
  `not-yet-actionable`, folded into existing capture front-ends) and the
  regroom pass (read-only draft → layer → human approves the cut → file →
  per-layer validation checkpoint; triggered by epics OR factory
  non-convergence). Borrows Factory's read-only-until-approved gate and
  milestone→feature layering. Restraint: one new front-end + one
  `needs-regroom` state, everything else reuses Beads + the capture
  front-ends. **NOT ratified;** open: floor value, hard-vs-advisory gate,
  ledger state model.
- **2026-06-19** — **Slice-size calibration, concrete draft:** instrument an
  outcome signal (converged? / fix-loop count / outcome class / cost /
  bounced-to-regroom) and several mechanical size proxies (acceptance count,
  diff size, dep fan-out, spec surface, context size, archetype, repo) on the
  EXISTING Dispatcher journal → Honeycomb leg; correlate to discover the
  ceiling. Ceiling/floor are asymmetric — the ceiling has a direct
  non-convergence signal; the floor is a counterfactual needing bundling-candidate
  detection. Two uses of the ceiling: reactive fix-loop bail-out (today) trains
  the predictive intake flag (post-calibration). Cold-start phasing; size gate
  is **advisory** while structural gates can be **hard** (resolves the grooming
  hard-vs-advisory question). Restraint: journal fields + one analysis pass.
  **NOT ratified;** open: floor measurement, sample size, re-calibration cadence.
- **2026-06-19** — **Realization & UX sketched:** four maintainer touchpoints
  (capture/intake → groom → dispatch → calibration), the augmented-vs-new skill
  inventory (augment `capture-work-item`/`capture-impl-gaps`/`process-memos`;
  one new `groom` front-end; Dispatcher + `needs-regroom` state + calibration
  pass as non-skill machinery), and the Fabro answer: **no platform change** —
  only Dispatcher-side outcome capture + one DOT fix-loop-cap/non-converged-exit
  tweak. Realization belongs in the orchestrator's own spec when ratified.
  Surfaced the `next`/Dispatcher ranking-divergence fix as work-item
  `livespec-impl-beads-i3jiny`. **NOT ratified.**
- **2026-06-19** — **Round-2 research (the named-but-absent shops, resolved):**
  a second deep-research pass (25 sources, 25 claims verified, 23 confirmed /
  2 killed) found NO shop publishes a human-authored breakdown ritual and NO
  shop publishes a quantitative agent-sizing cut-point (re-confirming "all
  folklore"). Agent-drafts/human-approves is the field's only ritual
  (vindicating our direction); slice-size calibration is net-new; borrow
  Factory's milestone→feature dependency-layering + read-only-until-approved
  gate. MindStudio Remy unresolved; two claims refuted. Also recorded: the
  family-infra spec relocation to NFR MERGED this day.

---

## Appendix — Downstream (PARKED, so we don't re-derive it)

Earlier in the 2026-06-16 session we worked the *downstream* (kickoff /
prioritize / drain) before the user redirected to the front-end. Captured
here so it isn't lost, but **out of scope for this doc's active work:**
- Fabro is the **execution** layer (workflow-as-DOT-graph; Runs board
  `Working → Pending → Verify → Merge`; queues + executes runs continuously;
  layered verify gates → fix loops). It prescribes *nothing* about breakdown
  or prioritization — that's the upstream layer this doc is about. (Round 2
  confirmed this directly: Fabro "assumes the human has already decomposed
  work into agent-feedable tasks.")
- The family already has the downstream layers: Beads Ledger (priority, deps,
  ready), the Dispatcher (`mode`/`budget`, janitor `just check` + doctor hard-
  gate, iteration journal), `next` (deterministic ranking), doctor (cross-repo
  check).
- The central downstream risk is the **"piling problem"** (agents outpace the
  verify/merge stage). Defense = **pull-based draining** (concurrency cap +
  budget + merge backpressure) + **tiered autonomy** (auto-merge on green
  gate; escalate-don't-drop on repeated-fail / conflict / governance-flag).
  These are deterministic Dispatcher *policy*, not a skill. Revisit after the
  breakdown step is settled.
