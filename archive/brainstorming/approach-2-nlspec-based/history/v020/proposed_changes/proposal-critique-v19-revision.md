---
proposal: proposal-critique-v19.md
decision: accept
revised_at: 2026-04-25T09:30:00Z
author_human: thewoolleyman
author_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v19

## Provenance

- **Proposed change:** `proposal-critique-v19.md` — a four-issue
  critique pass over v019 `PROPOSAL.md` and the bootstrap plan,
  triggered by deliberate review of the plan with respect to the
  v018 Q1 template-sub-specification mechanism. Findings split:
  Q1 (PROPOSAL.md, critical) — `minimal` template sub-spec
  structural contradiction; Q2 (PROPOSAL.md, critical) —
  `livespec` template's seed prompt unconditionally emits
  `sub_specs[]`; Q3 (PLAN, medium) — Phase 3 sub-spec routing
  unexercised; Q4 (PLAN, medium) — Phase 6 widens only
  `prompts/seed.md`, leaving propose-change/revise/critique
  prompts thin for Phase 7's heaviest work.
- **Revised by:** thewoolleyman (human) in dialogue with
  Claude Opus 4.7 (1M context).
- **Revised at:** 2026-04-25 (UTC).
- **Scope:** v019 `PROPOSAL.md` §"SPECIFICATION directory
  structure — Template sub-specifications" (Q1 framing line +
  `minimal` sub-spec diagram), §"`seed`" pre-seed-template-
  selection paragraph (Q2 dialogue extension), §"`seed`"
  sub_specs-payload paragraph (Q2 user-answer-driven semantics),
  §"`seed`" wrapper file-shaping work item 5 (Q1 uniform README
  per sub-spec). PLAN-side ripples: Phase 2 (livespec template's
  minimum-viable `prompts/seed.md` includes the new pre-seed
  dialogue question; minimal sub-spec scaffolding mention
  unchanged at Phase 2 because Phase 6 produces the actual
  sub-spec contents), Phase 3 (widens all four livespec-template
  prompts to bootstrap-minimum + sub-spec-targeted propose-
  change/revise smoke cycle in exit criterion), Phase 6 (drops
  "follows minimal template's own convention — multi-file but
  with no sub-spec-root README and no per-version README"
  wording; minimal sub-spec ships uniform sub-spec-root README
  + per-version README; seed intent block explicitly answers
  "yes, ships templates" to the new pre-seed question), Version
  basis paragraph (v020 supersedes v019). Companion docs
  unchanged. `deferred-items.md` unchanged (frozen at v018; no
  entries open or close — `sub-spec-structural-formalization`
  body remains accurate under the v020 reframing).

## Pass framing

This pass was a **shipped-contract-defect critique** focused on
the v018 Q1 template-sub-specification mechanism's interaction
with the seed prompt's shipped behavior and the Phase 3 / Phase
6 / Phase 7 bootstrap sequence. The four findings divide cleanly
across PROPOSAL.md (Q1, Q2) and the PLAN (Q3, Q4) and are
mutually independent — each was decided separately at Option A,
the recommended disposition.

Q1 and Q2 close the two ambiguities that v018 Q1 left open in
the template-sub-specification mechanism: Q1 closes the
structural ambiguity (sub-spec layout no longer claims to follow
the described template's end-user convention), Q2 closes the
prompt-emission ambiguity (sub-spec emission becomes
user-driven via the pre-seed dialogue, not unconditionally
hard-coded into the `livespec` template's seed prompt).

Q3 and Q4 are PLAN-only quality fixes that surface at Phase
3 / Phase 7 boundaries. Both use the same wording pattern as
existing v019 PLAN content, so the authoring lift is small.

All four Q1-Q4 accepted at Option A, the recommended disposition.

## Governing principles reinforced

- **Sub-specs are livespec-internal artifacts, not exemplars of
  end-user template usage** (Q1). The v020 framing decouples
  sub-spec layout from the convention of the template the
  sub-spec describes; this resolves the previously implicit
  conflation that produced the v019 `minimal` sub-spec
  contradiction. Sub-spec layout becomes one rule
  (livespec multi-file, README always present) applied
  uniformly across all v1 sub-specs and naturally extending
  to v2+ sub-specs.

- **Shipped contracts must work for end users** (Q2). The
  `livespec` template's seed prompt is a SHIPPED artifact
  invoked by every end-user project that picks the `livespec`
  template. Hard-coding sub-spec emission into the prompt
  produced a defect in the shipped contract that Phase 6 hid
  by being self-applied. v020 makes sub-spec emission
  user-driven via the existing pre-seed dialogue, so the
  shipped prompt's behavior is correct for both end users and
  meta-projects.

- **Bootstrap-exception boundary stays unchanged** (all four).
  The v018 Q2 / v019 Q1 imperative-window-ends-at-first-seed
  boundary is not weakened by any of v020's changes. Q1 and Q2
  edit pre-Phase-6 content (PROPOSAL.md), Q3 edits Phase 3's
  exit criterion (within the imperative window), and Q4 widens
  Phase 3's prompt-authoring scope (also within the imperative
  window). Phase 7 remains pure dogfood with zero imperative
  landings.

- **Specify architecture, not mechanism** (Q4). Q4's prompt-
  widening at Phase 3 enumerates WHICH prompts need bootstrap-
  minimum authoring and WHAT each must accomplish at the
  consumer-phase boundary; it does NOT prescribe the prompt
  text or its internal structure. The implementer (or executor
  agent) retains authoring choice within the architectural
  constraint that each prompt be sufficient for its next
  consumer phase.

- **Honor the dogfood discipline strictly**. Q3 catches sub-
  spec routing bugs at Phase 3's smoke-test boundary, where
  recovery is imperative-landing (cheap), instead of Phase 7's
  dogfood boundary where recovery would require the broken
  governed loop. Q4 widens prompts at Phase 3 (imperative
  landing) so Phase 7's dogfooded cycles run on prompts that
  can do the job without needing in-phase prompt
  hand-widening.

## Decision: Q1 — Accept Option A

§"SPECIFICATION directory structure — Template sub-
specifications" framing line and `minimal` sub-spec diagram
amended; §"`seed`" wrapper file-shaping work item 5 amended for
uniform README capture per sub-spec. PLAN Phase 6 per-tree
description for the `minimal` sub-spec amended uniformly with
the `livespec` sub-spec.

### Framing line — amended text

```
Sub-specs are livespec-internal spec trees and use the
multi-file livespec layout uniformly. Sub-spec layout
decouples from the end-user-facing convention of the template
the sub-spec describes — a sub-spec governs the template's
behavior under livespec, not the shape of specs end users
author with that template. Every v1 sub-spec ships
`spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`,
a sub-spec-root `README.md`, `proposed_changes/`, and
`history/` (with per-version `README.md` snapshots), uniformly.
```

### `minimal` sub-spec diagram — amended

The `minimal` sub-spec stanza in §"Template sub-specifications"
gains a `README.md` line at the sub-spec root (the diagram
becomes structurally identical to the `livespec` sub-spec
stanza except for the spec-content-purpose annotations).

### §"`seed`" wrapper file-shaping item 5 — amended trailing
clauses

The clause "Each sub-spec tree follows its OWN template's
convention for whether a versioned `README.md` is captured: the
`livespec` sub-spec ships a sub-spec-root `README.md` + a
per-version README snapshot; the `minimal` sub-spec ships
neither (mirroring the minimal template's no-README convention)"
is replaced by:

```
Each sub-spec tree uniformly captures a sub-spec-root
`README.md` AND a per-version `README.md` snapshot. Sub-spec
README presence is decoupled from the described template's
end-user convention, per §"Template sub-specifications" — the
sub-spec README serves as orientation for the sub-spec's
livespec-managed content, not as an end-user-facing artifact.
```

### Plan-side companion edits (Q1)

- **Phase 6** — the `minimal` sub-spec per-tree post-seed
  contents block loses the "follows the `minimal` template's
  own convention — multi-file but with no sub-spec-root README
  and no per-version README" sentence. Both sub-specs
  described uniformly: multi-file (spec.md / contracts.md /
  constraints.md / scenarios.md), sub-spec-root README,
  per-version README, `proposed_changes/` (containing only the
  skill-owned README), `history/v001/` with frozen spec files
  (including README) + empty `proposed_changes/` subdir.

## Decision: Q2 — Accept Option A

§"`seed`" pre-seed-template-selection paragraph extended with
the new "ships own livespec templates" dialogue question;
sub_specs-payload paragraph rewritten for user-answer-driven
emission. Phases 2 / 3 / 6 of the PLAN updated accordingly.

### Pre-seed-template-selection paragraph — appended dialogue
question

After the existing template-selection question, the dialogue
adds (only when the selected template's seed prompt declares
sub-spec-emission capability — `livespec` is the v1 example):

```
"Does this project ship its own livespec templates that should
be governed by sub-spec trees under
`SPECIFICATION/templates/<name>/`? (default: no)"

If "yes", the dialogue then asks for the list of template
directory names under `.claude-plugin/specification-templates/`
(or equivalent project-specific location). The seed prompt
emits one `sub_specs[]` entry per named template.

If "no" (the default), the seed prompt emits `sub_specs: []`.
```

### Sub_specs-payload paragraph — amended text

The v019 paragraph "Sub-specs payload (v018 Q1)" describing
template-conditional emission ("When the active main-spec
template is `livespec` ..., the seed prompt emits sub-spec
payloads for BOTH built-in templates ...") is replaced by:

```
Sub-specs payload (v018 Q1; v020 Q2 user-answer-driven). The
`sub_specs` field is a list (possibly empty) of `SubSpecPayload`
entries. Sub-spec emission is driven by the user's answer to the
pre-seed "ships own livespec templates" dialogue question (see
§"`seed`" — pre-seed template selection). On "yes", the seed
prompt emits one `sub_specs[]` entry per template named in the
follow-on dialogue, each entry's `files[]` carrying the
sub-spec's spec-file content at
`SPECIFICATION/templates/<template_name>/<spec-file>`. On "no"
(the default), the seed prompt emits `sub_specs: []`. The
shipped seed prompt's behavior is uniform across templates and
does not assume any specific main-spec template name; the
per-template hard-coded dispatch in v019 is superseded by the
user-driven dialogue answer. Custom-template authors MAY
choose whether their seed prompts implement sub-spec-emission
capability per the user-provided-extensions minimal-
requirements principle.
```

### Plan-side companion edits (Q2)

- **Phase 2** — the `livespec` template's minimum-viable
  `prompts/seed.md` scaffold MUST include the new pre-seed
  dialogue question (it's load-bearing for Phase 6's seed
  needing to answer "yes"). The Phase 2 description gains
  one clause to that effect.
- **Phase 3** — `prompts/seed.md` bootstrap-minimum widening
  scope grows to include rigorous handling of the new
  dialogue question: the "yes" branch enumerates the user-
  named templates and emits sub_specs[]; the "no" branch
  emits `sub_specs: []`. (This widening is bundled with Q4's
  four-prompt widening below.)
- **Phase 6** — the seed intent block adds an explicit
  paragraph stating that the LLM driving the seed dialogue
  answers "yes" to the new pre-seed question and names
  `livespec` and `minimal` as the two shipped templates that
  receive sub-spec trees. This makes Phase 6's behavior
  externally identical to v019's behavior while routing
  through the new user-driven mechanism.

## Decision: Q3 — Accept Option A

PLAN Phase 3's exit-criterion smoke test grows by one
propose-change / revise cycle targeting the sub-spec tree.

### Phase 3 exit criterion — amended trailing block

The existing exit-criterion paragraph (which currently asserts
the throwaway-fixture round-trip files a propose-change /
revise against `<tmp>/SPECIFICATION` only) is amended to
append an additional cycle:

```
After the main-tree propose-change/revise cycle, the smoke
test files a SECOND propose-change/revise cycle targeting the
sub-spec tree:

  /livespec:propose-change --spec-target <tmp>/SPECIFICATION/templates/livespec
  /livespec:revise         --spec-target <tmp>/SPECIFICATION/templates/livespec

Confirm `<tmp>/SPECIFICATION/templates/livespec/history/v002/`
materializes with the expected `proposed_changes/` subdir
contents. Same code path as the main-tree smoke; different
`--spec-target` argument. Catches `--spec-target` sub-spec
routing bugs at the Phase 3 boundary, where recovery is
imperative-landing.
```

PROPOSAL.md is unchanged by Q3.

## Decision: Q4 — Accept Option A

PLAN Phase 3's "Required implementation surface" prompt-
authoring item grows from one (`prompts/seed.md`) to four,
mirroring the existing seed.md widening pattern.

### Phase 3 prompt-authoring surface — amended text

The v019 single-prompt item (`The `livespec` template's
`prompts/seed.md` — bootstrap-minimum authoring sufficient for
the Phase 6 seed LLM round-trip ...`) is replaced by a
four-prompt block:

```
The `livespec` template's prompts — bootstrap-minimum
authoring per prompt:

- `prompts/seed.md` — bootstrap-minimum authoring sufficient
  for the Phase 6 seed LLM round-trip to produce a schema-
  valid `seed_input.schema.json` payload covering the main
  spec AND, when the user answers "yes" to the pre-seed
  "ships own livespec templates" question (Phase 6 does),
  one `sub_specs[]` entry per named template. The prompt
  handles BOTH dialogue branches rigorously: "yes" → enumerate
  named templates and emit sub_specs[]; "no" → emit
  `sub_specs: []`. (Q2 + Q4 joint widening.)

- `prompts/propose-change.md` — bootstrap-minimum authoring
  sufficient for Phase 7's first dogfooded cycle to file
  full-fidelity propose-change files: full front-matter
  authoring, sub-spec routing via `--spec-target`, reserve-
  suffix awareness for `-critique` etc. The prompt MUST
  produce propose-change content of sufficient quality to
  drive the Phase 7 widening cycles for the propose-change
  command itself.

- `prompts/revise.md` — bootstrap-minimum authoring sufficient
  for Phase 7's first dogfooded cycle to drive per-proposal
  decisions, write paired revision files with full audit
  trails, and trigger version cuts. The prompt MUST produce
  revision content of sufficient quality to drive the Phase 7
  widening cycles for the revise command itself (including
  the cycles that author the final revise.md prompt).

- `prompts/critique.md` — bootstrap-minimum authoring sufficient
  for Phase 7's first dogfooded cycle to invoke critique-as-
  internal-delegation against either a main-spec or sub-spec
  target via `--spec-target`. The prompt MUST produce
  critique-driven propose-change content of sufficient quality
  to drive the Phase 7 widening cycles for the critique command
  itself.

The `minimal` template's prompts stay stubbed at this phase —
Phase 6 uses only the `livespec` template. All four `minimal`-
template prompts are Phase 7 work.
```

The Phase 6 / Phase 7 bodies and exit criteria are unchanged
by Q4 (same consumer-phase semantics; different upstream
prompt-quality scaffolding). PROPOSAL.md is unchanged by Q4.

## Outcome

PROPOSAL.md v020 supersedes v019 with amendments in §"Template
sub-specifications" (framing + `minimal` sub-spec diagram) and
§"`seed`" (pre-seed-template-selection paragraph + sub_specs-
payload paragraph + wrapper file-shaping item 5). PLAN
v020-companion edits cover Phase 0 (freeze at v020), the
Version basis paragraph, Phase 2 (Q2 dialogue scaffolding
mention), Phase 3 (Q3 sub-spec smoke + Q4 four-prompt widening),
and Phase 6 (Q1 minimal sub-spec uniformity + Q2 explicit "yes"
answer in seed intent). Companion docs unchanged.
`deferred-items.md` unchanged (frozen at v018).

`brainstorming/approach-2-nlspec-based/PROPOSAL.md` reflects
v020 after this revision lands. The frozen v020 snapshot lives
at `brainstorming/approach-2-nlspec-based/history/v020/`. The
v019 snapshot at `history/v019/` is unchanged.
