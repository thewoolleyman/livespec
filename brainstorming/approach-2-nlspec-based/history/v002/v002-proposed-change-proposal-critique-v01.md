# Proposal Critique v01 — Completeness for Bootstrapping a SPECIFICATION

## Purpose

This critique evaluates `PROPOSAL.md` and its companion files in
`brainstorming/approach-2-nlspec-based/` against the question:

> *Is this material sufficient, today, to seed a working `SPECIFICATION/`
> for `livespec` itself, such that a competent implementer (or agent) could
> proceed without making load-bearing guesses?*

The yardstick is the proposal's own embedded grounding document
(`livespec-nlspec-spec.md`):

- behavioral completeness
- unambiguous interfaces
- explicit defaults and boundaries
- mapping tables for translation
- testable acceptance criteria
- conceptual fidelity, spec economy, intentional vs accidental ambiguity
- the recreatability test

Each gap below is named, located, and labeled with the failure mode it
represents (per Appendix A of the embedded guidelines): **ambiguity**,
**malformation** (self-contradiction), **incompleteness** (scope gap), or
**incorrectness** (likely-wrong as stated).

---

## What Is Strong

These elements should survive into v001 of the spec largely intact:

- **Conceptual model.** `intent` (revision inputs) vs `spec` (current
  authoritative surface) is cleanly separated and well-justified
  (`2026-04-19-nlspec-terminology-and-structure-summary.md`). The
  governed loop reframing of NLSpec's one-way chain is internally
  coherent.
- **Lifecycle artifact set.** The five-artifact set —
  `seed → spec → proposed_changes → revise → history` — is small enough
  to reason about and matches the diagram in
  `2026-04-19-nlspec-lifecycle-diagram.md`.
- **Operational partitions.** The argument for splitting `spec.md`,
  `contracts.md`, `constraints.md`, `scenarios.md` on
  *LLM-processability* grounds (rather than aesthetic ones) is the
  proposal's strongest "why".
- **Honest non-goals.** `subdomains-and-unsolved-routing.md` and
  `goals-and-non-goals.md` correctly refuse to fake a solution to
  cross-cutting routing. This is rare and worth preserving as an
  explicit boundary clarification (intentional ambiguity in the
  guidelines' sense).
- **Embedded grounding.** Carrying a project-local adapted copy of the
  NLSpec guidelines, with its diff from the upstream enumerated, is the
  right pattern.

---

## Major Gaps That Block Seeding

Each of these is load-bearing for v001 — the spec cannot be authored
without resolving them.

### 1. Runtime / packaging model is undefined — **incompleteness**

`PROPOSAL.md` calls `livespec` a "skill" with sub-commands but never
states:

- whether it is a Claude Code skill, an MCP server, a standalone CLI,
  some combination, or all three
- where the skill lives on disk (project-local? user-global?
  plugin-installed?)
- how sub-commands are dispatched (`/livespec seed …`? bash entry
  point? slash command?)
- what the host environment guarantees the skill can do (file I/O,
  shell execution, LLM calls)

Without this, every other behavior is unanchored. *Two implementers
would build incompatible systems from this proposal alone.*

### 2. Template mechanism is deferred but already required — **malformation**

The proposal simultaneously:

- requires `.livespec.jsonc` to name an `active template` with values
  `livespec | openspec | custom` (`PROPOSAL.md` line 28)
- claims templates define the on-disk structure (line 111)
- says templates are loaded by an unspecified mechanism (line 114)
- declares "designing the full template mechanism right now" a non-goal
  (`goals-and-non-goals.md` §"Non-Goals" 5)

This is a self-contradiction: every command (`seed`, `doctor`,
`propose-change`, `revise`) depends on knowing the template's shape, but
the template format is intentionally not specified. **The proposal
cannot ship without at least a hardcoded `livespec` built-in template
specified in full.** "Templates as a pluggable concept" can stay
deferred; the *one* baked-in template cannot.

Specific consequences:

- `custom` is listed as an enum value but `custom` is a category, not a
  template — schema-level confusion.
- `openspec` template is named but its on-disk layout, file names,
  conventions are not. The OpenSpec project versions are not pinned.
- Whether the OpenSpec template still uses `proposed_changes` /
  `history` semantics or adopts OpenSpec's `changes/` model is open.
  This is a routing / ownership question the proposal explicitly says
  it won't answer, but it must answer it for *built-in* templates.

### 3. `.livespec.jsonc` schema is underspecified — **incompleteness**

The proposal mandates "There is a json schema for this file, and it is
always enforced when reading and writing it" (line 30). The schema is
not provided. Required to seed:

- exhaustive field list and types
- defaults for every field (the guidelines insist defaults are
  requirements)
- behavior when the file is absent (does seed create it? does doctor
  refuse to run?)
- behavior with multiple `SPECIFICATION` dirs (line 10 says "Must
  handle multiple specifications in same project" — no model is given:
  array of dir paths? selector by command-line arg? per-subtree
  config?)
- precedence rules vs CLI flags vs environment variables (none
  mentioned)

### 4. Versioning semantics are undefined — **incompleteness**

`vnnn` directories appear throughout `PROPOSAL.md` but the proposal
never states:

- when a new version is cut (every `revise`? only on accepted change?
  on any spec write?)
- whether `revise` with zero accepted proposals still bumps version
- the format of `nnn` (zero-padded width? overflow at v999? semver
  alternative?)
- ordering rules when two `propose-change`s exist for the same topic
- whether the *current* `spec.md` is also stamped (line 43 implies
  history copies are prefixed `vnnn-` but the live working copy is
  not — needs to be made explicit)
- how to refer to "version 0" — pre-seed state? first seed? first
  revise after seed?

### 5. Proposed-change and acknowledgement formats — **incompleteness**

`PROPOSAL.md` requires both artifacts but specifies neither:

- **Proposed change.** Required sections? Front-matter? "Inline diff"
  format (unified diff? Markdown delta blocks? structured JSON
  patches)? How is a diff against "latest version" anchored when files
  may have been re-flowed?
- **Acknowledgement.** Required structure? Per-proposal or
  per-revision? Schema for "rationale for which proposed changes were
  accepted, which were rejected, and any revisions made"?

Without these, the `revise` step has no contract, and `doctor` has
nothing to statically check.

### 6. `revise` decision authority is ambiguous — **ambiguity**

Line 68 says `revise` "**Automatically** processes and acknowledges all
change proposals" but line 72 then expects "rationale for which proposed
changes were accepted, **which were rejected**, and any revisions made".

Who decides the accept/reject split? The LLM unilaterally? The user via
prompt? A merge-conflict-style review loop? This is the most consequential
human-in-the-loop question in the whole system and it is not addressed.

### 7. `doctor` static-check inventory is illustrative, not exhaustive — **incompleteness**

Line 79 lists "directory structure, template compliance, missing
versions in history, diff between current version and latest version in
history, missing tests, etc." The `etc.` is the problem. For doctor to
be implementable:

- enumerate every static check, its failure message, and its remediation
- specify exit code semantics (LLM-driven phase requires nonzero exit
  to short-circuit; what counts as failure vs warning?)
- define the "diff between current and latest history version" check
  precisely — diff of which files? what whitespace policy? what about
  intentional same-version edits?
- "missing tests" presumes a test-discovery convention the proposal
  has not defined (see §10)

Also: line 89 mandates "All commands should run doctor before and
after execution." This includes `help`, `seed` (pre-existence), and
`doctor` itself (recursion). Either carve out exceptions explicitly or
narrow the rule.

### 8. `seed` post-state is unspecified — **incompleteness**

After `seed` completes, the proposal does not say:

- whether `spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`
  are created empty, as headed stubs, or pre-populated from the seed
  text
- the contents of the auto-generated `README.md`s
- whether `.livespec.jsonc` is created if absent
- behavior on second invocation (idempotent? fail? offer migration?)
- whether `seed` itself produces a `v001` history entry or only the
  first `revise` does

This is the bootstrap-of-the-bootstrap and currently nondeterministic.

### 9. NLSpec progressive disclosure is hand-waved — **ambiguity**

Line 105: "the relevant subset of guidelines is surfaced in context for
the sub-command being executed". The mapping from sub-command to
relevant guideline subset is not defined. Without it:

- "progressive disclosure" is an aspiration, not a mechanism
- two implementers will surface different subsets and produce different
  behavior
- the embedded `livespec-nlspec-spec.md` (40 KB) is the only
  artifact, with no chunking or indexing scheme given

A mapping table (per the guidelines' own §4 — "tables beat prose for
mappings") is the natural fix.

### 10. Testing approach is under-defined and language-coupled — **ambiguity** and **incompleteness**

Lines 3–6:

- "python scripts" hardcodes a language. Why python specifically? Is
  this a guarantee of the spec or a coincidence of the current dev
  environment?
- "directly executing claude code and comparing to spec expectations"
  — `claude code` is one possible host. Does livespec require claude
  code at runtime or only for testing?
- "throwaway tmp dir" — fine, but what's seeded into it? A blank
  project? The current project as a copy?
- The `section_drift_prevention` meta-test is defined in one
  sentence — what counts as a "major section"? What does "corresponds
  to" mean (file name match? title text? annotation)?
- Test file naming, location, runner, and CI integration are absent.

Pull this section out of the bullet list and make it a sub-spec of its
own; it is currently the weakest part of the proposal relative to its
operational importance.

### 11. Holdout scenarios for Dark Factory are mentioned but not modeled — **incompleteness**

Multiple files cite "support holdout scenario usage in the StrongDM Dark
Factory style" as a *reason* `scenarios.md` is split out, but no file
defines:

- how holdouts are marked within `scenarios.md` (front-matter? section
  heading? separate file?)
- whether holdouts are excluded from default test runs
- how holdouts interact with `propose-change` / `revise` (can a
  proposal modify a holdout? is that a smell?)

If the rationale is real, the mechanism has to follow.

### 12. Drift checks have no referent — **ambiguity**

Line 86: "drift checks (LLM driven)". Drift between what and what?
Reasonable readings:

- spec vs implementation in the surrounding repo
- spec vs proposed_changes that were never revised
- current spec vs latest history version
- spec internal self-consistency (per the embedded guidelines'
  insistence on self-consistency)

Each requires different inputs and produces different outputs. Pick
which (probably all of them, separately named) and define the inputs.

---

## Significant Gaps That Should Be Closed Before Seeding

Lower severity than the above, but each is an obvious target for the
first round of `propose-change` if not closed in the seed.

### 13. Multi-specification handling — **incompleteness**

Line 10 mentions "multiple specifications in same project" but this
opens questions the proposal doesn't address: how commands target a
specific spec, how `doctor` scopes its checks, whether
`.livespec.jsonc` lists multiple `SPECIFICATION` roots or whether each
root has its own config. Either commit to a model or scope this out as
a v2 feature.

### 14. Out-of-band edits — **ambiguity**

If a human directly edits `spec.md` without going through
`propose-change` / `revise`, what happens? Doctor catches it via the
"diff between current and latest history version" check (line 81), but
the prompt-to-auto-create-a-proposed-change path is described in one
clause and needs more structure (what topic? what summary? does it
auto-revise?).

### 15. Critique authorship and topic collisions — **ambiguity**

Line 65: `critique <author>` defaults to "current AI model". How is the
current AI model detected (env var? skill metadata? prompt
interrogation)? What happens when two sequential critiques by the same
author are produced — do they collide on topic
`<author>-critique`, append, or version?

### 16. Per-template critique prompts — **incompleteness**

Line 110 says "Allow custom critique prompt" but the loading mechanism
and prompt-injection point are not specified. This is small but
load-bearing for the `critique` command.

### 17. Identity / git integration — **incompleteness**

Nothing in the proposal addresses:

- whether livespec writes git commits or only files
- whether `.livespec.jsonc` is expected to be committed
- the assumed branch model (main-only? PR-based?)
- conflict resolution when two proposed changes touch the same file

The proposal can punt on git integration entirely (treat as out of
scope) or take a position. It currently does neither.

### 18. Cross-file referencing within a single spec — **incompleteness**

The embedded guidelines' "How NLSpecs Relate to Each Other" section
addresses *between-spec* references, but the proposal's split into four
files inside one `SPECIFICATION` is *intra-spec*. Required:

- stable IDs / anchors for individual requirements
- referencing convention from `contracts.md` to `spec.md`
- rename / reflow rules

Without this, the partitioning into multiple files re-introduces the
drift the embedded guidelines warn against.

### 19. Definition of Done for v1 — **incompleteness**

The embedded guidelines insist a spec ends with a Definition of Done.
The proposal has none. What constitutes a shippable v1 of `livespec`?
Which sub-commands are MVP? Which template(s)? What test coverage? Any
performance or latency constraints?

### 20. Self-application — **incompleteness (intentional?)**

Implied throughout but not stated: this project, `livespec`, will
dogfood by having its own `SPECIFICATION/`. State this explicitly. It
sets the bootstrap order: writing the seed prompt → seeding own spec →
implementing skill from own spec.

---

## Smaller Issues, Inconsistencies, and Clean-Ups

- **Default template name mismatch.** `PROPOSAL.md` line 28:
  `default 'livespec'`. `goals-and-non-goals.md` §"Goals" 3 implies
  the same. Confirm and use one name consistently — and consider
  renaming, since `livespec/livespec` (template inside tool) is
  confusing.
- **Spec-vs-template ambiguity.** "OpenSpec-compatible structure"
  appears in both PROPOSAL and goals — pin which OpenSpec version /
  commit is the reference target.
- **`proposed_changes` versioning at write time vs revise time.**
  Filename `v001-proposed-change-<topic>.md` (line 38) implies a
  version number is in the filename when the proposal is created — but
  no version exists yet at that point (a version is only cut on
  `revise`). Either the filename uses the *target* (next) version, or
  versions are added at move-to-history time. Decide and document.
- **`scenarios.md` Gherkin convention drift risk.** Line 22 specifies
  "fenced `gherkin` code blocks" — pin the Gherkin dialect (Cucumber 6+
  vs SpecFlow vs plain text BDD) or accept that "render predictably in
  Markdown" is the only contract.
- **BCP 14 scope.** Line 19 says spec/contracts/constraints use BCP 14,
  but if a template chooses a single-file structure (which the goals
  doc allows), does BCP 14 still apply uniformly? State the rule
  template-independently.
- **`revise <freeform text>`.** What is the freeform text *for*?
  Override of acceptance decisions? An additional intent input applied
  alongside the proposals? Both? Currently both readings are valid.
- **README under `proposed_changes` and `history`.** Mandated but not
  specified. Likely auto-generated; needs a content contract.
- **`livespec-nlspec-spec.md` adaptation list.** The list of
  changes vs upstream is in `PROPOSAL.md` (lines 95–104) *and*
  effectively re-encoded in the file's own "Prior Art" header. Single
  source of truth (the guidelines file) with the proposal pointing at
  it would prevent drift.
- **Lifecycle diagram coverage.** `2026-04-19-nlspec-lifecycle-diagram.md`
  shows `seed → spec` and `revise → spec/history` but does *not* show
  `critique → proposed_changes` or `doctor` anywhere. The diagram is
  partial relative to the command set.
- **Documented deletion of `proposed_changes` after revise.** Line 75
  says "move proposed change to history" — confirm whether the working
  `proposed_changes/` directory is then empty or whether some
  proposals can persist across revisions.
- **Date/timezone normalization.** History dirs are versioned but no
  timestamps are mentioned. Acknowledgements may want to record
  `revised-at`. Unspecified.

---

## Application of the Recreatability Test

> *If the implementation were destroyed and only the specification
> remained, could a competent implementer faithfully recreate the
> system?*

Applied to the current proposal corpus:

- A competent implementer could recreate the **conceptual model**
  (loop, partitions, vocabulary).
- They could recreate the **directory shape** of a livespec-template
  project (with the gaps in §4 and §5 forcing guesses).
- They could **not** recreate the runtime, the schema, the
  acknowledgement format, the diff format, the doctor check
  inventory, the seed post-state, the test harness, the holdout
  mechanism, the progressive-disclosure mapping, or the OpenSpec
  template — without making decisions that two implementers would make
  differently.

Conclusion: **the proposal is sufficient as a design brief but
insufficient as a seed.** A `seed` invocation against this material
today would produce a `spec.md` heavy on motivation and light on
contract, with most of the "what must be true" living in the
implementer's head.

---

## Recommended Path to a Seedable Spec

Without prescribing the spec content itself, the minimum closure list
before running `seed`:

1. Decide and document the **runtime / packaging** (skill vs CLI vs
   MCP). One sentence is enough.
2. Define the **default `livespec` template** in full (file list,
   naming, headings, expected sections per file).
3. Publish the **`.livespec.jsonc` schema** with defaults and absence
   behavior.
4. Specify **versioning rules**: when, how, format.
5. Specify the **proposed-change** and **acknowledgement** file
   contracts.
6. Resolve the **`revise` accept/reject authority** question.
7. Enumerate **doctor static checks** and define exit-code semantics.
8. Define the **`seed` post-state** (file contents and idempotency).
9. Provide the **sub-command → guideline subset** mapping table for
   progressive disclosure.
10. Pull **testing approach** into its own section with file
    locations, runner, and the `section_drift_prevention` mechanism
    defined.
11. Write a **Definition of Done** for v1.
12. State explicitly that **livespec dogfoods itself** and name the
    bootstrap order.

Items 1, 2, 4, 5, 6, 8, and 11 are blockers. The rest can be filed as
the first batch of `propose-change`s after the seed.

---

## Notes on Material Outside `PROPOSAL.md`

- `goals-and-non-goals.md` is the strongest companion document.
  Promote large parts of it (especially "Why These Non-Goals Are
  Rational") into `spec.md` directly.
- `subdomains-and-unsolved-routing.md` should become a marked
  **Boundary Clarification** appendix in the seeded spec (per the
  guidelines' description of intentional ambiguity that "names its
  silence so it isn't mistaken for an omission").
- `prior-art.md` belongs in `SPECIFICATION/README.md` references or an
  appendix, not in the spec body — it documents *how the spec came to
  be*, which the guidelines explicitly route to ADRs / commit
  messages, not the present-tense spec.
- `2026-04-19-nlspec-lifecycle-diagram.md` and its legend should be
  embedded in `spec.md` once updated to cover `critique` and `doctor`.
- `2026-04-19-nlspec-terminology-and-structure-summary.md` is largely
  rationale; collapse to a glossary plus an appendix entry.
- `livespec-nlspec-spec.md` should remain a separate file
  (skill-loadable), referenced from `spec.md` but not duplicated into
  it.
- `nlspec-spec.md` (verbatim upstream) should move to a `prior-art/`
  subdirectory inside the seeded `SPECIFICATION/`, matching the
  reference in the adapted guidelines' header.
