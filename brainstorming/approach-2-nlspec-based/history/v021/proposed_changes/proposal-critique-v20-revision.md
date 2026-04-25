---
proposal: proposal-critique-v20.md
decision: accept
revised_at: 2026-04-25T11:00:00Z
author_human: thewoolleyman
author_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v20

## Provenance

- **Proposed change:** `proposal-critique-v20.md` — a
  three-issue critique pass over v020 `PROPOSAL.md` and the
  bootstrap plan, triggered by a deliberate review of the
  plan with respect to the v018 Q1 / v020 Q1+Q2
  sub-specification changes. Findings split: Q1 (PROPOSAL.md
  + PLAN, blocking) — doctor static-check applicability
  mechanism inconsistency between PROPOSAL.md (orchestrator-
  level) and PLAN (per-check `APPLIES_TO` + runtime-skip
  Finding); Q2 (PLAN, blocking) — Phase 3 `seed/SKILL.md`
  bootstrap prose under-specifies the v020 Q2 three-question
  pre-seed dialogue; Q3 (PLAN, ambiguous) — Phase 6's
  `tests/heading-coverage.json` population mechanism is
  unspecified.
- **Revised by:** thewoolleyman (human) in dialogue with
  Claude Opus 4.7 (1M context).
- **Revised at:** 2026-04-25 (UTC).
- **Scope:** v020 `PROPOSAL.md` §"doctor → Static-phase
  orchestrator" `DoctorContext` field set (Q1 — replace
  `template_scope: Literal["main", "sub-spec"]` with
  `template_name: str`). PLAN-side ripples: Phase 3 (Q1 —
  `livespec/context.py` field swap, registry shape revert,
  drop `APPLIES_TO` constants and runtime-skip prose,
  document orchestrator-owned applicability table; Q2 —
  `seed/SKILL.md` bullet enumerates three dialogue steps
  explicitly), Phase 6 (Q3 — explicit imperative
  `tests/heading-coverage.json` population sub-step), Phase
  8 item 16 (Q1 — `template_scope` reference swapped to
  `template_name`), Version basis paragraph (v021 supersedes
  v020). Companion docs unchanged. `deferred-items.md`
  unchanged (frozen at v018; no entries open or close — the
  `sub-spec-structural-formalization` body remains accurate
  under the v021 mechanism choice).

## Pass framing

This pass was a **PROPOSAL ↔ PLAN consistency-defect
critique** focused on the v018 Q1 / v020 Q1+Q2 sub-
specification mechanism's downstream execution surfaces
(doctor static-check applicability, the v020 Q2 dialogue's
SKILL.md prose surface, and Phase 6's heading-coverage
population mechanism). The three findings divide cleanly
across PROPOSAL+PLAN (Q1) and PLAN-only (Q2, Q3) and are
mutually independent — each was decided separately at
Option A, the recommended disposition.

Q1 closes a PROPOSAL ↔ PLAN inconsistency that v018 Q1
introduced when adding `template_scope` to `DoctorContext`
and `APPLIES_TO` constants to check modules: the two
mechanisms could not coexist coherently with v020 Q1's
`minimal` sub-spec structural reframing, because the
binary `template_scope` cannot discriminate `livespec`
sub-spec from `minimal` sub-spec at runtime. v021 Q1
single-sources applicability dispatch at the orchestrator
(PROPOSAL-aligned) and removes the runtime-skip mechanism.

Q2 and Q3 are PLAN-only under-specifications surfaced when
the PLAN's Phase 3 / Phase 6 prose is read literally against
PROPOSAL.md's already-explicit dialogue and wrapper
contracts. Both fixes are localized text edits.

All three Q1-Q3 accepted at Option A, the recommended
disposition.

## Governing principles reinforced

- **Single source of truth for mechanism dispatch** (Q1).
  The v018 Q1 widening accidentally produced two competing
  mechanisms (orchestrator-level + per-check) for the same
  applicability decision, with the PLAN-side mechanism
  missing its required dispatch input. v021 Q1 collapses to
  one source (PROPOSAL.md's orchestrator-level dispatch),
  drops the per-check `APPLIES_TO` constant, and aligns the
  `DoctorContext` field set to the orchestrator-level model.
  Both source documents agree on one mechanism after this
  revision.

- **Plan must reflect the full PROPOSAL surface a literal
  implementer hits** (Q2, Q3). The PLAN's job is to brief a
  literal executor agent on what to land at each phase. When
  PROPOSAL.md describes a three-question dialogue but PLAN
  describes "the pre-seed template dialogue" (singular), the
  executor authors only the singular interpretation. When
  PROPOSAL.md does not assign meta-test-file population to
  the wrapper but PLAN states the file gets populated
  without naming the actor, the executor has no instruction
  to follow. v021 Q2 and Q3 close both gaps with localized
  PLAN-text edits.

- **Bootstrap-exception boundary stays unchanged** (all
  three). The v018 Q2 / v019 Q1 imperative-window-ends-at-
  first-seed boundary is not weakened by any of v021's
  changes. Q1 is a mechanism alignment that applies at every
  phase running doctor (pre- and post-Phase-6); Q2 narrows
  Phase 3's SKILL.md authoring scope (within the imperative
  window); Q3 names an explicit Phase 6 imperative side-
  effect (within the imperative window's closing step).
  Phase 7 remains pure dogfood with zero imperative
  landings.

- **Specify architecture, not mechanism** (Q1, Q3). v021 Q1
  documents the orchestrator-owned applicability table at
  the level of "(template_name, check_slug) → applicable"
  semantics, not at the level of how the orchestrator
  internally encodes the table (frozenset / dict /
  match-statement is implementer choice). v021 Q3 names the
  "imperative one-time executor step" at the actor /
  responsibility level, not at the level of what code path
  the executor uses to walk the headings. The implementer
  retains authoring choice within the architectural
  constraint.

- **Honor the PROPOSAL/PLAN division of authority** (Q2).
  PROPOSAL.md §"`seed`" already enumerates the three
  dialogue questions and their gating; PLAN does not need to
  re-specify them — only to point at the right scope. v021
  Q2 enumerates the three dialogue steps in the Phase 3
  bullet without restating PROPOSAL.md content; PROPOSAL.md
  remains the sole authority on dialogue semantics.

## Decision: Q1 — Accept Option A

§"doctor → Static-phase orchestrator" `DoctorContext` field
set amended: `template_scope: Literal["main", "sub-spec"]`
is replaced by `template_name: str`. PLAN Phase 3 four
bullets amended; PLAN Phase 8 item 16 reference swapped.

### PROPOSAL.md — line 2398 amended

Replace:

```
per-tree `DoctorContext` (with `spec_root` set to the tree's
root and a new `template_scope: Literal["main", "sub-spec"]`
field discriminating main-spec from sub-spec checks for
per-tree applicability dispatch) and runs the applicable
check subset.
```

with:

```
per-tree `DoctorContext` (with `spec_root` set to the tree's
root and a new `template_name: str` field carrying the
tree's template-name marker — `"main"` for the main spec
tree, or the sub-spec directory name (e.g. `"livespec"`,
`"minimal"`) for each sub-spec tree — used for per-tree
applicability dispatch) and runs the applicable check
subset.
```

### PROPOSAL.md — lines 2453-2459 amended

The existing v014 N3 paragraph enumerating the two fields
gained by `DoctorContext` (`config_load_status`,
`template_load_status`) is extended to enumerate the v018 Q1
addition under v021's resolution:

```
`DoctorContext` (see `python-skill-script-style-requirements.md`
§"Context dataclasses") gains the following fields:

- `config_load_status: Literal["ok", "absent", "malformed",
  "schema_invalid"]` (v014 N3)
- `template_load_status: Literal["ok", "absent", "malformed",
  "schema_invalid"]` (v014 N3)
- `template_name: str` (v018 Q1, field-name finalized in
  v021 Q1) — `"main"` sentinel for the main spec tree, or
  the sub-spec directory name for each sub-spec tree;
  consumed by the orchestrator-owned applicability table
  for per-tree check dispatch.
```

The semantics paragraph for `config_load_status` /
`template_load_status` (currently following the field
listing) is unchanged.

### PROPOSAL.md — lines 2402-2416 unchanged

The existing per-tree check applicability list
(`gherkin-blank-line-format` applies to main+livespec but
not minimal; `template-exists` and `template-files-present`
are main-tree-only; every other check applies uniformly) is
unchanged. With v021 Q1 it now reads as the authoritative
applicability table consumed by the orchestrator (no
runtime-skip semantics).

### PLAN — Phase 3 `livespec/context.py` bullet amended

Replace:

```
- `livespec/context.py` — `DoctorContext`, `SeedContext`, and
  the other context dataclasses with the exact fields named in
  the style doc §"Context dataclasses", including v014 N3's
  `config_load_status` / `template_load_status` AND v018 Q1's
  `template_scope: Literal["main", "sub-spec"]` (used by
  `run_static.py` for per-tree applicability dispatch — see the
  `APPLIES_TO` constant rule below in this phase's
  `livespec/doctor/static/` enumeration).
```

with:

```
- `livespec/context.py` — `DoctorContext`, `SeedContext`, and
  the other context dataclasses with the exact fields named in
  the style doc §"Context dataclasses", including v014 N3's
  `config_load_status` / `template_load_status` AND v018 Q1's
  `template_name: str` (`"main"` sentinel for the main spec
  tree, or the sub-spec directory name for each sub-spec tree;
  consumed by `run_static.py`'s orchestrator-owned applicability
  table — see the orchestrator bullet below in this phase's
  `livespec/doctor/run_static.py` enumeration).
```

### PLAN — Phase 3 `livespec/doctor/run_static.py` bullet amended

Replace:

```
- `livespec/doctor/run_static.py` — orchestrator per PROPOSAL.md
  §"Static-phase structure" + v014 N3 bootstrap lenience + v018
  Q1 per-tree iteration. The orchestrator enumerates
  `(spec_root, template_name)` pairs at startup (main tree
  first; then each sub-spec tree under
  `<main-spec-root>/templates/<sub-name>/`); per pair it builds
  a per-tree `DoctorContext` (with `template_scope` set
  appropriately) and runs the applicable check subset.
```

with:

```
- `livespec/doctor/run_static.py` — orchestrator per PROPOSAL.md
  §"Static-phase structure" + v014 N3 bootstrap lenience + v018
  Q1 per-tree iteration (applicability dispatch finalized in
  v021 Q1). The orchestrator enumerates
  `(spec_root, template_name)` pairs at startup (main tree
  first with template-name sentinel `"main"`; then each
  sub-spec tree under `<main-spec-root>/templates/<sub-name>/`
  with template-name set to the sub-spec directory name); per
  pair it builds a per-tree `DoctorContext` (with `template_name`
  set appropriately) and runs the applicable check subset
  decided by the orchestrator-owned applicability table:

    - `template_exists` and `template_files_present` invoked
      only when `template_name == "main"` (sub-spec trees are
      spec trees, not template payloads).
    - `gherkin_blank_line_format` invoked when
      (`template_name == "main"` AND main `.livespec.jsonc.template
      == "livespec"`) OR `template_name == "livespec"`; never
      invoked when `template_name == "minimal"` (matches
      PROPOSAL.md §"Per-tree check applicability"; the
      `minimal` sub-spec's `scenarios.md` follows the minimal
      template's no-Gherkin convention).
    - All other checks invoked uniformly per tree.

  The orchestrator never asks a check whether it applies; the
  table is the single source. Checks themselves emit no
  applicability-driven `skipped` Findings (skipped status is
  reserved for the v014 N3 bootstrap-lenience checks and
  semantically equivalent content-aware skips codified in the
  `static-check-semantics` deferred entry).
```

### PLAN — Phase 3 `livespec/doctor/static/__init__.py` bullet amended

Replace:

```
- `livespec/doctor/static/__init__.py` — static registry. Per
  v018 Q1, each entry exposes the triple `(SLUG, run, APPLIES_TO)`
  (extending the prior `(SLUG, run)` shape).
```

with:

```
- `livespec/doctor/static/__init__.py` — static registry.
  Each entry exposes the pair `(SLUG, run)` (the v018 Q1
  triple shape with `APPLIES_TO` is reverted in v021 Q1; the
  orchestrator now owns the applicability table).
```

### PLAN — Phase 3 `livespec/doctor/static/` per-check bullet amended

Replace:

```
- `livespec/doctor/static/` — each check module declares an
  `APPLIES_TO: frozenset[Literal["main", "sub-spec"]]`
  module-top constant alongside `SLUG` and `run`. The
  orchestrator inspects this constant per-tree to decide
  whether to invoke the check. Default value: `frozenset({
  "main", "sub-spec"})` (the check runs on every tree). The
  three v1 narrowings:
  - `template_exists`: `APPLIES_TO = frozenset({"main"})`
    (sub-spec trees are spec trees, not template payloads).
  - `template_files_present`: `APPLIES_TO = frozenset({
    "main"})` (same reason).
  - `gherkin_blank_line_format`: `APPLIES_TO = frozenset({
    "main", "sub-spec"})` BUT the check itself emits a
    `status: "skipped"` Finding when the tree's template
    convention is the `minimal` template's no-Gherkin
    convention (the conditional applicability is content-
    aware; runtime skip is cleaner than a more elaborate
    constant). The exact dispatch is codified in
    `static-check-semantics`.
```

with:

```
- `livespec/doctor/static/` — each check module exposes
  `SLUG` and `run` only (no `APPLIES_TO` constant per v021 Q1
  — applicability is the orchestrator's responsibility, not
  the check's). The v1 applicability narrowings are
  documented at the orchestrator level above; checks
  themselves remain template-name-agnostic. Bootstrap-
  lenience semantics (v014 N3) and any other content-aware
  `skipped` semantics remain inside individual check modules
  per the `static-check-semantics` deferred entry.
```

### PLAN — Phase 8 item 16 reference amended

Replace:

```
materialized across Phase 3 (seed's multi-tree
file-shaping work; `--spec-target` flag implementation on
propose-change / critique / revise; `SubSpecPayload`
schema + dataclass + validator; `DoctorContext`
`template_scope` field), Phase 6 (sub-spec tree seeding
```

with:

```
materialized across Phase 3 (seed's multi-tree
file-shaping work; `--spec-target` flag implementation on
propose-change / critique / revise; `SubSpecPayload`
schema + dataclass + validator; `DoctorContext`
`template_name` field per v021 Q1), Phase 6 (sub-spec tree seeding
```

## Decision: Q2 — Accept Option A

PLAN Phase 3 `seed/SKILL.md` bullet amended to enumerate the
three pre-seed dialogue steps explicitly. PROPOSAL.md
unchanged.

### PLAN — Phase 3 `seed/SKILL.md` bullet amended

Replace:

```
- `seed/SKILL.md` — **bootstrap prose** covering the pre-seed
  template dialogue, the two-step `resolve_template.py` →
  Read(`prompts/seed.md`) dispatch, payload assembly, wrapper
  invocation, post-wrapper narration, and exit-code handling
  with retry-on-4. This is intentionally narrower than the full
  per-sub-command body structure in PROPOSAL.md; Phase 7 brings
  it to final per `skill-md-prose-authoring`.
```

with:

```
- `seed/SKILL.md` — **bootstrap prose** covering the pre-seed
  dialogue, the two-step `resolve_template.py` →
  Read(`prompts/seed.md`) dispatch, payload assembly, wrapper
  invocation, post-wrapper narration, and exit-code handling
  with retry-on-4. The pre-seed dialogue per PROPOSAL.md
  §"`seed`" lines 1717-1759 has THREE questions when the
  selected template is `livespec`, all of which the bootstrap
  prose MUST author:

    1. **Template-selection question** (v014 N1 / v017 Q2) —
       options: `livespec` (multi-file recommended default),
       `minimal` (single-file `SPECIFICATION.md`), or a custom
       template path.
    2. **(v020 Q2) Sub-spec-emission question** (asked only
       when the selected template's seed prompt declares
       sub-spec-emission capability — the `livespec` built-in
       is the v1 example): "Does this project ship its own
       livespec templates that should be governed by sub-spec
       trees under `SPECIFICATION/templates/<name>/`? (default:
       no)"
    3. **(v020 Q2) Template-name follow-up** (asked only on a
       "yes" answer to question 2): the user provides the list
       of template directory names under
       `.claude-plugin/specification-templates/` (or equivalent
       project-specific location) that should each receive a
       sub-spec tree.

  This is intentionally narrower than the full per-sub-command
  body structure in PROPOSAL.md; Phase 7 brings it to final per
  `skill-md-prose-authoring`.
```

PROPOSAL.md is unchanged by Q2.

## Decision: Q3 — Accept Option A

PLAN Phase 6 amended to add an explicit imperative
sub-step populating `tests/heading-coverage.json` after seed
succeeds. PROPOSAL.md unchanged.

### PLAN — Phase 6 amended

The current `tests/heading-coverage.json` paragraph in Phase
6 (which currently reads as a fact-statement about the post-
seed state):

```
Every `##` heading in every seeded spec file (main + both
sub-specs) gets a corresponding entry in
`tests/heading-coverage.json` (each entry carries a
`spec_root` field naming its tree; entries with
`test: "TODO"` + non-empty `reason` are acceptable at this
point; Phase 7–8 work replaces TODOs with real test IDs).
```

is replaced by an explicit imperative-step description:

```
**Imperative one-time heading-coverage population.** After
the seed wrapper completes successfully and BEFORE Phase 6's
exit criterion is asserted, the executor agent performs one
additional imperative step: walk every `##` heading in every
seeded spec file (main + both sub-specs) and write a
corresponding entry to `tests/heading-coverage.json`. Each
entry carries a `spec_root` field naming its tree; entries
land with `test: "TODO"` + non-empty `reason` placeholders at
this point (Phase 7–8 work replaces TODOs with real test IDs
via the governed loop). The file is committed alongside the
Phase 6 seed commit.

This step is permitted under PROPOSAL.md §"Self-application"
Bootstrap exception (v018 Q2; v019 Q1 clarification) — Phase
6 is the imperative window's closing step, and meta-test
data file population is a one-time bootstrap side-effect
that does not belong in the seed wrapper's deterministic
file-shaping contract (PROPOSAL.md §"`seed`" wrapper file-
shaping work items 1-6 are unchanged). From Phase 7 onward,
every propose-change/revise that adds / changes / removes
`##` headings updates `tests/heading-coverage.json` via the
governed loop's `resulting_files[]` mechanism.
```

PROPOSAL.md is unchanged by Q3.

## Outcome

PROPOSAL.md v021 supersedes v020 with one surgical amendment
in §"doctor → Static-phase orchestrator" (Q1 —
`DoctorContext` field-set finalization: `template_scope` →
`template_name`). PLAN v021-companion edits cover the
Version basis paragraph (v021 supersedes v020), Phase 0
(freeze at v021), Phase 3 (Q1 four-bullet alignment to
orchestrator-owned applicability table; Q2 explicit
three-question dialogue enumeration), Phase 6 (Q3 explicit
imperative heading-coverage population sub-step), Phase 8
item 16 (Q1 `template_scope` → `template_name` reference
swap), and the execution prompt's "v020 / v021" references.
Companion docs unchanged. `deferred-items.md` unchanged
(frozen at v018; the `sub-spec-structural-formalization`
entry's body remains accurate under the v021 mechanism
choice — the field-name finalization is below the entry's
mechanism description level).

`brainstorming/approach-2-nlspec-based/PROPOSAL.md` reflects
v021 after this revision lands. The frozen v021 snapshot
lives at `brainstorming/approach-2-nlspec-based/history/v021/`.
The v020 snapshot at `history/v020/` is unchanged.
