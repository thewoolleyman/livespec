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

## Synthesis for livespec (where we land so far — tentative)

The wider field splits into two schools that livespec is *uniquely both* of:

| School | Unit of work | Where human judgment goes | Exemplar |
|---|---|---|---|
| **A — Spec-hierarchy-as-source** | a vertical slice / scenario of the spec | authoring + curating spec + scenarios + acceptance | StrongDM, Spec-Kit |
| **B — Dependency-graph-issue** | a dependency-linked work-item | the decomposition + the dependency links | Beads |

livespec already *has both*: `SPECIFICATION/` (+ `scenarios.md`, `propose-change`/`revise`) is School A; the Beads/Dolt ledger is School B. The
two compose cleanly — **the spec/scenario layer supplies the cut-line and the
acceptance; the Beads layer supplies the unit, the dependency links, and
mechanical readiness.** That composition is the spine of the direction below.

### Emerging design direction (tentative — needs the workstreams below)

- **Unit = a vertical slice anchored to ONE scenario.** Cut test: *"is there a
  single scenario (acceptance statement) this slice satisfies, autonomously
  verifiable by `just check` + `/livespec:doctor` (+ that scenario)?"* One →
  it's a chunk. Needs several independent ones → split.
- **Agent-DRAFTS the breakdown, human OWNS the cut.** Mirrors Devin's planner
  and Spec-Kit's `/tasks`: an aid proposes slices + dependency links +
  acceptance from a spec change / gap / epic; the maintainer edits and
  approves. The expensive blank-page scoping is offloaded; the *judgment*
  (where to cut, what "done" means) stays human.
- **Dependency-layer at breakdown time** so Layer-0 slices dispatch
  immediately and same-layer slices parallelize. (Beads already supports the
  graph + `bd ready`.)
- **Definition of Ready = deps-closed (mechanical) AND a stated
  acceptance/scenario AND governance scope (which repos/files; auto vs.
  human-gated).** Never deps-closed alone — the research is explicit that
  readiness ≠ verifiability.
- **Re-decomposition trigger = the agent fails to converge.** Devin re-plans
  per session; StrongDM iterates the spec until scenarios pass. Non-
  convergence *is the signal* the slice was too big — it's the grooming
  feedback loop, and it should route back to a human grooming pass, not an
  infinite retry.

### The "should we have a skill?" question — position has EVOLVED

Initial take (pre-research): *probably no skill — kickoff/prioritize/drain
are deterministic orchestrator concerns; codify policy, don't build a skill.*
That still holds for the **downstream** (parked below). But the research
**flipped the answer for the breakdown step**: the dominant, verified pattern
*is* an agent-assisted decomposition step the human steers (Devin's planner,
Spec-Kit `/tasks`). So a **lightweight grooming/decompose aid that DRAFTS a
slice-and-dependency breakdown for the maintainer to edit and approve** is now
well-justified — provided it *drafts* and the human *owns the cut and the
acceptance*. Open: whether this is a new `/livespec-impl-beads:groom` (or
`:decompose`) skill, or a Definition-of-Ready checklist folded into the
existing `capture-work-item` / `capture-impl-gaps`. Decide in Workstream B.

---

## Open workstreams (the user asked to pursue ALL of these)

### Workstream A — Our cut-line heuristic
Adopt and pressure-test **"one independently-testable scenario = one slice."**
Concretely test it against a real recent epic: *how should `livespec-gy21`
(the project-scoping epic just completed) have been sliced under this rule?*
Does "one scenario per slice" actually produce the right grain for our work,
or do spec-change / cross-repo-bump / refactor work-item types need their own
cut-lines? Output: a written cut-line heuristic with worked examples.

### Workstream B — The agent-assisted grooming ritual
Design what the draft-decompose aid proposes and where the approval gate
sits. Decide: capture-time quick-slice vs. a dedicated grooming pass (both
exist — when each?). Decide skill-vs-checklist (per the evolved position
above). Define the fields the aid must fill per slice: scope, the one
scenario/acceptance, dependency links, governance scope, repo target.
Mind the family rule: cross-repo coordination lives in the livespec layer;
impl plugins round-trip labels (see
[[feedback_no_cross_repo_leak_into_impl]] in maintainer memory).

### Workstream C — Invent + instrument our own sizing
Since the field has NO numeric sizing rules, pick *provisional* limits
(e.g., files touched, # of independent scenarios, dependency fan-out) and
**let convergence/non-convergence data calibrate them.** The honest move is
to instrument first: capture, per Fabro run, whether the slice converged,
how many fix-loops, wall-clock/cost, then correlate with slice "size" proxies
to discover *our* cut-points empirically rather than guess them. Ties to the
operability telemetry already designed in `preconditions.md` (the journal →
Honeycomb leg).

---

## Open questions / unknowns (carry forward)

1. **Quantitative sizing** — what numeric proxies actually predict "agent-
   one-shottable" *for our work* (mostly spec-governed Python + cross-repo
   config)? Unsolved in the field; Workstream C is our path to an answer.
2. **Capture vs. grooming trigger rituals** — who/what triggers re-
   decomposition? Tentative: non-convergence routes to a human grooming
   pass. Needs a concrete state model in the ledger (a `needs-regroom`
   state?).
3. **Does "satisfaction" (probabilistic LLM-judge acceptance) generalize**
   beyond StrongDM's agentic-software domain to our mostly-deterministic
   spec-governed code? Or is `just check` + `/livespec:doctor` + one scenario
   already our sufficient, deterministic acceptance? Lean: deterministic-first
   is fine for us; satisfaction is a fallback for genuinely agentic slices.
4. **Targeted follow-up research** on the named-but-absent shops (Stripe
   minions, Cursor, Factory.ai, Fabro's own workflow patterns, Remy) — they
   may have breakdown rituals this pass couldn't confirm.
5. **How does spec decomposition (propose-change → revise producing scenarios)
   hand off to impl decomposition (Beads slices)?** The seam between School A
   and School B in *our* stack is under-specified.

---

## Decision log

- **2026-06-16** — Scope locked to the *human front-end breakdown* step;
  downstream prioritize/drain explicitly parked (appendix). (User direction.)
- **2026-06-16** — Tentative direction: unit = vertical slice anchored to one
  scenario; agent-drafts/human-approves; dependency-layer for parallelism;
  DoR = deps + acceptance + governance; re-decomposition on non-convergence.
  **NOT ratified** — pending Workstreams A/B/C.
- **2026-06-16** — "Skill?" answer evolved: a *drafting* grooming aid is
  justified for breakdown (was "probably not"); downstream stays policy, not
  skill. Skill-vs-checklist deferred to Workstream B.

---

## Appendix — Downstream (PARKED, so we don't re-derive it)

Earlier in the 2026-06-16 session we worked the *downstream* (kickoff /
prioritize / drain) before the user redirected to the front-end. Captured
here so it isn't lost, but **out of scope for this doc's active work:**
- Fabro is the **execution** layer (workflow-as-DOT-graph; Runs board
  `Working → Pending → Verify → Merge`; queues + executes runs continuously;
  layered verify gates → fix loops). It prescribes *nothing* about breakdown
  or prioritization — that's the upstream layer this doc is about.
- The family already has the downstream layers: Beads ledger (priority, deps,
  ready), the Dispatcher (`mode`/`budget`, janitor `just check` + doctor hard-
  gate, iteration journal), `next` (deterministic ranking), doctor (cross-repo
  check).
- The central downstream risk is the **"piling problem"** (agents outpace the
  verify/merge stage). Defense = **pull-based draining** (concurrency cap +
  budget + merge backpressure) + **tiered autonomy** (auto-merge on green
  gate; escalate-don't-drop on repeated-fail / conflict / governance-flag).
  These are deterministic Dispatcher *policy*, not a skill. Revisit after the
  breakdown step is settled.
