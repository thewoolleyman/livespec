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
unchanged. The **2026-06-19 reframe** (next major section) **supersedes the
earlier synthesis** wherever they conflict, and the **slice cut-line**, the
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
thought matters more than speed here.

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

### Primary sources (for future re-reading)
- Devin 2.0 Interactive Planning — cognition.ai/blog/devin-2, docs.devin.ai
- GitHub Spec-Kit — github.com/github/spec-kit (v0.10.3, Jun 2026)
- Beads — github.com/steveyegge/beads/blob/main/docs/DEPENDENCIES.md
- StrongDM Software Factory — factory.strongdm.ai (+ simonwillison.net first-hand, Feb 2026)
- Fabro (execution layer, for context) — github.com/fabro-sh/fabro, docs.fabro.sh

---

## The 2026-06-19 reframe (supersedes the earlier synthesis)

The prior sessions kept snagging on cross-repo. This session's unlock:
**cross-repo is a category error for this design.** Strip it out and the
general pattern becomes clean.

### Dependency note — a spec relocation this reasoning leans on

A separate session is landing a `/livespec:critique` → `/livespec:revise`
pass on branch `spec/relocate-family-infra-to-nfr` that **moves livespec's
own family-infrastructure sections out of the *functional*
`SPECIFICATION/contracts.md` and into `non-functional-requirements.md`**
(the five sections: Cross-repo coordination — pin-and-bump; Shared content
sync — copier template; Shared code sync — livespec-dev-tooling; Shared
runtime — livespec-runtime; Sibling spec ownership). The doctor check
`wiring-completeness-cross-repo` is *promoted* to a standalone entry under
contracts.md §"Doctor cross-boundary invariants" (the doctor *mechanism*
stays functional; the family roster it reads moves to NFR). A root-cause
rule was codified in NFR §"Boundary": functional files describe only what
*any* livespec consumer inherits; livespec's own family infrastructure is
self-application and lives in NFR.

**Status as of 2026-06-19: NOT yet merged** — the five sections are still
`##` headings in `contracts.md`. The boundary below holds *conceptually*
either way; this doc just describes NFR as grooming guidance's home without
claiming the physical relocation has landed.

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

### The grooming ritual — how the split gets drafted + approved — *structure set, details open*

- **Two touchpoints, gated by a size test (both matter, not competitors):**
  1. **Intake cut at work-item creation** — a cheap readiness check: *is
     this already one actionable slice (one coherent "done", deps known)?* If
     yes → ready. If no → mark not-yet-actionable. The frictionless common
     case.
  2. **Regroom pass (optional, later)** — the heavier draft-decompose that
     actually splits the not-yet-actionable items (epics / too-big) into
     slices. This is the verified "agent drafts, human approves" pattern
     (Devin planner / Spec-Kit `/tasks`).
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
- **The earlier cross-repo fork is DISSOLVED.** The old "where does
  cross-repo grooming live — impl-layer vs livespec-layer?" question
  evaporates: grooming is orchestrator-internal; core only ever *checks*
  cross-repo consistency (structural doctor invariants) and *defines the
  scenario concept*.
- **STILL OPEN:** the groom front-end's exact draft output; the intake
  checklist's precise gates; final confirmation of the home (non-functional
  core guidance + reference-orchestrator-spec realization).

### Slice-size calibration — discovering the limits from real run data — *approach set, design open*

- The field has **no quantitative agent-sizing rules** (all refuted as
  folklore). The honest move is to **invent + instrument**: pick provisional
  limits, instrument Fabro runs (converged? fix-loop count? wall-clock /
  cost), and correlate with slice-size proxies to discover *our* cut-points
  empirically rather than guess them. Ties to the journal → Honeycomb leg
  already designed in `preconditions.md`.
- **Now also calibrate a FLOOR** (minimum viable slice), not just a ceiling
  — driven by the cut-line's over-split finding.
- **Re-decomposition trigger = the agent fails to converge.** Devin re-plans
  per session; StrongDM iterates the spec until scenarios pass.
  Non-convergence *is the signal* the slice was too big — it routes back to a
  human grooming pass (the regroom step above), not an infinite retry.
- **STILL OPEN:** the concrete Fabro-run instrumentation and the chosen
  slice-size proxies (ceiling AND floor).

---

## Open questions / unknowns (carry forward)

1. **Quantitative sizing** — what numeric proxies actually predict
   "agent-one-shottable" *for our work* (mostly spec-governed Python +
   cross-repo config)? Unsolved in the field; slice-size calibration is our
   path to an answer — and it now must yield both a ceiling and a floor.
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
4. **Targeted follow-up research** on the named-but-absent shops (Stripe
   minions, Cursor, Factory.ai, Fabro's own workflow patterns, Remy, Dan
   Shapiro's "five levels") — they may have breakdown rituals this pass
   couldn't confirm. Use the `deep-research` skill if pursued.
5. **The School-A → School-B handoff seam.** How does spec decomposition
   (propose-change → revise producing scenarios) hand off to impl
   decomposition (orchestrator Ledger slices)? In the reframe this is the
   functional/non-functional seam: the functional scenario concept supplies
   the cut-line; the orchestrator's Ledger consumes it. Under-specified — the
   exact handoff mechanics are the grooming ritual's remaining work.

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

---

## Appendix — Downstream (PARKED, so we don't re-derive it)

Earlier in the 2026-06-16 session we worked the *downstream* (kickoff /
prioritize / drain) before the user redirected to the front-end. Captured
here so it isn't lost, but **out of scope for this doc's active work:**
- Fabro is the **execution** layer (workflow-as-DOT-graph; Runs board
  `Working → Pending → Verify → Merge`; queues + executes runs continuously;
  layered verify gates → fix loops). It prescribes *nothing* about breakdown
  or prioritization — that's the upstream layer this doc is about.
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
