---
topic: contract-and-reference-implementations-phase-1
author: claude-fable-5
created_at: 2026-06-09T20:26:29Z
---

Phase 1 of the "LiveSpec as a contract + reference implementations"
re-steering: rebuild the cross-boundary contract as a CLI surface wired
by `.livespec.jsonc`, making livespec-core agnostic to BOTH the agent
runtime that drives it interactively AND the orchestrator that produces
the implementation. This is the load-bearing spec change of the
migration; Phases 2–6 (building the reference CLIs, extracting the
Claude binding, rebuilding the default orchestrator, proving the axes
swap, codifying the diagrams) realize it and are deliberately OUT of
scope here.

Authoritative sources (pre-formal research captures, per
`research/workflow-processes/CLAUDE.md` graduation rule):

- `research/workflow-processes/livespec-as-contract-and-reference-implementations.md`
  (2026-06-02 — the re-steering: CLI contract, two-flow spine, doctor
  shrink, "item 0" config relocations, phased migration plan).
- `research/workflow-processes/livespec-as-contract-and-reference-implementations-reframing.md`
  (2026-06-08 — the sharpening: Ledger/Loop/Dispatcher decomposition
  stays orchestrator-internal; git-jsonl disqualified for parallel
  producers; "harness" → Driver rename; disposition of the recast
  Layer-3 propose-change).

**RESERVED DECISIONS.** Seven naming/architecture calls are reserved
for the user and are NOT decided by this draft. Where the draft needs a
word it uses the research docs' leaning as a working name, marked
`[RESERVED #N]`: #1 Driver-vs-Adapter-vs-Binding (working name:
**Driver**); #2 Loop-noun Mill-vs-production-loop (working name:
**Loop**); #3 pin-and-bump / `compat` home; #4 `cross_repo_targets`
split; #5 fate of the pending `recast-layer3-standalone-orchestrate-plugin`
propose-change (recommendation: formally REJECT at revise; its
surviving content is folded into this proposal); #6 fate of the pending
`append-only-store-legibility-and-merge-safe-reduction` propose-change
(recommendation: withdraw as orchestrator-private); #7 interactive
gap/drift dialogue ownership (Driver vs orchestrator CLI — needs a
worked example; this draft leaves it an explicit open question).

Relationship to the two OTHER pending proposed-changes: this proposal
folds the SURVIVING parts of `recast-layer3-standalone-orchestrate-plugin.md`
(the orchestrator-consumes-only-the-published-surface invariant, the
dispatchable-verb property, per-repo addressability) and relocates its
loop discipline to the orchestrator-internal Dispatcher guidance
(Proposal 5). It does NOT revise or absorb the append-only-store
proposal; that file's disposition is `[RESERVED #6]` and is exercised
at the same revise session that processes this file.

## Proposal: replace-three-layer-architecture-with-contract-plus-reference-implementations

### Target specification files

- SPECIFICATION/spec.md

### Summary

Replace §"Three-layer orchestration architecture" with a new
§"Contract + reference implementations architecture" that states the
re-steered model: LiveSpec is a contract plus reference implementations
at every seam. Core is agnostic to the **Driver** `[RESERVED #1]` (the
thin, agent-runtime-specific wrapper through which a human drives the
spec lifecycle interactively — Claude Code, Codex, OpenCode, Pi) and to
the **orchestrator** (the pluggable producer that consumes the spec and
produces the implementation). "Implementation" is recast from a peer
tier into the **work product** — the code, tests, config, and infra the
spec is *for*; the orchestrator is the producer, the implementation is
the artifact produced. The Layer 1/2/3 vocabulary is retired.

### Motivation

The current three-layer model conflates the product (implementation)
with the producer (orchestrator) and hard-couples both the contract
surface (skills) and the orchestration loop (the livespec-resident
Layer 3 driver) to one agent runtime (Claude Code). The re-steering
makes the contract a CLI surface any runtime can drive and any
orchestrator can consume, with reference implementations proving each
seam is real and swappable. There is no third tier: there is a spec
tier that exposes an API, and orchestrators that consume it; the
implementation is the output of the latter. "Layer" is retired because
the loop moves into the orchestrator and a "skill" decomposes into
(prose, in core) + (CLI, the contract), so there is no stack left to
layer.

### Proposed Changes

1. Remove §"Three-layer orchestration architecture" (all three layer
   bullets and the "Cross-side composition belongs at Layer 3"
   paragraph).
2. Add §"Contract + reference implementations architecture" stating:
   - **The thesis.** LiveSpec is a contract plus reference
     implementations. The core `livespec` library is agnostic to the
     Driver `[RESERVED #1]` and the orchestrator; the product is the
     contract plus reference implementations at each seam (reference
     spec-side CLIs, reference Driver bindings, reference
     orchestrators).
   - **Implementation is the work product.** Not a tier, not an actor:
     the code/tests/config/infra the spec is for. The orchestrator
     produces it.
   - **The two flows are the preserved spine.** A table codifying the
     asymmetric pair: **gap** (spec → implementation; corrects the
     IMPLEMENTATION; destination: a tracked work-item, owned by the
     orchestrator; method: mechanical / LLM / human — the
     orchestrator's private choice, usually LLM; human dependency
     optional) and **drift** (implementation → spec; corrects the
     SPEC; destination: a proposed-change, owned by the spec
     lifecycle; method usually needs a human; human dependency
     usually REQUIRED). Method is NOT a determinism distinction.
   - **Drift's human gate is load-bearing doctrine.** Only a human can
     rule "the implementation is right, the spec is wrong"; that is
     why drift lands as a proposed-change and never a direct spec
     write — the propose-change/revise gate IS the human adjudication
     mechanism, and it is the irreducible human touchpoint that
     survives even a fully autonomous orchestrator. Orchestrators MAY
     file drift (machine path); only humans accept it.
   - **Orchestrator internal decomposition (guidance, NOT contract).**
     A working orchestrator decomposes internally into a **Ledger**
     (work-item store + dependency graph; the authoritative
     concurrent-write system of record), a **Loop** `[RESERVED #2]`
     (the per-work-item producer that consumes a ready work-item and
     emits implementation artifacts), and a **Dispatcher** (polls the
     Ledger, invokes the Loop, writes results back; owns parallelism).
     This decomposition is stated as orchestrator-internal guidance
     only: core's contract sees exactly the three orchestrator CLIs of
     `contracts.md` §"Orchestrator CLI contract" and never names
     Ledger/Loop/Dispatcher in any config key or invariant. The two
     halves swap independently (keep the Ledger, swap the Loop;
     keep the Loop, swap the Ledger).
   - **Substrate guidance.** A shared-mutable-file JSONL ledger is
     unsuitable for PARALLEL producers (git's unit of concurrency is
     the commit, not the row; N concurrent producers serialize and
     collide on merge); it remains acceptable for serial use. A
     parallel-capable Ledger requires row-level concurrent writes and
     structural merge (e.g. Beads on Dolt). Code artifacts stay in git
     (branch-per-run is already correct there); the contention problem
     is specific to the shared ledger.
   - **Vocabulary.** "Layer 1/2/3" is retired. "Harness" is NOT used
     for the thin agent wrapper (it collides with the established
     wider meaning: everything in an agent except the model); the
     wrapper's name is `[RESERVED #1]`, working name Driver.
3. Update §"Terminology" and any other spec.md cross-references that
   name the three-layer architecture, "Layer 3", or the
   livespec-resident driver, to point at the new section. The
   `tests/heading-coverage.json` co-edit for the H2 rename rides in
   the revise payload per the Self-application discipline.

## Proposal: define-orchestrator-cli-contract-and-config-wiring

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Replace §"Implementation-plugin contract — the 10-skill surface" and
§"Thin-transport skill doctrine" with the new contract: a **CLI
surface** wired by `.livespec.jsonc`. Three orchestrator-side CLIs
(spec-reader, gap-capture, drift-capture) are NAMED in config and
otherwise behaviorally undefined; the spec-side CLIs (seed,
propose-change, revise, critique, doctor, prune-history) are
pre-populated with core's defaults and individually overridable. CLI
shape conventions replace the skill-namespace invocation doctrine.

### Motivation

"Skills" tie the contract to one agent runtime. A CLI is the common
interface every runtime and every orchestrator can drive; the Driver
`[RESERVED #1]` wraps it for interactive use. The 10-skill surface,
its work-item record schema obligations, and the skill-namespace
cross-plugin invocation rule are all artifacts of the
plugin-as-contract model this re-steering deletes. The surviving
invariant from the pending recast propose-change — the orchestrator
depends only on the published surface and never reads stores directly
— is strengthened here: LiveSpec never sees the orchestrator's store
at all.

### Proposed Changes

1. Remove §"Thin-transport skill doctrine" and
   §"Implementation-plugin contract — the 10-skill surface" (including
   the heavyweight/thin-transport skill catalogues, §"Cross-boundary
   handoffs", §"Impl-side cleanup invariants (cross-boundary)" — see
   Proposal 5 for where the cleanup concerns go —
   §"Backend-variability asymmetry", §"Work-item `spec_commitment_hint`
   field", and §"Persistent Agent Knowledge realization"; work-item
   record schemas are orchestrator-private per Proposal 4).
2. Add §"Orchestrator CLI contract — the three named CLIs": LiveSpec
   defines NONE of their behavior, only that they are named in
   `.livespec.jsonc` and callable:
   - **Spec-reader CLI** — reads the spec however it wants (plain
     reads, cached, indexed, embedded, RAG, …). Its API is undefined —
     the same orchestrator writes both the reader and everything that
     consumes it, so their shared interface is private. It MUST expose
     spec content **by template category** (spec / contracts /
     constraints / scenarios / …) so a consumer can tell what is a
     scenario: it **categorizes, never conceals** — holdout is the
     orchestrator's policy choice, not the contract's. (This
     supersedes §"Spec Reader required-capability surface"; see
     Proposal 4.)
   - **Gap-capture CLI** — a capture interface. Detects spec → impl
     gaps and writes them to whatever work-item mechanism the
     orchestrator has. The spec-reader CLI is injected as a reference.
     LiveSpec never sees the gaps or the store. Detection method is
     mechanical / LLM / human at the orchestrator's private choice —
     usually LLM (comparing a large prose spec to an implementation).
     This CORRECTS the current 10-skill surface's "no LLM in the
     detection path" clause for `detect-impl-gaps`, which is wrong for
     real semantic gap detection.
   - **Drift-capture CLI** — a capture interface. The spec-reader CLI
     and the propose-change CLI are injected. Routes impl → spec drift
     to propose-change. Filing is a machine path; acceptance is human
     (per the spec.md two-flow doctrine).
3. Add §"Spec-side CLI contract": seed / propose-change / revise /
   critique / doctor / prune-history are each named in
   `.livespec.jsonc`, pre-populated with core's reference defaults,
   and individually overridable — an alternate implementation is
   selected by overriding the name in config. `propose-change` is the
   one spec-side CLI injected into the orchestrator (into
   drift-capture). Doctor is NOT privileged: config-named and
   overridable like any other spec-side CLI.
4. Add §"CLI shape conventions": one binary per side with subcommands
   (NOT slash commands); `--json` everywhere with stable schemas,
   human text otherwise; stdin/stdout + files for payloads so any
   language can drive it; stable exit codes (the existing
   §"Lifecycle exit-code table" is reused unchanged); every CLI
   accepts explicit project-root addressing (carrying forward the
   `--project-root` property from the recast propose-change) so a
   consumer can address any repository's state through the named CLI
   rather than by reading anything directly.
5. Add the folded orchestrator-discipline invariant (the SURVIVOR of
   the pending recast propose-change): an orchestrator MUST depend
   only on the config-named CLI surface plus project configuration; it
   MUST NOT read spec-side internals beyond what the spec-side CLIs
   expose, and LiveSpec MUST NOT read the orchestrator's work-item
   store, prompts, or internal state. Every config-named CLI is
   dispatchable directly from the config value with no out-of-band
   name → invocation mapping.
6. Update §"Wrapper CLI surface", §"Skill ↔ template JSON contracts",
   §"Sub-command wire contracts", and other sections that currently
   describe the contract in skill terms to reference the CLI contract.
   (The wholesale decomposition of each skill into prose + CLI is
   Phase 2 implementation work; this proposal re-states the CONTRACT,
   and Phase 2 realizes it.)

## Proposal: shrink-doctor-cross-boundary-job-to-cli-callability

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Doctor's entire cross-boundary job becomes: **every config-named CLI
resolves and is callable.** All semantic cross-boundary invariants are
deleted from core's contract: `gap-tracking-one-to-one`,
`no-orphan-dependency`, `no-stale-gap-tied`, `no-duplicate-gap-id`,
`no-stalled-epic`, `depends_on-ref-wellformedness`, and
`unresolved-spec-commitment`. Doctor never inspects gaps, work-items,
or stores. Spec-tier static checks and repo-hygiene invariants are
unaffected.

### Motivation

Every deleted invariant walks the orchestrator's private state
(work-items, `depends_on` graphs, gap-id labels, commitment hints) —
exactly the class of coupling the re-steering removes. An orchestrator
that wants those disciplines owns them privately (its Ledger can
enforce far richer invariants natively). What core can legitimately
verify across the boundary is that the wiring table is sound: the
named CLIs exist and can be invoked. The "callable" test leans
zero-shape (the named CLI resolves and is executable; no probe
convention) — if a probe convention later proves necessary it is a
follow-on refinement, not part of this change.

### Proposed Changes

1. In §"Doctor cross-boundary invariants", remove the seven semantic
   invariants listed above, the §"Work-item integrity invariants —
   plugin-agnostic data acquisition" acquisition mechanism (including
   the `LIVESPEC_IMPL_LIST_WORK_ITEMS` env-var seam), and the
   `gap-tracking-one-to-one` snapshot machinery. Replace the section
   intro with the single cross-boundary invariant
   **`config-named-cli-callability`**: for every CLI named in
   `.livespec.jsonc` (spec-side and orchestrator-side), the named
   entry resolves and is executable; a missing or non-executable
   resolution fires `fail` naming the config key and value.
2. RETAIN unchanged the spec/repo-tier invariants that read no
   orchestrator state: `primary-checkout-commit-refuse-hook-installed`,
   `master-direct-uncommitted-spec-edits`,
   `copier-template-workflow-coverage`, and the whole static-phase
   spec-tree catalogue (version contiguity, out-of-band edits, heading
   taxonomy, etc.).
3. `contract-version-compatibility` `[RESERVED #3]`: the draft's
   leaning is to RELOCATE the `compat`/pin-and-bump enforcement to the
   family/dev-tooling coordination surface (`livespec-dev-tooling`
   already owns the bump-pin automation) and drop this invariant from
   core's catalogue — it is not "is a named CLI callable". If the user
   decides retention instead, the invariant stays with its current
   text. The revise session executes whichever disposition #3 lands
   on.
4. The memo-hygiene invariant (doctor → `list-memos`) is removed with
   the 10-skill surface: memos are orchestrator-private queue state.

## Proposal: relocate-work-item-and-dependency-machinery-out-of-core

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/spec.md

### Summary

Execute "item 0": everything about work-items, dependency graphs,
stores, and cross-repo work-item resolution moves OUT of core's
contract into the orchestrator. Core's `.livespec.jsonc` contract
shrinks to spec-tier facts (`template`, `spec_root`) + the named CLIs.
§"Cross-repo dependency awareness" (the typed `DependsOnEntry` union,
`livespec_runtime.cross_repo.resolve_ref`, retry policy, consumer
surface, hook integration) leaves core's contract entirely.
§"Spec Reader required-capability surface" is superseded by the
spec-reader CLI.

### Motivation

Under the re-steered model, work-items and their `depends_on` graph
are the orchestrator's Ledger — private by construction. Core
specifying their record schema, their dependency-entry typing, their
resolution semantics, or their store paths contradicts the contract
boundary this migration establishes. An orchestrator that models
cross-repo dependencies owns that machinery; another may model it
natively or not at all.

### Proposed Changes

1. Remove §"Cross-repo dependency awareness" and all its subsections
   from core's contract. The machinery itself (the
   `livespec_runtime.cross_repo` code) does not vanish — it becomes
   contract surface of whichever orchestrator uses it, documented in
   that orchestrator's own SPECIFICATION; core's contract no longer
   names it. Doctor invariants that walked it are deleted by
   Proposal 3.
2. Remove the orchestrator-private config keys from core's
   `.livespec.jsonc` schema: the per-plugin `format`,
   `work_items_path`, `memos_path` class of keys (an orchestrator MAY
   keep equivalents in its OWN config section; core's schema does not
   know them). Replace `implementation: { plugin: ... }` with the
   orchestrator selection + the three named orchestrator CLIs (exact
   key naming is Phase-2 implementation detail; the contract here is
   that config names an orchestrator and its three CLIs).
3. `cross_repo_targets` `[RESERVED #4]`: the draft's leaning is the
   split the research doc proposes — the work-item-resolution use
   moves to the orchestrator; any release-coordination use moves to
   the family-coordination surface alongside pin-and-bump
   `[RESERVED #3]`. Until #3/#4 are decided, this proposal records the
   leaning and the revise session executes the decided cut.
4. Remove §"Spec Reader required-capability surface"; the spec-reader
   CLI (Proposal 2) supersedes it. The four required capabilities
   (read current spec, read history, report version, diff versions)
   are downgraded from contract to non-normative guidance for
   spec-reader implementers, explicitly noting the
   category-exposure rule (categorizes, never conceals) as the one
   surviving normative property, stated on the CLI.
5. In spec.md §"Proposed-change and revision file formats", the
   `spec_commitments` front-matter machinery loses its cross-boundary
   enforcement (the `unresolved-spec-commitment` invariant is deleted
   by Proposal 3, and `spec_commitment_hint` leaves with the work-item
   schema). The declaration block itself is RETAINED as OPTIONAL
   informational provenance (a propose-change MAY declare expected
   impl follow-ups for human readers); whether an orchestrator tracks
   them is its private choice. Gap detection — the spec→impl flow —
   is the durable mechanism that surfaces unrealized spec commitments.

## Proposal: retire-layer3-surface-and-relocate-dispatcher-discipline

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Retire the Layer-3 orchestration surface end-to-end: the
livespec-resident driver mandate (spec.md), the §"Layer 3
discoverability nudge" (contracts.md), and
non-functional-requirements.md §"Cross-repo orchestration layer
(livespec-resident)" + §"Layer 3 loop driver — required shape and
discipline". The loop DISCIPLINE those sections carry (mode parameter,
budget parameter, janitor-as-hard-gate, structured iteration journal,
config-supplied janitor/branch/manifest/isolation) does not disappear:
it relocates as orchestrator-internal **Dispatcher** guidance.

### Motivation

Per the reframing doc's disposition of the pending recast
propose-change: the "Layer 3 standalone plugin" framing and the
three-layer architecture it lives in are overtaken — the loop moved
into the orchestrator, so there is no Layer 3 to be
resident-or-plugin about. The livespec-resident-vs-plugin distribution
debate dissolves. What survives is (a) the
published-surface-only discipline (folded into Proposal 2) and (b) the
loop discipline, which is exactly the Dispatcher's specification and
belongs inside the orchestrator repo's own spec, not core's.
`[RESERVED #5]` records the recommendation that the pending recast
propose-change is formally REJECTED at revise (rather than revised
into a model with no layers), with this proposal as the named
successor for its surviving content.

### Proposed Changes

1. spec.md: the Layer-3 bullet and cross-side-composition paragraph
   are removed by Proposal 1; this proposal records that no repository
   is REQUIRED or expected to carry a cross-repo loop driver as core
   contract surface, and the existing
   `.claude/skills/livespec-orchestrate/SKILL.md` is slated for
   retirement when the reference orchestrator realizes the Dispatcher
   (Phase 4 implementation; until then it remains as working tooling
   without contract status).
2. contracts.md: remove §"Layer 3 discoverability nudge" from the
   `/livespec:next` section (there is no Layer-3 surface to nudge
   toward; an unconditional nudge is a dead-end pointer). The
   spec-side `next` skill itself REMAINS in core's spec lifecycle —
   ranking the next SPEC-side action is a spec-tier concern. The
   cross-side "what should I work on now" composition dissolves:
   impl-side ranking is Dispatcher-private over the Ledger; the
   spec ↔ impl adjudication is already handled by the two flows (gap
   corrects the implementation; drift corrects the spec,
   human-accepted).
3. non-functional-requirements.md: remove §"Cross-repo orchestration
   layer (livespec-resident)" and §"Layer 3 loop driver — required
   shape and discipline". Add a compact non-normative
   §"Orchestrator-internal Dispatcher guidance" recording the
   relocated discipline for orchestrator authors: a Dispatcher SHOULD
   support a mode parameter, a budget parameter, a janitor command run
   as a hard gate, and a structured iteration journal; the janitor
   command, integration branch, repo manifest, and worktree/isolation
   strategy come from the orchestrator's own configuration, never
   hardcoded. The guidance is explicitly NON-normative on core's
   contract: core neither names nor verifies any of it (doctor's
   cross-boundary job is CLI callability only, per Proposal 3).
4. Impl-side cleanup invariants (`no-stale-merged-branch`,
   `no-stale-merged-pr-branch`, `no-stale-worktree`) leave core's
   contract with the 10-skill surface (Proposal 2.1): local-git
   hygiene around the production loop is the Dispatcher's janitor
   territory, orchestrator-private. (This also dissolves the open
   warn-status schema-gap blocker recorded against those invariants:
   core's Finding schema no longer needs a `warn` slot for them.)
