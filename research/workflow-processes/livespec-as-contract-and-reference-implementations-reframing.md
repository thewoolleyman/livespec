# LiveSpec as a contract with reference implementations -- reframing

**Status:** decisions recorded 2026-06-09 (see §8 "Decision record" at the
bottom); formalization in flight via
`SPECIFICATION/proposed_changes/contract-and-reference-implementations-phase-1.md`
(pre-formal research capture per the `research/workflow-processes/CLAUDE.md`
graduation rule -- the load-bearing rules land in `SPECIFICATION/` at revise).

**Date:** 2026-06-08 (decision record appended 2026-06-09).

**Authored from:** branch `master`, multi-session design discussion (tool
evaluation + terminology audit).

**Follows up:**
`research/workflow-processes/livespec-as-contract-and-reference-implementations.md`
(the "contract + reference implementations" re-steering). This doc does not
replace it; it sharpens two things that doc left coarse: the internal shape
of the orchestrator axis, and the names.

**Addresses:**
`SPECIFICATION/proposed_changes/recast-layer3-standalone-orchestrate-plugin.md`
(see Section 6).

> One-line thesis: the orchestrator axis is not one unit. It is a **Ledger**
> (work-item store + dependency graph) and a **Loop** (the producer),
> coupled by a **Dispatcher** -- and the thin agent wrapper currently called
> a "harness" must be renamed, because "harness" now means something specific
> and almost opposite in the wider literature.

---

## 1. Summary of decisions

1. **The orchestrator is internally two things, not one.** A work-item store
   plus dependency graph (the **Ledger**), and a per-work-item production
   loop (the **Loop**), joined by a **Dispatcher** that polls the Ledger and
   fans work out to the Loop. The prior doc's single "orchestrator" framing
   and its flat reference cohort `livespec-impl-{git-jsonl, gascity, kilroy}`
   conflate these -- those three are not peers (one is a store substrate, one
   is a loop engine, one is a whole fleet).

2. **This stays an internal decomposition, NOT a new axis in core's
   contract.** Core still sees exactly the three orchestrator CLIs
   (spec-reader, gap-capture, drift-capture). Work-items, the `depends_on`
   graph, and cross-repo resolution remain orchestrator-private, exactly as
   the prior doc's "item 0" already moved them. The Ledger/Loop boundary is
   wired inside the orchestrator repo's own config, never in `.livespec.jsonc`.

3. **git-jsonl is disqualified for parallel workloads.** Not for
   dependency-graph reasons -- because a JSONL ledger is a single shared
   mutable file, and git's unit of concurrency is the commit, not the row. N
   concurrent producers serialize on that file and generate merge conflicts.
   This was hit independently in LiveSpec development and is the same wall
   Steve Yegge hit, which is why Beads evolved onto Dolt (see Section 3).

4. **The viable parallel-capable assembly is Beads/Dolt (Ledger) + Fabro
   (Loop).** Full Gas City alongside Fabro is mostly redundant or competing:
   both are orchestrators that want to own the loop. The piece of the Gas City
   stack worth taking is its bottom two layers -- Beads on Dolt -- as the
   concurrent-safe Ledger. The fleet apparatus above it (pools, health patrol,
   packs, reconciliation, Sling) is surplus to the LiveSpec orchestrator
   contract, which needs a producer per work-item, not a standing agent city.

5. **"Harness" must be renamed.** The thin, agent-specific wrapper around
   core's CLIs (the Claude Code / Codex / Pi binding) collides head-on with
   the now-established meaning of "harness" (Birgitta Böckeler: everything in
   an agent except the model -- the guides-and-sensors governor). Recommended
   replacement: **Driver** (device-driver analogy; the prior doc's own
   PlantUML already labels it "interactive driver"). Alternates: **Adapter**,
   **Binding**.

6. **Bonus alignment.** Freeing up "harness" lets LiveSpec use it correctly:
   the spec is a feedforward guide, holdout scenarios are a feedback sensor,
   and gap/drift are the cybernetic governor. In Böckeler's vocabulary
   LiveSpec is a **behaviour-harness authoring-and-regulation system** (see
   Section 5.3).

---

## 2. The orchestrator is not one unit

### 2.1 The conflation

The prior doc names one orchestrator axis and lists
`livespec-impl-{git-jsonl, gascity, kilroy}` as its reference cohort. Those
are at three different layers:

- **git-jsonl** -- a *store substrate* (where work-items live).
- **kilroy** -- a *loop engine* (what consumes a work-item and produces code;
  a Go implementation of StrongDM's Attractor pattern).
- **gascity** -- a *fleet* that bundles a store (Beads/Dolt), a
  dispatch/patrol layer, and more.

Listing them as peers hides the real structure. A working orchestrator is a
**product of two axes**: a store crossed with a loop. The Beads/Dolt + Fabro
assembly this discussion converged on is exactly such a product -- not a
fourth item on the flat list.

### 2.2 The internal decomposition

The orchestrator decomposes into three internal roles:

| Role           | Responsibility                                                                                  | Reference fills              |
| -------------- | ----------------------------------------------------------------------------------------------- | ---------------------------- |
| **Ledger**     | Work-item store + `depends_on` graph; the authoritative, concurrent-write system of record.     | Beads/Dolt; git-jsonl        |
| **Loop**       | Consumes a ready work-item, runs its build/verify graph, emits the implementation artifact.     | Fabro; Kilroy (Attractor)    |
| **Dispatcher** | Polls the Ledger for ready work, invokes the Loop, writes status/results back. Owns parallelism. | Gas City's Sling; a script   |

Two properties matter:

- **Core's contract does not grow.** The orchestrator's public face is still
  the three CLIs. The Ledger is *behind* `gap-capture` (which writes to it);
  the Loop is *behind* the production pipeline; `spec-reader` is orthogonal.
  Core never talks to the Ledger directly, so it stays agnostic to whether
  the store is Dolt, JSONL, or anything else. "Item 0" holds unchanged.

- **The two halves swap independently.** Keep Beads, swap Fabro for Kilroy;
  or keep Fabro, swap Beads for JSONL. That independence is the whole reason
  to name them separately.

### 2.3 Mapping the three CLIs onto the decomposition

- `spec-reader` -- reads the spec by category; orthogonal to Ledger/Loop, but
  injected into gap-capture and drift-capture as today.
- `gap-capture` -- writes gaps into the **Ledger** (e.g. `bd create`).
- `drift-capture` -- routes drift to `propose-change` (spec-side); reads via
  `spec-reader`. Unchanged.
- The **Loop** consumes ready Ledger items and emits the implementation.
- The **Dispatcher** is the runtime that makes it move and is where the
  parallel-write pressure on the Ledger originates.

---

## 3. Substrate decision: git-jsonl does not scale for parallel work

The disqualifier is mechanical, not preferential. A JSONL ledger is a single
shared mutable file. Git's unit of concurrency is the commit, not the row, so
N producers appending and committing concurrently serialize on that file and
collide on merge. Dependency-graph richness is a separate question; even a
perfect dependency model on JSONL still hits this wall under parallelism.

This was encountered independently during LiveSpec development, and it is the
same constraint that drove Steve Yegge to put Beads on Dolt rather than flat
files. Beads' own design makes the motivation explicit: it is Dolt-powered
(a version-controlled SQL database with cell-level merge and native
branching) and uses hash-based issue IDs specifically so that multiple agents
creating issues simultaneously do not produce merge collisions. A real
database gives row-level transactional writes and structural merge; a shared
append file gives neither.

**Store separation that falls out of this.** Put the *mutable shared ledger*
in Dolt (work-items -- where parallelism bites) and leave *code artifacts* in
git (Fabro's per-stage branch checkpoints -- where branch-per-run is already
correct and git handles concurrency fine). The contention problem is specific
to the shared ledger; solve it where it lives and leave the Loop's git
checkpointing alone.

---

## 4. The viable assembly, and what Gas City adds (little)

If Fabro is the Loop, the value-add of *full* Gas City is mostly redundant or
competing:

- Gas City is itself an orchestrator whose propulsion model is "if you find
  work on your hook, you run it" -- a standing agent claims a bead and runs
  it. Fabro wants to be the thing that runs it. Run both and you must pick
  which one is the loop; the loser is dead weight.
- Gas City's Event Bus duplicates Fabro's run events / retros; its Formulas
  and Molecules duplicate Fabro's DOT phase graphs; its sandbox/provider story
  duplicates Fabro's cloud sandboxes.
- Its fleet apparatus (pools, health patrol, packs, declarative
  reconciliation) is surplus to the LiveSpec orchestrator contract, which
  requires a producer per work-item, not a long-lived multi-agent city.

What *does* pay for itself is the bottom of the Gas City stack: **Beads on
Dolt** as the concurrent-safe Ledger. That fills exactly the work-item +
dependency hole Fabro leaves (Fabro has no backlog, ledger, or dependency
graph -- it takes a goal and runs a graph). Beads natively models the
`depends_on` graph the LiveSpec orchestrator must own privately.

Net: the "store choice" is really **git-jsonl vs Beads/Dolt**, with Fabro as
the Loop either way; parallelism forces Beads/Dolt. Full Gas City only earns
its place if a standing fleet is actually wanted, in which case it *replaces*
Fabro rather than complementing it (and you lose Fabro's stronger
model-routing, verification-gate, and checkpoint story).

---

## 5. Terminology reframing

### 5.1 "Harness" -> Driver

Böckeler's "Harness engineering for coding agent users" establishes "harness"
to mean everything in an agent except the model itself -- the system of
**guides** (feedforward controls that steer before the agent acts) and
**sensors** (feedback controls that observe after and help it self-correct),
acting together as a cybernetic governor that regulates the codebase toward
its desired state.

LiveSpec's current "harness" is the opposite kind of thing: a thin,
agent-specific wrapper that binds core's generic CLIs and harness-neutral
prose to one tool runtime's tool-calling. Keeping the word guarantees
confusion with the wider meaning.

**Recommendation: Driver.** The device-driver analogy is exact and instantly
legible: core is the OS exposing generic syscalls (the spec-side CLIs); each
agent runtime (Claude Code, Codex, Pi) is different hardware; the Driver
adapts the generic calls to that runtime. It explains why the component is
thin and why there is one per agent. It is also already LiveSpec's own word --
the prior doc's PlantUML labels the component `interactive driver`.

Alternates, both grounded in the prior doc's own text:

- **Adapter** -- the formal pattern name; neutral, unambiguous.
- **Binding** -- the prior doc already says the harness contains "the
  harness-specific binding of that prose to a tool runtime."

Repo naming would shift `livespec-harness-{claude,codex,opencode,pi}` to
`livespec-driver-{...}` (or `-adapter-` / `-binding-`).

### 5.2 Names for the orchestrator internals

- **Ledger** (recommended) for the store + dependency graph. It is the
  authoritative, ordered, queryable record of work units and their
  relationships, contrasts cleanly with the execution side, and is already
  the word this ecosystem uses (Beads describes itself as "the ledger").
  Conservative alternate: **Registry**. Avoid **work graph** -- "graph"
  collides with Fabro's DOT phase graphs on the Loop side.
- **Loop** for the producer. Keep the descriptive **production loop** (already
  in the prior doc), or adopt **Mill** if a crisp noun is wanted to pair
  against Ledger (Ledger records, Mill produces). Reference fills are
  Attractor-class engines (Fabro, Kilroy).
- **Dispatcher** for the coupling (Gas City's Sling is one implementation; a
  thin polling script is another). This is where parallelism -- and therefore
  the pressure on the Ledger -- lives.

The two genuine coin-flips are *Mill vs production-loop* and *Driver vs
Adapter*; the rest are held firm.

### 5.3 Böckeler alignment (the bonus)

Once "harness" is freed, LiveSpec's own components map cleanly onto
Böckeler's cybernetic framing, which both validates the Section 2 split and
gives LiveSpec a grounded vocabulary:

- The **spec** (intent + contracts + constraints) is a **feedforward guide**.
- **Holdout scenarios** are a **feedback sensor**.
- The **implementation** is the regulated system.
- **gap** is feedforward correction of the artifact; **drift** is feedback
  correction of the spec. Together they are the **governor**.

In Böckeler's terms, LiveSpec is a *behaviour-harness authoring-and-regulation
system*. "Harness" should be reserved for that meaning -- never for the thin
agent wrapper, which is the Driver.

### 5.4 Consolidated naming table

| Old / current term                         | New term            | What it is                                                        |
| ------------------------------------------- | ------------------- | ----------------------------------------------------------------- |
| harness (`livespec-harness-*`)              | **Driver**          | Thin agent-specific wrapper binding core CLIs to a tool runtime   |
| orchestrator (as one unit)                  | **Ledger + Loop + Dispatcher** | Internal decomposition of the orchestrator axis        |
| (implicit store half)                       | **Ledger**          | Work-item store + `depends_on` graph; concurrent-write record     |
| production loop                             | **Loop** / **Mill** | Per-work-item producer of the implementation artifact             |
| (implicit coupling)                         | **Dispatcher**      | Polls Ledger, invokes Loop, writes back; owns parallelism         |
| "harness" (Böckeler sense)                  | reserved            | The spec+scenarios+gap/drift governor -- what LiveSpec authors     |

---

## 6. Disposition of `recast-layer3-standalone-orchestrate-plugin.md`

That proposed-change recasts "Layer 3 -- Cross-repo orchestration" from a
livespec-resident skill into an optional, independently-distributed
orchestration **plugin** that composes Layer 2 `next` primitives across
spec-side and impl-side, dispatches the chosen action, runs the janitor as a
hard gate, emits an iteration journal, and loops until the queue drains or a
budget is exhausted. It also makes the cross-plugin contract support an
external orchestrator (dispatchable `action` verbs; `--project-root` on the
query skills).

Under the contract + reference-implementations model, split it:

**Survives, and is strengthened.** The load-bearing invariant -- *the
orchestrator depends only on the published contract surface, MUST NOT read
impl-side stores directly, and derives dispatch from published output* -- is
exactly the new model's discipline. It becomes the three-CLI boundary plus
orchestrator-private work-items. The `--project-root` addressability and the
"`action` is a dispatchable verb in the emitting plugin's surface" property
carry forward intact; they are how a Dispatcher addresses Ledger state across
repos without reaching into a store format.

**Retired.** The "Layer 3 standalone plugin" framing, and the three-layer
(CLI / skill / loop) architecture it lives in, are overtaken. The prior doc
already retired "layer": the loop moved *into* the orchestrator, so there is
no Layer 3 to be resident-or-plugin about, and no standalone "orchestrate
plugin" to distribute. The livespec-resident-vs-plugin distribution debate
dissolves with it.

**Relocates.** The recast PC's loop *discipline* -- mode parameter, budget
parameter, janitor-as-hard-gate, structured iteration journal,
config-supplied janitor/branch/manifest/isolation -- does not disappear. It
becomes the **Dispatcher's** specification inside the orchestrator repo. The
"unified cross-side ranking" partly dissolves: impl-side "what to run next"
is Dispatcher-private over the Ledger; spec-side "next" stays in core's spec
lifecycle; the spec<->impl adjudication is already handled by gap (impl
correction) and drift (proposed-change, human-accepted).

This matches the prior doc's Appendix A disposition of the same PC ("REFRAME /
likely supersede: its core move -- orchestrator consumes only the published
surface -- is right and survives; fold the valid parts into Phase 1, retire
the rest"). Recommended concrete action: when Phase 1 specs the new contract,
fold the surviving invariant and the relocated Dispatcher discipline in, and
formally reject the Layer-3-plugin framing rather than revising it into a
model that no longer has layers.

---

## 7. Deltas to fold into the migration plan

- **Phase 1 (spec the contract):** state the orchestrator's internal
  Ledger / Loop / Dispatcher decomposition as guidance, while keeping core's
  contract at the three CLIs. Record that the store substrate is
  orchestrator-private and that JSONL is unsuitable for parallel producers.
- **Phase 3 (extract harness):** rename harness -> Driver (or Adapter /
  Binding) before extraction, to avoid baptizing repos with the colliding
  term. `livespec-driver-claude` first.
- **Phase 4 (default orchestrator):** the default's substrate decision is now
  explicit -- git-jsonl remains acceptable only for serial use; the
  parallel-capable reference assembly is Beads/Dolt (Ledger) + Fabro (Loop)
  with a thin Dispatcher.
- **Phase 5 (prove both axes swap):** the orchestrator axis is itself a
  product of two sub-axes; a genuine pluggability proof should swap the Loop
  (Fabro <-> Kilroy) and the Ledger (Beads/Dolt <-> git-jsonl) independently.
- **Open question carried forward:** the interactive gap/drift dialogue
  ownership (Driver vs orchestrator CLI) from the prior doc is unchanged by
  this reframing and still needs a worked example.

---

## References

Canonical links for everything referenced in this discussion.

**LiveSpec (this repo)**

- Prior doc being followed up:
  `research/workflow-processes/livespec-as-contract-and-reference-implementations.md`
  -- <https://github.com/thewoolleyman/livespec/blob/master/research/workflow-processes/livespec-as-contract-and-reference-implementations.md>
- Proposed-change addressed in Section 6:
  `SPECIFICATION/proposed_changes/recast-layer3-standalone-orchestrate-plugin.md`

**Loop engines (Attractor-class)**

- Fabro -- <https://github.com/fabro-sh/fabro> ; docs <https://docs.fabro.sh>
- Kilroy (Dan Shapiro, Go implementation of Attractor) --
  <https://github.com/danshapiro/kilroy>
- Kilroy fork used in the author's factory work --
  <https://github.com/thewoolleyman/kilroy>
- StrongDM Attractor (the NLSpec) -- <https://github.com/strongdm/attractor>
- StrongDM Software Factory -- <https://factory.strongdm.ai> ; Attractor
  product page <https://factory.strongdm.ai/products/attractor>

**Ledger / store substrate**

- Beads (Steve Yegge) -- <https://github.com/steveyegge/beads>
- Beads introduction (Yegge, on the "agent memory" motivation) --
  <https://steve-yegge.medium.com/introducing-beads-a-coding-agent-memory-system-637d7d92514a>
- Dolt (DoltHub / Tim Sehn -- SQL database with git semantics) --
  <https://github.com/dolthub/dolt> ; <https://www.dolthub.com>

**Fleet orchestration**

- Gas City -- <https://github.com/gastownhall/gascity>
- Gas Town (Steve Yegge -- the reference orchestrator Gas City was extracted
  from) -- <https://github.com/steveyegge/gastown>

**Harness engineering / terminology**

- Birgitta Böckeler, "Harness engineering for coding agent users"
  (martinfowler.com) --
  <https://martinfowler.com/articles/harness-engineering.html>
- LangChain, "The anatomy of an agent harness" (the Agent = Model + Harness
  framing) -- <https://blog.langchain.com/the-anatomy-of-an-agent-harness/>
- Anthropic, "Effective harnesses for long-running agents" --
  <https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents>
- Ashby's Law of Requisite Variety --
  <https://en.wikipedia.org/wiki/Variety_(cybernetics)#Law_of_requisite_variety>
- Cybernetics -- <https://en.wikipedia.org/wiki/Cybernetics>

**Author's companion work**

- The Software Factory: A Practitioner's Guide to Specification-Driven
  Development for Enterprise Services --
  <https://github.com/thewoolleyman/software-factory-practitioners-guide>

---

## 8. Decision record (2026-06-09)

All open naming/architecture calls from this doc and the prior doc were
decided by the user on 2026-06-09. The normative home for these decisions is
`SPECIFICATION/proposed_changes/contract-and-reference-implementations-phase-1.md`
(pending `/livespec:revise`); this section records them in the research trail.

1. **Driver** is the name of the thin agent-runtime wrapper (over Adapter /
   Binding). Repos: `livespec-driver-{claude,codex,...}`.
2. **Loop** is the producer noun (over Mill); "production loop" remains
   acceptable long-form prose.
3. **Pin-and-bump relocates**: the `compat` schema + bump policy move to the
   family/dev-tooling coordination surface; the
   `contract-version-compatibility` doctor invariant is dropped from core.
4. **`cross_repo_targets` splits** and leaves core's config contract:
   work-item-resolution use -> orchestrator-private; release-coordination
   use -> family-coordination surface.
5. **Recast PC**: formally REJECTED at revise; the Phase-1 propose-change is
   the named successor for its surviving content (Section 6's split holds).
6. **Append-only-store PC**: formally REJECTED at revise; its content
   migrates to the git-jsonl orchestrator's own SPECIFICATION (Phase 4).
7. **Interactive gap/drift dialogue is orchestrator-owned** (Section 7's
   carried-forward open question, now closed): each orchestrator ships its
   own standard SKILL.md front-ends in-repo, usable from the supported agent
   runtimes (Claude Code / Codex CLI / Pi); publication as per-orchestrator
   installable plugins is deferred future work. The Driver <-> orchestrator
   zero-dependency invariant is preserved.

**Reference orchestrator cohort (decided the same session):** exactly two
orchestrators are current work -- **git-jsonl** (serial; the existing
homegrown orchestration logic; optionally human-driven directly via a coding
agent runtime) and **Beads/Dolt + Fabro** (parallel-capable; the assembly the
livespec family dogfoods for ALL internal repos). Gas City fleets and Kilroy
remain possible future alternates, not commitments.

**Canonical diagram:** the decided architecture is captured at
`diagrams/contract-and-reference-implementations.plantuml` (+ rendered
`.svg`), superseding `diagrams/orchestration-layers.*` as the architecture
picture of record; the Phase-1 propose-change requires the spec to reference
it and the repo README to link the rendered form.

*Update (v105):* the canonical diagram moved to the repo README as an
embedded fenced Mermaid block; the `.plantuml`/`.svg` pair above was removed.
