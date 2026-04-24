---
topic: proposal-critique-v17
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-24T18:15:00Z
---

# Proposal-critique v17

A targeted critique pass over v017 `PROPOSAL.md` surfacing six
gaps uncovered while reviewing the bootstrap plan
(`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`) against
PROPOSAL.md v017. The pass opens with a major-gap finding (Q1 —
built-in templates lack sufficient specifications for agentic
regeneration) plus five further integration / recreatability
gaps (Q2-Q6) surfaced in a second review wave and promoted by
the user during continuation-session triage.

Findings in this pass:

- **Major gaps (1 item):** Q1 (template sub-specifications).
- **Critical execution-blocking gaps (3 items):** Q2
  (self-application bootstrap exception), Q3 (initial-vendoring
  mechanism), Q4 (typechecker + returns-plugin disposition
  closure).
- **High quality / rework-risk gaps (2 items):** Q5 (seed-prompt
  LLM round-trip correctness verification), Q6 (companion-doc
  migration policy).

## Proposal: Q1 — Built-in templates lack sufficient specifications for agentic regeneration, and the main spec has no structural hook for template sub-specifications

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md` (the
  `template-prompt-authoring` entry; possibly a new entry
  formalizing the sub-spec mechanism)

### Summary

**Failure mode: incompleteness (major gap).** PROPOSAL.md
specifies the STRUCTURE of the two built-in templates
(`livespec`, `minimal`) — directory layout, required files,
`template.json` schema, prompt I/O contracts — but does NOT
specify their CONTENT to the fidelity required to agentically
(re)generate a template that meets livespec's quality criteria.

Specifically, the following are unspecified or under-specified:

- **Prompt interview flow.** `prompts/seed.md` must drive an LLM
  to produce schema-valid `seed_input.schema.json` payloads from
  user intent. PROPOSAL.md §"Built-in template: `livespec`"
  (lines ~1231-1279) says only that "top-level headings [are]
  derived from the seed intent by the template's
  `prompts/seed.md` (template-controlled behavior)". No
  interview structure, question order, or heading-derivation
  heuristic is specified. The same applies to
  `prompts/propose-change.md`, `prompts/revise.md`, and
  `prompts/critique.md`.
- **NLSpec discipline internalization.** The `livespec`
  template's prompts Read `livespec-nlspec-spec.md`
  (PROPOSAL.md lines ~1268-1272), but what NLSpec discipline
  each prompt extracts from the reference — and how the
  extracted discipline gets injected into the LLM's
  output — is unspecified.
- **Starter content beyond the `scenarios.md` literal.**
  `README.md`, `spec.md`, `contracts.md`, `constraints.md` are
  described as "header and placeholder section(s)" (lines
  ~1235-1246). No placeholder text, heading taxonomy, or
  BCP14-keyword discipline is specified for these files.
- **Delimiter-comment format (minimal template).** Already
  deferred — v014 N9 + v016 P2 + `deferred-items.md`'s
  `template-prompt-authoring` + `end-to-end-integration-test`
  entries all name this as "implementer choice" / "joint
  resolution".
- **Critique prompt finding-emission and revise prompt
  accept/reject structure.** Both prompts' internal flow is
  unspecified.

The recreatability test fails here in a specific way: two
competent implementers — or, more pointedly, two agents each
authoring template content from the spec alone — produce
templates that both pass `doctor`-static checks but whose prompt
behavior diverges substantially. One seed prompt might ask three
questions; another might ask twelve. One might derive `spec.md`
headings narrowly from user nouns; another might expand to a
predefined taxonomy. The resulting templates are not
interchangeable deliverables.

This is a **major gap** because the two built-in templates are
livespec's primary user-facing surface. Every seeded project's
initial spec quality is entirely determined by the seed prompt's
behavior. An under-specified prompt produces under-specified
specs downstream.

### Motivation

Livespec's self-application principle declares that livespec
itself is maintained via livespec's own propose-change → revise
loop ("dogfooding", per PROPOSAL.md §"Self-application"). This
principle implies that any livespec-shipped artifact —
including the two built-in templates — must be specifiable to
the fidelity required for regeneration via that loop. Today,
the templates cannot be: their content is largely implicit in
"whoever wrote them".

The concrete consequences visible in the bootstrap plan:

- Phase 2 and Phase 3 currently author template prompt content
  by hand (or by agent). If by hand, it bypasses the governed
  loop. If by agent, the agent has no spec to author against —
  only narrative intent scattered across PROPOSAL.md.
- The `template-prompt-authoring` deferred-items entry punts on
  this ("implementer choice"), which is acceptable for v1 scope
  decisions but NOT for long-term template evolution or for the
  v1 self-application DoD item 14.
- Custom-template authors (v1 scope per PROPOSAL.md line 1175)
  have no reference for what a well-specified template looks
  like — PROPOSAL.md's own `livespec` template is the intended
  reference, but that template is currently specified only by
  the implicit behavior of its files.

The main specification also needs a structural hook for nested
sub-specifications so that livespec-shipped sub-artifacts (the
built-in templates) can each carry their own spec tree under
the same governed loop. PROPOSAL.md's §"SPECIFICATION directory
structure (livespec template)" (lines ~763-850) describes a
flat structure — `spec.md`, `contracts.md`, `constraints.md`,
`scenarios.md`, `proposed_changes/`, `history/`. No provision
exists for nested sub-spec trees.

### Proposed Changes

Pick one:

**Option A (Recommended).** Extend the SPECIFICATION directory
structure to admit nested sub-specification directories for
livespec-shipped sub-artifacts:

- `SPECIFICATION/templates/<template-name>/` holds a complete
  sub-specification for each built-in template. Each sub-spec
  follows the same file conventions as the main spec — its own
  `spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`,
  `proposed_changes/`, `history/` — but scoped to the
  template's internal contracts, starter-content policies, and
  prompt interview flows.
- Template content (`template.json`, `prompts/*.md`, starter
  content under `specification-template/`) is generated by
  agents from its sub-spec. Changes flow through the same
  propose-change → revise loop, targeting the sub-spec's
  `proposed_changes/` and `history/` rather than the main
  spec's.
- The livespec repo itself seeds these sub-specs alongside its
  main spec. Phase 6 of the bootstrap plan produces main +
  two template sub-specs atomically.

Implications for the main spec (all of which must land in the
same v018 revision cycle as this decision):

- SPECIFICATION/ MAY contain a `templates/` subdirectory with
  one sub-directory per built-in template; each sub-directory
  is structurally identical to a livespec-managed spec tree.
- `doctor`-static checks parameterize over spec trees: the
  main `SPECIFICATION/` + each sub-spec under
  `SPECIFICATION/templates/<name>/`. Version-contiguity,
  history pairing, heading-coverage, BCP14 keyword, and
  Gherkin blank-line checks apply per-sub-spec (the `livespec`
  sub-spec uses Gherkin; the `minimal` sub-spec does not).
- `propose-change` and `revise` accept a
  `--spec-target <path>` flag (default: main spec root)
  selecting which sub-spec's `proposed_changes/` and `history/`
  are operated on. The seam is the same as `resolve_template.py`'s
  `--project-root` convention; the default is the spec root
  resolved via `.livespec.jsonc` at `--project-root`.
- `tests/heading-coverage.json` entries carry a `spec_root`
  field discriminating main-spec vs. sub-spec headings. The
  meta-test scopes its walk per entry.
- `seed` produces the full tree (main + sub-specs) atomically:
  one seed invocation populates main `spec.md`/etc. AND each
  template sub-spec. The `seed_input.schema.json` widens to
  carry a `sub_specs: list[SubSpecPayload]` field.
- v1 template scope: ONLY the `livespec` and `minimal`
  built-ins ship sub-specs. Custom templates MAY carry their
  own sub-spec but are NOT required to; livespec imposes no
  sub-spec requirement on extension authors (consistent with
  the user-provided extensions minimal-requirements principle).
- The `template-prompt-authoring` deferred-items entry is
  CLOSED by this change: prompt content is generated from the
  sub-spec's `spec.md` / `contracts.md` content, not
  implementer-chosen. The closure revision points to the new
  sub-spec mechanism.
- A new deferred-items entry — `sub-spec-structural-
  formalization` — captures the expansion (doctor
  parameterization, propose-change/revise CLI widening, seed
  multi-tree output, heading-coverage scoping).

This matches livespec's self-application principle, places
template content under the same governed loop as core code, and
gives agents the spec fidelity they need to author template
prompts. It formalizes a scope expansion (sub-spec trees)
confined to livespec-shipped sub-artifacts. It does NOT re-open
v1's "Multi-specification per project" non-goal (PROPOSAL.md
§"Multi-specification per project" line 1009), which is about
unrelated independent specs co-existing in one repo; this is
hierarchical sub-specs of a single primary spec — a narrower,
strictly smaller model.

**Option B.** Formally lift v1's "Multi-specification per
project" non-goal for the livespec repo only. Each template is
its own independent livespec sub-project with its own
`.livespec.jsonc` at
`.claude-plugin/specification-templates/<name>/.livespec.jsonc`
and its own SPECIFICATION/ tree. Templates are governed by their
own independent propose-change/revise loops; the livespec repo's
root `.livespec.jsonc` governs only the main spec. propose-change
and revise auto-resolve via upward-walk to the nearest
`.livespec.jsonc` (PROPOSAL.md's existing mechanism). No new CLI
flag needed.

Implications: three sets of `proposed_changes/` + `history/`;
three `heading-coverage.json` files; three separate doctor runs
per `just check`; `mise install` and `just bootstrap` unchanged.
Cleaner per-template isolation; each template's versioning is
independent. Downside: lifts a stated v1 non-goal wholesale,
not surgically — admits multi-spec-per-project as a general
feature rather than as a livespec-internal mechanism.

**Option C.** Expand the main `spec.md` / `contracts.md` with
new sections fully specifying both templates' prompts, starter
content, and delimiter-comment format. No new directory
structure; no sub-specs. Concerns entangled with core `spec.md`
material; each template's prompt interview flow is a
several-hundred-line specification that would dominate the core
spec files. Contradicts livespec's file-separation conventions.
Not recommended.

Recommended: **A**, because it matches livespec's
self-application principle, confines scope expansion to a
narrow nested-sub-specs mechanism (not wholesale multi-spec),
and keeps the governed-loop invariant intact for every
livespec-shipped deliverable.

## Proposal: Q2 — Self-application bootstrap exception is implicit, not articulated

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`

### Summary

**Failure mode: incompleteness (ambiguity at boundary).**
PROPOSAL.md §"Self-application" mandates that livespec be
developed by dogfooding: "every change" lands via the
propose-change → revise loop. But the FIRST landing of the
propose-change and revise sub-commands themselves has nowhere
to flow through — their targets do not exist at that point. The
`Self-application` section's step 2 ("Implement the plugin
skeleton") followed by step 4 ("using propose-change/revise
cycles against the seeded spec") constitutes a de-facto
bootstrap exception, but it is implicit — not named or bounded
as such.

The recreatability test fails in a pointed way: an agent or
implementer reading PROPOSAL.md v1 alone cannot tell which
parts of the implementation are subject to the dogfooding rule.
Two reasonable readings are possible — "every change
including the skeleton must flow through the loop" (circular,
impossible) and "the skeleton lands imperatively and the loop
applies afterwards" (what the bootstrap plan assumes). The spec
does not pick between them.

### Motivation

The bootstrap plan at
`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` already assumes
the second reading: Phase 2 (skeleton) and Phase 3 (minimum-
viable seed) land imperatively because their targets (the
propose-change and revise commands themselves) don't yet
exist; Phase 6 (first seed) is when the loop becomes operable
and every subsequent change flows through it.

Without an explicit bootstrap-exception clause in PROPOSAL.md:

- The spec and the bootstrap plan diverge on a core
  governance question. The plan operates under an assumption
  the spec doesn't validate.
- Future implementers of livespec-like tools reading PROPOSAL.md
  as reference cannot distinguish the bootstrap exception from
  an accidental ambiguity.
- Audits of "did this change flow through the loop?" cannot
  answer definitively because the boundary isn't defined.

### Proposed Changes

Pick one:

**Option A (Recommended).** Extend PROPOSAL.md §"Self-application"
with an explicit bootstrap-exception clause, placed immediately
after the numbered bootstrap ordering:

> **Bootstrap exception.** The bootstrap ordering above
> (steps 1-4, ending with the first `livespec seed` invocation)
> lands imperatively. The governed propose-change → revise loop
> becomes operable starting at step 5 — after seed has produced
> the working `SPECIFICATION/` tree. From the second change
> onward (every change to livespec's skill bundle, developer
> tooling, built-in templates, or the seeded `SPECIFICATION/`),
> the loop is MANDATORY; hand-editing any file under any spec
> tree or under `.claude-plugin/specification-templates/<name>/`
> after the first seed is a bug in execution, not a permitted
> fast-path. The exception applies ONCE per livespec repo, at
> initial bootstrap; it does NOT apply to v2+ releases of
> livespec (those flow through the governed loop against the
> then-existing SPECIFICATION).

Under v018 Q1-Option-A (template sub-specifications), the
exception likewise covers the initial Phase-6 seed of the two
template sub-specs under `SPECIFICATION/templates/<name>/`; from
Phase 7 onward each sub-spec is governed by its own propose-
change/revise loop via `--spec-target <path>`.

**Option B.** Inline the bootstrap-exception in the bootstrap
plan only, not in PROPOSAL.md. PROPOSAL.md remains silent on
bootstrap ordering.

Implication: treats the bootstrap plan as sole authority for
bootstrap behavior. Doesn't solve the recreatability test —
the plan is a working document, not the spec, and doesn't
propagate into every agent's context the way PROPOSAL.md does.

**Option C.** Rewrite §"Self-application" to say the loop
applies only from v1.0.0 onward, not from first seed.

Implication: pushes the bootstrap boundary far out. Phase 7
(remaining sub-commands) and Phase 8 (deferred-items processing)
would also land imperatively, contradicting the established
discipline that post-seed everything flows through the loop.

Recommended: **A**, because it makes the bootstrap boundary
explicit at the earliest point where the loop is operable
(first seed), preserves the governed-loop invariant for every
post-seed change, and closes the recreatability test. Fits
naturally alongside Q1-Option-A's sub-spec tree extension (the
same "from first seed onward" rule applies uniformly to main
spec + sub-specs).

## Proposal: Q3 — Initial-vendoring mechanism for upstream-sourced _vendor/ libraries is circular

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md`

### Summary

**Failure mode: incompleteness (circular bootstrap dependency).**
PROPOSAL.md §"Runtime dependencies → Vendored pure-Python
libraries" and `python-skill-script-style-requirements.md`
§"Vendoring discipline" both name `just vendor-update <lib>` as
"the only blessed mutation path" for upstream-sourced vendored
libs (`returns`, `fastjsonschema`, `structlog`, `jsoncomment`).
That recipe invokes Python through `livespec.parse.jsonc` to
read/write `.vendor.jsonc`, and `livespec.parse.jsonc` imports
the vendored `jsoncomment` library.

First-time vendoring of `jsoncomment` has no documented path —
the recipe cannot run before jsoncomment is already vendored.
The same gap applies to the initial population of `returns`,
`fastjsonschema`, and `structlog`. The `typing_extensions`
shim has a distinct carve-out (shim libraries widen manually
via code review, per v013 M1) but upstream-sourced libs have
no equivalent documented procedure.

### Motivation

The bootstrap plan's Phase 1 declares `.vendor.jsonc` with
entries for five libs, and Phase 2 lands `_vendor/<lib>/`
directories with their LICENSE files. But neither phase names
a mechanism for the initial population — is it
`just vendor-update jsoncomment` (impossible, since it depends
on jsoncomment itself), a one-time manual procedure (git clone
+ checkout + cp + LICENSE capture), or a dedicated bootstrap
recipe?

Without a documented answer:

- The recreatability test fails: two implementers will choose
  different procedures and produce non-identical initial
  `_vendor/` trees (different checkout timestamps, different
  LICENSE byte-capture moments, different directory shapes).
- Phase 2 review cannot audit "was the initial vendoring done
  correctly?" because there's no canonical procedure to check
  against.
- The spec says "never edit `_vendor/` files directly" and
  "the only blessed mutation path is `just vendor-update`"
  simultaneously; first-time population violates both rules by
  necessity.

### Proposed Changes

Pick one:

**Option A (Recommended).** Extend PROPOSAL.md §"Vendoring
discipline" (and mirror in the style doc §"Vendoring
discipline") with an explicit initial-vendoring clause:

> **Initial-vendoring exception (one-time).** The first
> population of every upstream-sourced vendored lib
> (`returns`, `fastjsonschema`, `structlog`, `jsoncomment`) is
> a one-time MANUAL procedure, distinct from the blessed
> `just vendor-update` path:
>
> 1. `git clone` the upstream repo at a working ref into a
>    throwaway directory.
> 2. `git checkout <ref>` matching the `upstream_ref` recorded
>    in `.vendor.jsonc`.
> 3. Copy the library's source tree under
>    `.claude-plugin/scripts/_vendor/<lib>/`.
> 4. Copy the upstream `LICENSE` file verbatim to
>    `.claude-plugin/scripts/_vendor/<lib>/LICENSE`.
> 5. Record the lib's provenance in `.vendor.jsonc`:
>    `upstream_url`, `upstream_ref`, `vendored_at` (ISO-8601
>    UTC).
> 6. Delete the throwaway clone.
> 7. Smoke-test: the wrapper bootstrap imports the vendored
>    lib successfully.
>
> Once `jsoncomment` is initially vendored, `just vendor-update
> <lib>` becomes the only permitted path for subsequent
> re-vendoring of upstream-sourced libs. The initial procedure
> applies ONCE per livespec repo, at Phase 2 of the bootstrap
> plan; thereafter all upstream-sourced-lib mutations flow
> through the blessed recipe. Shim libraries (currently only
> `typing_extensions`, per v013 M1) continue to follow the
> separate "widened manually via code review" rule —
> initial-vendoring of a shim is "the author writes the shim
> file by hand and copies the upstream LICENSE."

**Option B.** Author a `just vendor-bootstrap-all` recipe that
runs pure-shell (no Python) to initially-populate every
vendored lib, then `just vendor-update` takes over.

Implication: adds a second just recipe; the shell-only recipe
diverges from Python-standard rules (livespec's single-language
principle); no clear gain over A's one-time manual procedure.

**Option C.** Write the initial population in a dedicated
`dev-tooling/bootstrap_vendor.py` script that depends only on
stdlib.

Implication: creates a two-tier bootstrap (stdlib bootstrapper
populates jsoncomment; jsoncomment-dependent
`livespec.parse.jsonc` handles subsequent updates). Splits the
vendoring authority across two distinct mechanisms.

Recommended: **A**, because it's the simplest narrow carve-out
(one-time exception, explicitly bounded to Phase 2),
preserves `just vendor-update` as the sole post-bootstrap
mutation path, doesn't introduce a second mechanism, and
matches the bootstrap-exception pattern proposed in Q2 (narrow
carve-outs for genuinely-one-time operations).

## Proposal: Q4 — Typechecker + returns-pyright-plugin disposition deferred without closure criteria

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`

### Summary

**Failure mode: incompleteness (under-specified closure
criteria).** Both `returns-pyright-plugin-disposition` (v007)
and `basedpyright-vs-pyright` (v012 L14) are deferred items
without objective closure criteria. Their `deferred-items.md`
entries list tradeoffs but do not name the observable condition
that closes the decision. Per the deferred-items discipline,
every entry must be closable by a future propose-change;
without criteria, no propose-change can close them at which
point closure becomes implementer judgment — defeating the
recreatability test.

Simultaneously, the bootstrap plan's Phase 1 (per the recent
commit `b041d19` revising the plan toward narrow Phase-3 gate
+ earlier typechecker decisions) declares these decisions are
made DURING Phase 1 by pinning the chosen typechecker + plugin
config in `pyproject.toml` with rationale comments. But
PROPOSAL.md does not reflect that push-forward, nor does it
name the criteria Phase 1 uses.

### Motivation

- The typechecker choice is a load-bearing guardrail. The
  "Strongest-possible guardrails for agent-authored Python"
  principle (foundational since v012) rests on pyright
  strict-plus diagnostics (v012 L1 + L2). basedpyright's
  defaults-are-stricter advantage and baselining system are
  alternative mechanisms for the same guardrail.
- The `returns`-pyright-plugin disposition affects every
  `Result`/`IOResult` type in livespec (pervasive). Without the
  plugin, certain two-track composition paths may require
  `# type: ignore`, which contradicts the style doc's "no
  # type: ignore without narrow justification" rule.
- Leaving both deferred without criteria means Phase 1 is the
  implicit closure point — but PROPOSAL.md doesn't document
  that, and `deferred-items.md`'s entries don't name a criterion
  that Phase 1 uses. Two implementers running Phase 1 will
  reach different conclusions.

### Proposed Changes

Pick one:

**Option A (Recommended).** Decide both at v018 spec level,
naming concrete choices with rationale captured in PROPOSAL.md
§"Runtime dependencies → Developer-time dependencies" and
style doc §"Type safety":

- **`returns-pyright-plugin-disposition`: vendor the
  dry-python/returns pyright plugin alongside the library** at
  `.claude-plugin/scripts/_vendor/returns_pyright_plugin/`;
  configure in `[tool.pyright]` via `pluginPaths` pointing at
  the vendored plugin directory. Rationale: `Result` and
  `IOResult` are used pervasively (every public function
  returns one or the other per the architecture-level
  constraint); without the plugin, strict-mode inference of
  the two-track composition forces routine `# type: ignore`
  usage, contradicting both the style-doc rule and the
  guardrail principle.

  Deferred-items entry CLOSED in v018; `deferred-items.md`
  entry body rewritten to a closure pointer referencing
  PROPOSAL.md + style-doc sections.

- **`basedpyright-vs-pyright`: stay on pyright** (preserving
  the v012 L14 original recommendation). Rationale: pyright's
  strict-plus diagnostics (v012 L1 + L2, manually enabled) are
  the load-bearing guardrails; basedpyright's
  defaults-are-stricter advantage is marginal given v012 L1+L2
  already manually enabled every strict-plus option required.
  basedpyright's baselining system is valuable for legacy-code
  adoption but livespec starts strict from Phase 2 (no legacy
  code baseline needed). Community-fork maintainer-pool risk
  outweighs the incremental defaults-simplification benefit.

  Deferred-items entry CLOSED in v018; `deferred-items.md`
  entry body rewritten to a closure pointer.

**Option B.** Leave both deferred but add objective closure
criteria to each `deferred-items.md` entry:

- `returns-pyright-plugin-disposition`: close with the choice
  that minimizes `# type: ignore` instances in
  `.claude-plugin/scripts/livespec/**` under pyright strict-plus.
  Measurable — an implementer can evaluate (with plugin vs
  without) against a test code base and pick.
- `basedpyright-vs-pyright`: close with the choice that
  requires fewer manual strict-plus flag selections in
  `pyproject.toml` AND preserves all v012 L1 + L2 diagnostics.
  Measurable — an implementer can diff the two configurations.

Implication: kicks both closures to Phase 1 (per the bootstrap
plan's existing intent). Criteria exist but require running
Phase 1 to resolve; no v018 spec-level decision.

**Option C.** Keep deferred without criteria but name the
Phase-1 bootstrap plan as the closure mechanism (the Phase-1
commit pins the choice with rationale in `pyproject.toml`
comments).

Implication: PROPOSAL.md doesn't decide; PROPOSAL.md still
lacks the criteria. Defers everything to an external document
(the bootstrap plan, which isn't part of the spec and may
evolve independently).

Recommended: **A**, because the typechecker choice is load-
bearing enough to belong in the spec with rationale; pushing
both decisions to v018 lets the bootstrap plan's Phase 1
reference PROPOSAL.md as the authority (rather than the
reverse). Matches "Specify architecture, not mechanism": the
typechecker-plus-plugin IS architecture (it affects public-API
type guarantees across every module), not mechanism.

## Proposal: Q5 — Seed-prompt LLM round-trip correctness unverifiable before the E2E integration test runs

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`
  (`end-to-end-integration-test` and `template-prompt-authoring`
  entries interact with this)

### Summary

**Failure mode: incompleteness (verification gap).**
PROPOSAL.md §"Templates → Skill↔template communication layer"
defines the JSON schema contract between the skill and each
template prompt, and §"Testing approach → End-to-end harness-
level integration test" defines a harness-level E2E test using
the `minimal` template. Two gaps:

1. The `livespec` template's prompts (`prompts/seed.md`,
   `prompts/propose-change.md`, `prompts/revise.md`,
   `prompts/critique.md`, plus the two optional
   `prompts/doctor-llm-*-checks.md`) carry substantially more
   authoring complexity than `minimal`'s (spec-file-structure
   derivation, NLSpec-discipline injection, scenario-file
   convention compliance) but are NOT covered by any
   verification mechanism before the `real`-tier E2E test runs.
2. Under v018 Q1-Option-A, the `livespec` template's prompt
   content is agent-generated in Phase 7 from
   `SPECIFICATION/templates/livespec/` (the sub-spec seeded in
   Phase 6). The agent-generation step has no automatic
   verification tier before Phase 8's deferred-items processing
   consumes its output.

A silently-wrong `prompts/seed.md` produces garbage
SPECIFICATION output downstream. A silently-wrong
`prompts/revise.md` produces garbage history. The E2E mock
tier's `fake_claude.py` replaces ONLY the SDK layer — it does
NOT exercise prompt behavior; prompt behavior is exercised
only when `LIVESPEC_E2E_HARNESS=real` (which requires
`ANTHROPIC_API_KEY` and does NOT run in `just check`).

### Motivation

- The `minimal` template's prompts have hardcoded delimiter
  comments (v014 N9) that let `fake_claude.py` drive wrappers
  deterministically. But the delimiters don't validate prompt
  *behavior* (what the prompt asks the LLM to produce) — they
  only identify *which wrappers to invoke*. A minimal prompt
  could be broken and the mock test still passes.
- The `livespec` template has no delimiter convention (v014 N9
  explicitly exempted it). Its prompts are validated only at
  agent-generation time in Phase 7, against the Phase-6-seeded
  sub-spec.
- Without a prompt-level verification tier, Phase 7's
  agent-generation step either passes through without
  validation OR has to invent its own verification (implementer
  judgment).
- Phase 8 deferred-items processing consumes prompt-driven
  output (seed-produced content migrated into SPECIFICATION/
  sections). Broken prompts poison Phase 8's input.

### Proposed Changes

Pick one:

**Option A (Recommended).** Add a dedicated prompt-QA tier to
PROPOSAL.md §"Testing approach", distinct from the E2E harness
tier:

- `tests/prompts/` subtree mirroring the structure of
  `.claude-plugin/specification-templates/<name>/prompts/` for
  every built-in template.
- Per-prompt tests exercise the prompt against a small
  deterministic fake_claude harness scoped to prompt-level
  behavior (distinct from `tests/e2e/fake_claude.py`, which
  drives wrappers end-to-end). The prompt-QA harness replays
  a deterministic prompt-response pair per test case and
  asserts on the structured output (schema validity at the
  `{seed,proposal,revise}_input.schema.json` boundary PLUS
  semantic properties — e.g., that a seed prompt given
  "build a web service" intent produces top-level headings
  matching the domain, not arbitrary taxonomy).
- Every built-in template's REQUIRED prompts
  (`seed.md`, `propose-change.md`, `revise.md`,
  `critique.md`) MUST have ≥1 prompt-QA test each. Custom
  templates MAY ship their own prompt-QA tests; livespec does
  not require them (consistent with the minimal-requirements
  principle for user-provided extensions).
- Runs as part of `just check` (per-commit cadence). Fast
  and deterministic — no live API, no real LLM invocation.
- Naming: a new deferred-items entry
  `prompt-qa-harness` captures the specific implementation
  (harness shape, fixture format, which schema-level vs
  semantic-level assertions apply per prompt); the entry is
  joint-resolved with `template-prompt-authoring` (which
  authors the prompts being tested) and
  `end-to-end-integration-test` (which owns the distinct E2E
  harness).

Under v018 Q1-Option-A, the prompt-QA tier validates every
built-in template's prompts BEFORE Phase 7 agent-generates
their final content from their sub-specs. Phase 7's propose-
change cycle against each sub-spec therefore targets a prompt
set whose behavior is already machine-verified.

**Option B.** Expand the existing `tests/e2e/fake_claude.py`
to cover the `livespec` template (in addition to its current
`minimal`-only scope). The v014 N9 delimiter-comment convention
extends to the `livespec` template's prompts.

Implication: breaks the v014 N9 minimal-template-only scoping;
forces delimiter comments in the `livespec` template's prompts
(explicitly exempted by v014 N9); larger E2E surface; no clean
split between wrapper-level integration and prompt-level
behavior verification.

**Option C.** Defer verification to Phase 7's agent-generation
step. Phase 7's propose-change/revise cycle against
`SPECIFICATION/templates/livespec/` generates the prompts; the
revise step applies schema validation on the generated output;
if prompts produce bad output during Phase 7, Phase 7 catches
it.

Implication: depends on Phase 7 being a living oracle (it is,
post-seed). Leaves no automatic per-commit regression test;
Phase 7 runs once at bootstrap time and is not re-executed on
every change. Phase 7 catches Phase-7-time breakage; it does
not catch subsequent regressions.

Recommended: **A**, because it adds a dedicated verification
tier that is deterministic, scoped to prompt behavior, and
runs per-commit. The E2E tier stays harness-level (wrapper
integration); the prompt-QA tier stays unit-level (prompt
behavior). Matches the "static enumeration over dynamic
discovery" principle — every prompt has a deterministic test
case enumerated in the test tree.

## Proposal: Q6 — Companion-doc migration policy under-specified for Phase 8 auditability

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`
  (`companion-docs-mapping` entry)

### Summary

**Failure mode: incompleteness.** The `companion-docs-mapping`
deferred entry names a destination per doc informally (e.g.,
"`subdomains-and-unsolved-routing.md` → spec.md 'Non-goals'
appendix or similar"). The "or similar" hedging is judgment-
left-to-implementer. Two implementers processing the same
deferred entries will produce non-identical seeded specs
(different section placements, different section titles, some
docs migrated vs archived, etc.).

The bootstrap plan's Phase 8 "verify every companion doc has a
mapped home in `SPECIFICATION/`" does not resolve the "or
similar" ambiguity — it only verifies *that* a home exists,
not *which* home is correct.

### Motivation

The bootstrap plan's Phase 6 narrows seed to PROPOSAL.md +
`goals-and-non-goals.md` only, deferring other companion docs
to Phase 8's propose-change/revise cycles. Phase 8's
auditability depends on each companion doc having a precisely-
named destination BEFORE the cycle starts. Without that
precision, Phase 8 makes judgment calls during the cycle
(implementer judgment), which defeats the recreatability test.

Concrete consequence: a reviewer looking at a Phase-8 revise
commit cannot answer "did the migration go to the right
place?" without re-running the judgment call the original
author made.

### Proposed Changes

Pick one:

**Option A (Recommended).** Formalize a migration-class policy
in PROPOSAL.md §"Self-application" (or a dedicated §"Companion
documents and migration classes" subsection). Each companion
doc is classified as exactly one of:

- **MIGRATED-to-SPEC-file**: content moves verbatim (or
  restructured for BCP 14 + heading conventions) into a named
  `SPECIFICATION/` file. The destination file is named
  explicitly.
- **SUPERSEDED-by-section**: content becomes a named section
  in an existing `SPECIFICATION/` file. The destination file
  AND the receiving section name are both named explicitly.
- **ARCHIVE-ONLY**: content lives in `brainstorming/` for
  historical context, not migrated. Explicit rationale
  required per doc.

PROPOSAL.md carries a table assigning every companion doc
in `brainstorming/approach-2-nlspec-based/` to one class + its
destination. Candidate assignments (Phase 6 scope vs Phase 8
scope also noted):

| Doc | Class | Destination | Phase |
|---|---|---|---|
| `goals-and-non-goals.md` | SUPERSEDED-by-section | `spec.md` "Goals" + "Non-goals" sections | 6 |
| `python-skill-script-style-requirements.md` | MIGRATED-to-SPEC-file | `constraints.md` | 8 |
| `subdomains-and-unsolved-routing.md` | SUPERSEDED-by-section | `spec.md` "Non-goals" appendix | 8 |
| `prior-art.md` | SUPERSEDED-by-section | `spec.md` "Prior Art" appendix | 8 |
| `2026-04-19-nlspec-lifecycle-diagram.md` | SUPERSEDED-by-section | `spec.md` "Lifecycle" section | 8 |
| `2026-04-19-nlspec-lifecycle-diagram-detailed.md` | SUPERSEDED-by-section | `spec.md` "Lifecycle" section (subordinate to preceding entry) | 8 |
| `2026-04-19-nlspec-lifecycle-legend.md` | SUPERSEDED-by-section | `spec.md` "Lifecycle" section (subordinate) | 8 |
| `2026-04-19-nlspec-terminology-and-structure-summary.md` | SUPERSEDED-by-section | `spec.md` "Lifecycle" section (subordinate) | 8 |
| `livespec-nlspec-spec.md` | ARCHIVE-ONLY + TEMPLATE-BUNDLED | Archived in `brainstorming/`; shipped as-is in `.claude-plugin/specification-templates/livespec/livespec-nlspec-spec.md` (per PROPOSAL.md §"Built-in template: `livespec`") | N/A (already shipped) |
| `deferred-items.md` | ARCHIVE-ONLY | Archived in `brainstorming/`; items processed in Phase 8 | 8 (items) / N/A (doc itself) |
| `critique-interview-prompt.md` | ARCHIVE-ONLY | Archived in `brainstorming/`; brainstorming-process artifact, not part of shipped livespec | N/A |

Update the `companion-docs-mapping` deferred-items entry to
reference this policy; its body becomes a pointer to PROPOSAL.md
plus per-doc resolution notes during Phase 8 processing.

**Option B.** Defer the classification to Phase 8 itself. Add
criteria to the `companion-docs-mapping` deferred entry: "for
each companion doc, the propose-change names its destination
class; if SUPERSEDED, the revise documents the receiving
section; if MIGRATED, the revise names the resulting spec file;
if ARCHIVE-ONLY, the revise documents why no migration is
needed." Phase 8 provides the policy at processing time.

Implication: still implementer judgment at Phase 8 time, but
with a structured decision surface. Each Phase-8 propose-change
makes the class explicit; reviewers can audit class choice per
commit. Doesn't resolve the recreatability gap at spec level
(two implementers produce different classifications).

**Option C.** Adopt Option A's policy without the categorical
labels — instead, for each doc, name the exact destination
("X goes to Y, section Z"). Simpler table; categories implicit.

Implication: functionally equivalent to A for mechanical
purposes; loses the reusable categorization that future
custom-template authors could model against. Works fine if
categorization is viewed as livespec-internal overhead.

Recommended: **A**, because it matches the bootstrap plan's
Phase 8 auditability need (each companion-doc migration is a
one-commit revise pointing at its pre-decided class and
destination), preserves the recreatability test, and gives
future custom-template authors a reference model for how
companion-doc migrations work. The categorical labels
(MIGRATED / SUPERSEDED / ARCHIVE-ONLY) are small overhead that
improves reviewability substantially.
