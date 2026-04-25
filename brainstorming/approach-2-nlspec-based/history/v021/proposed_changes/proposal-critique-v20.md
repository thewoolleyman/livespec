---
topic: proposal-critique-v20
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-25T10:30:00Z
---

# Proposal-critique v20

A targeted critique pass over v020 `PROPOSAL.md` and the
bootstrap plan
(`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`) surfacing
three findings — one PROPOSAL.md ↔ PLAN consistency defect
and two PLAN-level under-specifications — all rooted in the
v018 Q1 template-sub-specification mechanism's downstream
execution surfaces (doctor static-check applicability, the
v020 Q2 sub-spec-emission dialogue's SKILL.md prose surface,
and Phase 6's heading-coverage population mechanism).

This pass was triggered by a deliberate review of the
bootstrap plan with respect to the v018 Q1 / v020 Q1+Q2
sub-specification changes, focusing on what a literal
implementer hits at execution time. The findings are not
recreatability gaps in the PROPOSAL itself; they are
**logical inconsistencies between PLAN and PROPOSAL** plus
**plan-level under-specifications** that any literal
executor agent would surface at Phase 3 / Phase 6.

Findings in this pass:

- **Q1 (PROPOSAL.md + PLAN, blocking):** the doctor
  static-check applicability mechanism is described
  inconsistently across PROPOSAL.md (orchestrator-level
  dispatch with `(spec_root, template_name)` enumeration
  pairs) and PLAN (per-check `APPLIES_TO: frozenset[
  Literal["main", "sub-spec"]]` constants plus a
  runtime-skip-via-Finding inside `gherkin_blank_line_format`
  for the `minimal` sub-spec). The PLAN's runtime-skip
  approach additionally requires the check to know it's in
  the `minimal` sub-spec specifically, but the
  `DoctorContext` field set added in v018 Q1 only carries a
  binary `template_scope: Literal["main", "sub-spec"]` —
  there is no `template_name` field, so the runtime-skip
  cannot actually discriminate `livespec` sub-spec from
  `minimal` sub-spec. Two competing mechanisms; only one is
  fully wired.

- **Q2 (PLAN, blocking):** Phase 3's `seed/SKILL.md`
  bootstrap-prose bullet is described as covering "the
  pre-seed template dialogue" (singular). Per PROPOSAL.md
  §"`seed`" lines 1717-1759 (v014 N1 / v017 Q2 plus v020
  Q2), the pre-seed dialogue is a composite of THREE
  questions when the active template is `livespec`: (1)
  template selection; (2) the v020 Q2 "ships own livespec
  templates?" question, default "no"; (3) on "yes", a
  follow-up asking for the list of template directory names.
  Phase 6's seed intent block already presumes all three are
  wired up ("Answer with YES" / "name two: `livespec` and
  `minimal`"). A literal Phase 3 implementer reading "the
  pre-seed template dialogue" (singular) authors only the
  template-selection question and Phase 6's seed run has
  nothing to answer.

- **Q3 (PLAN, ambiguous):** Phase 6 says
  `tests/heading-coverage.json` "gets populated alongside
  the seeded spec" but does not specify the mechanism. The
  seed wrapper cannot reasonably touch a meta-test data file
  outside the spec tree (PROPOSAL.md §"`seed`" wrapper
  file-shaping work item list is an enumerated 6-step
  contract that does not include `tests/` writes; extending
  it would couple wrapper logic to the test-tree's
  existence/layout and would itself require a PROPOSAL.md
  change). Phase 6 is the imperative-window's closing point
  per the v018 Q2 bootstrap-exception clause and the only
  natural place where this one-time population can land.

## Proposal: Q1 — Doctor static-check applicability mechanism inconsistency between PROPOSAL.md and PLAN

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
  (§"doctor → Static-phase orchestrator", specifically the
  per-tree `DoctorContext` description at lines 2391-2401
  and the `DoctorContext` field-set summary at lines
  2453-2459)
- `brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`
  (Phase 3 — the `livespec/context.py` bullet, the
  `livespec/doctor/run_static.py` orchestrator bullet, the
  `livespec/doctor/static/__init__.py` registry bullet, and
  the `livespec/doctor/static/` per-check bullet describing
  the `APPLIES_TO` constant + `gherkin_blank_line_format`
  runtime skip; Phase 8 item 16 — the
  `sub-spec-structural-formalization` closure prose
  referencing `template_scope`)

`deferred-items.md` is NOT touched. The
`sub-spec-structural-formalization` entry's body describes
the mechanism at a level above the field-name choice
(template_scope vs. template_name) and does not assert
anything that conflicts with the resolution here.
deferred-items.md remains frozen at v018.

### Summary

**Failure mode: incompleteness (PLAN ↔ PROPOSAL
inconsistency at field-set boundary).** v018 Q1 introduced
two related mechanisms for per-tree applicability dispatch
in doctor's static phase, but the two source documents
encode different mechanisms:

- **PROPOSAL.md** describes orchestrator-level applicability
  dispatch (lines 2402-2416). The orchestrator enumerates
  `(spec_root, template_name)` pairs at startup (the main
  tree uses sentinel template-name `"main"`) and decides
  applicability per (template_name, check_slug) tuple. The
  v1 narrowings: `template-exists` and
  `template-files-present` are main-tree-only;
  `gherkin-blank-line-format` applies to the main spec tree
  when the active main template is `livespec`, AND to the
  `livespec` sub-spec, BUT NOT to the `minimal` sub-spec.
  Every other check applies uniformly. Implementation
  consequence: the orchestrator never invokes a check on a
  tree where the check does not apply.

- **PLAN** describes a two-layer mechanism (Phase 3's
  `livespec/doctor/static/` bullet). Each check module
  declares an `APPLIES_TO: frozenset[Literal["main",
  "sub-spec"]]` constant at module top. The orchestrator
  inspects this constant per-tree to decide invocation. For
  `gherkin_blank_line_format`, `APPLIES_TO = frozenset({
  "main", "sub-spec"})` (i.e., the orchestrator invokes it
  on every tree), and the check itself emits a `status:
  "skipped"` Finding "when the tree's template convention is
  the `minimal` template's no-Gherkin convention". The
  binary `template_scope: Literal["main", "sub-spec"]` field
  on `DoctorContext` (added in v018 Q1; described at PLAN
  Phase 3 line 575) is the dispatch input.

The two mechanisms are not equivalent. They diverge on:

1. **Where dispatch lives.** PROPOSAL.md: orchestrator.
   PLAN: split between orchestrator (binary structural
   narrowing via APPLIES_TO) and inside the check (template-
   convention-aware narrowing via runtime Finding skip).

2. **What dispatch input is needed.** PROPOSAL.md needs
   `template_name` (e.g., `"main"` / `"livespec"` /
   `"minimal"`) at the orchestrator. PLAN needs both
   `template_scope` (binary structural; consumed by
   APPLIES_TO check) and *implicitly* `template_name` (so
   the check can detect "minimal sub-spec" at runtime). PLAN
   adds only the binary `template_scope` to `DoctorContext`,
   leaving the runtime-skip mechanism without the
   discrimination input it needs.

The literal-implementer failure: an implementer following
PLAN authors `gherkin_blank_line_format`'s body trying to
detect "is this the minimal sub-spec?" from the only
available signal (`template_scope == "sub-spec"`), which
matches the `livespec` sub-spec equally and produces a
false-positive skip on the `livespec` sub-spec (or, if the
implementer reads PROPOSAL.md and back-ports `template_name`
ad-hoc, they introduce a dataclass field that is not
documented in either source). Either path produces an
implementation that does not match the documented contract.

The fix is to choose ONE mechanism and update both source
documents to match. Three options for resolution:

- **Option A (recommended): Orchestrator-only dispatch
  (PROPOSAL-aligned).** Drop `APPLIES_TO` from check modules
  entirely. Keep the registry shape at `(SLUG, run)` pairs
  (the v018 Q1 widening to a triple is reverted). Add
  `template_name: str` to `DoctorContext` (replacing the
  binary `template_scope`). The orchestrator owns a single
  applicability table indexed by (template_name, check_slug)
  derived from PROPOSAL.md §"Per-tree check applicability"
  rules. The check itself never emits a "skipped" Finding
  for applicability reasons (runtime-skip Findings are
  reserved for genuine content-aware skips like the
  bootstrap-lenience checks). This is the simplest model,
  has a single source of truth (PROPOSAL.md), keeps
  `DoctorContext` minimal, and aligns with PROPOSAL.md's
  existing prose.

  **PROPOSAL.md changes:** line 2398 — replace
  `template_scope: Literal["main", "sub-spec"]` with
  `template_name: str`. Lines 2453-2459 — add `template_name`
  to the enumerated fields gained by `DoctorContext` under
  v018 Q1 (alongside `config_load_status` and
  `template_load_status`). Lines 2402-2416 stay as-is (they
  already describe orchestrator-level dispatch).

  **PLAN changes:** Phase 3 — `livespec/context.py` bullet
  swaps `template_scope: Literal["main", "sub-spec"]` for
  `template_name: str`. `livespec/doctor/run_static.py`
  bullet documents the orchestrator-owned applicability
  table. `livespec/doctor/static/__init__.py` registry
  bullet reverts to `(SLUG, run)` pairs. `livespec/doctor/
  static/` per-check bullet drops the `APPLIES_TO` constant
  requirement and the runtime-skip-via-Finding paragraph for
  `gherkin_blank_line_format`; instead, the v1 applicability
  table is documented at the orchestrator level. Phase 8
  item 16 (`sub-spec-structural-formalization`) swaps
  `template_scope` reference to `template_name`.

- **Option B: Two-layer dispatch (PLAN-aligned + extended).**
  Keep `APPLIES_TO` binary on each check module (useful for
  the structural narrowing on `template_exists` /
  `template_files_present`). Add `template_name: str` to
  `DoctorContext` *alongside* `template_scope` so
  `gherkin_blank_line_format`'s runtime-skip can read
  `ctx.template_name == "minimal"`. PROPOSAL.md
  §"Per-tree check applicability" gains a sentence
  acknowledging that the `gherkin-blank-line-format` skip on
  `minimal` sub-spec is realized via runtime Finding-skip
  semantics, not orchestrator skip. Most invasive
  resolution; preserves both mechanisms. Listed for
  completeness.

- **Option C: Drop the gherkin minimal-exclusion entirely.**
  Apply `gherkin_blank_line_format` to every spec tree
  uniformly. The `minimal` sub-spec's `scenarios.md`
  receives gherkin-blank-line findings; users either fix or
  accept them. Simplest dispatch but conflicts with v020
  Q1's framing that sub-spec layout is decoupled from the
  described-template's end-user convention — minimal
  sub-spec scenarios.md still wants no-Gherkin per its
  content. Likely wrong for v1; listed for completeness.

### Recommendation

Option A. It is the minimal-change resolution that aligns
PLAN to PROPOSAL.md (already the more declarative source on
this mechanism), keeps `DoctorContext` minimal,
single-sources the applicability table at the orchestrator,
and drops the runtime-skip-via-Finding ambiguity entirely.
The PROPOSAL.md changes are surgical (two lines) and the
PLAN changes are localized to four bullets in Phase 3 plus a
field-name swap in Phase 8 item 16.

## Proposal: Q2 — Phase 3 `seed/SKILL.md` bootstrap prose under-specifies the v020 Q2 dialogue

### Target specification files

- `brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`
  (Phase 3 — the `seed/SKILL.md` bullet within the "Required
  implementation surface" list, currently describing
  bootstrap prose that covers "the pre-seed template
  dialogue" singular)

PROPOSAL.md is NOT touched by this finding. The
PROPOSAL-side description at §"`seed`" lines 1717-1759
already enumerates all three dialogue questions and their
gating; Phase 3 of PLAN simply needs to reflect that scope.
`deferred-items.md` is NOT touched.

### Summary

**Failure mode: incompleteness (under-specified
implementation surface).** Phase 3's "Required
implementation surface" list says:

```
seed/SKILL.md — bootstrap prose covering the pre-seed
template dialogue, the two-step resolve_template.py →
Read(prompts/seed.md) dispatch, payload assembly, wrapper
invocation, post-wrapper narration, and exit-code handling
with retry-on-4. ...
```

"The pre-seed template dialogue" is singular. PROPOSAL.md
§"`seed`" describes a composite three-question dialogue when
the active template is `livespec`:

1. **Template-selection question** (v014 N1 / v017 Q2). The
   user picks one of `livespec` (multi-file recommended
   default), `minimal` (single-file `SPECIFICATION.md`), or
   a custom template path.

2. **(v020 Q2) Sub-spec-emission question.** Asked only
   when the selected template's seed prompt declares
   sub-spec-emission capability (the `livespec` built-in is
   the v1 example): "Does this project ship its own livespec
   templates that should be governed by sub-spec trees under
   `SPECIFICATION/templates/<name>/`? (default: no)"

3. **(v020 Q2) Template-name follow-up.** Asked only on a
   "yes" answer to question 2. The user provides the list of
   template directory names under
   `.claude-plugin/specification-templates/` (or equivalent
   project-specific location) that should each receive a
   sub-spec tree.

Phase 6's seed intent block already presumes all three are
wired up (PLAN Phase 6 lines 994-1006: "Answer the
template-selection question with `livespec`. Answer the new
'Does this project ship its own livespec templates...?'
question with **YES**. When the dialogue follows up asking
which template directory names should receive sub-spec
trees, name **two**: `livespec` and `minimal`").

A literal Phase 3 implementer reading the singular phrasing
would author bootstrap SKILL.md prose covering only question
1 (template selection); questions 2 and 3 would silently be
absent. Phase 6's executor agent would then encounter a
dialogue that doesn't ask the questions Phase 6's intent
block tries to answer — the "Answer with YES" instruction
becomes inoperable.

The fix is plan-only: enumerate the three dialogue steps
explicitly in the Phase 3 SKILL.md bullet so a literal
implementer authors all three. PROPOSAL.md is unchanged
(already explicit at §"`seed`").

Two options for resolution:

- **Option A (recommended): Make Phase 3 SKILL.md prose
  explicit (PLAN-only).** Replace "the pre-seed template
  dialogue" in the Phase 3 `seed/SKILL.md` bullet with an
  enumerated three-step list: (1) v014 N1 / v017 Q2
  template-selection question; (2) v020 Q2 "ships own
  livespec templates?" question with default "no"; (3) on
  "yes", the follow-up asking for template directory names
  under `.claude-plugin/specification-templates/`. The
  remainder of the bullet (resolve_template.py dispatch,
  payload assembly, wrapper invocation, exit-code handling)
  is unchanged. PROPOSAL.md unchanged.

- **Option B: Move the sub-spec-emission dialogue into the
  template prompt instead.** Re-architect: have the
  `livespec` template's `prompts/seed.md` ask question 2 (and
  3) during its interview phase, leaving `seed/SKILL.md`
  narrow at question 1. This violates PROPOSAL.md §"`seed`"
  line 1719 ("seed's SKILL.md prose MUST prompt the user
  for template choice in dialogue BEFORE invoking the
  wrapper") and the sub-spec-emission gating note ("only
  when the selected template's seed prompt declares
  sub-spec-emission capability"). Requires PROPOSAL.md
  amendments. Not recommended.

- **Option C: Defer the sub-spec-emission dialogue to Phase
  7.** Phase 3's seed run does not exercise the dialogue;
  Phase 6's executor agent answers the seed prompt manually
  with a hand-authored payload that includes
  `sub_specs[]` entries. SKILL.md gets the dialogue only at
  Phase 7 widening. Risk: the v020 Q2 "user-driven, not
  template-conditional" semantic isn't exercised
  end-to-end until Phase 7. Plan would need a paragraph
  spelling this deferral out. Not recommended (it weakens
  the Phase 3 mechanical-achievability gate that v019 Q1
  introduced for exactly this kind of imperative-window
  surface).

### Recommendation

Option A. It is a minimal plan-side clarification that does
not touch PROPOSAL.md and aligns Phase 3's authoring scope
with what Phase 6 already presumes. Risk of regression is
zero (PROPOSAL.md remains the authority and is already
correct).

## Proposal: Q3 — Phase 6's `tests/heading-coverage.json` population mechanism is unspecified

### Target specification files

- `brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`
  (Phase 6 — the prose between "After seed, the working
  tree contains:" and "Running `/livespec:doctor` against
  this newly-seeded state passes its STATIC phase per-tree
  ...", specifically the sentence "Every `##` heading in
  every seeded spec file (main + both sub-specs) gets a
  corresponding entry in `tests/heading-coverage.json` ...")

PROPOSAL.md is NOT touched by this finding (the seed wrapper
contract at §"`seed`" file-shaping work items 1-6 is correct
as-is and should not be extended to touch
`tests/heading-coverage.json`). `deferred-items.md` is NOT
touched.

### Summary

**Failure mode: ambiguity (unspecified mechanism at
imperative-window boundary).** Phase 6 currently states:

```
Every ## heading in every seeded spec file (main + both
sub-specs) gets a corresponding entry in
tests/heading-coverage.json (each entry carries a
spec_root field naming its tree; entries with
test: "TODO" + non-empty reason are acceptable at this
point; Phase 7–8 work replaces TODOs with real test IDs).
```

This is a fact-statement about the post-Phase-6 state, not a
mechanism. Three places where the population could plausibly
land:

1. **The seed wrapper writes it.** Rejected: PROPOSAL.md
   §"`seed`" wrapper file-shaping work items 1-6 enumerate
   the wrapper's deterministic file-shaping responsibilities
   exhaustively (write `.livespec.jsonc`; write main-spec
   files; write sub-spec files; create main-spec
   `history/v001/`; create sub-spec `history/v001/` trees;
   auto-capture seed proposed-change). `tests/heading-
   coverage.json` is outside the spec tree (it lives at
   `<repo-root>/tests/`); coupling the wrapper to a meta-test
   data file would break the wrapper's separation of
   concerns and require a PROPOSAL.md amendment.

2. **A propose-change/revise cycle populates it.** Rejected
   for Phase 6: Phase 6 IS the seed step — the first
   propose-change cycle doesn't run until Phase 7 (per the
   v018 Q2 / v019 Q1 imperative-window-ends-at-first-seed
   boundary). Additionally, Phase 6's exit criterion already
   requires `just check` to pass (which includes
   `check-heading-coverage`), so the file must be populated
   BEFORE Phase 6 exits. Deferring to Phase 7 would break
   the Phase 6 exit gate.

3. **An imperative one-time executor step at Phase 6.** The
   plan's only remaining option: the executor agent
   (Phase 6's invocation of `/livespec:seed` is itself
   imperative within the bootstrap-exception window — see
   PROPOSAL.md §"Self-application" Bootstrap exception (v018
   Q2; v019 Q1 clarification): "the bootstrap ordering
   above (steps 1-4 ... ending with the first `livespec
   seed` invocation in step 3) lands imperatively") performs
   one additional one-time imperative step after seed
   succeeds: walks every `##` heading in main + both
   sub-specs and writes the corresponding entries to
   `tests/heading-coverage.json` with `spec_root` per tree
   and `test: "TODO"` + non-empty `reason` placeholders.
   From Phase 7 onward, every revise that adds / changes /
   removes `##` headings updates the file via the
   propose-change/revise audit trail.

The fix is plan-only: make option 3 explicit in the Phase 6
prose so the literal executor knows to perform the
imperative population step before claiming Phase 6's exit
criterion. PROPOSAL.md is unchanged.

Three options for resolution:

- **Option A (recommended): Imperative one-time executor
  step in Phase 6 (PLAN-only).** Add a sub-step to Phase 6:
  after the seed wrapper completes successfully, the
  executor agent walks every `##` heading in main + both
  sub-specs, writes entries to `tests/heading-coverage.json`
  (each carrying `spec_root` per tree + `test: "TODO"` +
  non-empty `reason` placeholders), and commits the file
  alongside the seed commit. Justified under v018 Q2's
  bootstrap-exception clause — Phase 6 is the imperative
  window's closing step, and this one-time meta-test data
  file population is a natural side-effect of the seed
  alongside the seed-revision file. From Phase 7 onward,
  every propose-change/revise that touches `##` headings
  updates the file via the governed loop. PROPOSAL.md
  unchanged.

- **Option B: Seed wrapper writes it.** Extend
  `bin/seed.py` to write `tests/heading-coverage.json` after
  writing spec files. Requires a PROPOSAL.md amendment to
  §"`seed`" wrapper file-shaping work items (adding a
  7th item) AND couples wrapper logic to the test tree's
  existence/layout. Not recommended.

- **Option C: Defer to a Phase 7 propose-change cycle.**
  Leave `tests/heading-coverage.json` empty `[]` after Phase
  6's seed; the FIRST Phase 7 propose-change against the
  main spec is a meta-revision whose `resulting_files[]`
  populates the heading-coverage entries for all three trees.
  Risk: Phase 6's exit criterion includes
  `check-heading-coverage` passing, which would FAIL on the
  empty array given populated spec trees. The plan's
  tolerance rule ("empty `[]` only pre-Phase-6") forbids
  this. Either adjust the tolerance rule or pick another
  option. Most disruptive; not recommended.

### Recommendation

Option A. Phase 6 already does multiple imperative things
(invokes seed; the seed wrapper auto-captures
`seed.md` + `seed-revision.md`; the executor verifies the
post-seed tree state). Adding one more imperative step
(populate `tests/heading-coverage.json`) within the
already-imperative Phase 6 closing window is the minimal
change. PROPOSAL.md is unchanged.

## Disposition summary

| # | Topic | Files touched | Recommended option |
|---|---|---|---|
| Q1 | Doctor static-check applicability mechanism (PROPOSAL ↔ PLAN inconsistency) | PROPOSAL.md (lines 2398, 2453-2459) + PLAN (Phase 3 four bullets, Phase 8 item 16) | A — Orchestrator-only dispatch |
| Q2 | Phase 3 `seed/SKILL.md` bootstrap prose under-specification | PLAN (Phase 3 single bullet) | A — Make Phase 3 SKILL.md prose explicit |
| Q3 | Phase 6 `tests/heading-coverage.json` population mechanism | PLAN (Phase 6 single sub-step) | A — Imperative one-time executor step |

`deferred-items.md` is unchanged. No deferred entries open
or close. No companion docs are touched. The
`sub-spec-structural-formalization` deferred entry's body
remains accurate under Q1's resolution (the field-name
choice is a layer below the entry's mechanism description).

The bootstrap-exception boundary (v018 Q2 / v019 Q1) is
unmoved: Q1 is a mechanism alignment within both pre- and
post-Phase-6 scope (orchestrator dispatch applies at every
phase that runs doctor); Q2 narrows Phase 3's SKILL.md
authoring scope (within the imperative window); Q3 makes a
Phase 6 imperative side-effect explicit (within the
imperative window's closing step). Phase 7 remains pure
dogfood with zero imperative landings.
