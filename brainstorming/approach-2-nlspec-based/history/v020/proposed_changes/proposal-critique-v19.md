---
topic: proposal-critique-v19
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-25T09:00:00Z
---

# Proposal-critique v19

A targeted critique pass over v019 `PROPOSAL.md` and the
bootstrap plan
(`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`) surfacing
four findings — two PROPOSAL.md-level and two PLAN-level —
all rooted in the v018 Q1 template-sub-specification mechanism
and its interaction with both the seed prompt's shipped
contract and the Phase 3 / Phase 6 / Phase 7 bootstrap
sequence.

This pass was triggered by a deliberate review of the bootstrap
plan with respect to the latest v018 Q1 changes (template
sub-specifications under `SPECIFICATION/templates/<name>/`).
The findings are not recreatability gaps; they are
**self-contained logical contradictions and shipped-contract
defects** that any literal implementer hits at execution time
and that Phase 6 would migrate verbatim into
`SPECIFICATION/spec.md`, poisoning the seeded oracle.

Findings in this pass:

- **Q1 (PROPOSAL.md, critical):** the `minimal` template's
  sub-spec structure is described as multi-file (spec.md /
  contracts.md / constraints.md / scenarios.md) under a framing
  ("structurally identical to a main spec tree per the
  template's own conventions") that is true for the `livespec`
  sub-spec and false for the `minimal` sub-spec, whose own
  template convention is single-file (`SPECIFICATION.md` at
  `spec_root: "./"`). The framing and the diagram contradict
  each other.

- **Q2 (PROPOSAL.md, critical):** the `livespec` template's
  shipped seed prompt unconditionally emits `sub_specs[]` for
  both built-in templates whenever the active main-spec
  template is `livespec`. End-user projects that pick the
  `livespec` template for their own specs would receive
  spurious `SPECIFICATION/templates/livespec/` and
  `SPECIFICATION/templates/minimal/` trees they did not ask
  for and have no use for. The prompt has no signal to
  distinguish "livespec-the-project bootstrapping itself" from
  "an end-user project using the livespec template."

- **Q3 (PLAN, medium):** Phase 3's exit-criterion smoke test
  files a propose-change / revise cycle against
  `<tmp>/SPECIFICATION` (the main tree) only. Sub-spec routing
  via `--spec-target SPECIFICATION/templates/livespec` is not
  exercised end-to-end before Phase 7, where every template's
  content is generated through that exact code path. A bug in
  `--spec-target` sub-spec routing escapes Phase 3's narrow
  gate.

- **Q4 (PLAN, medium):** Phase 3 widens only `prompts/seed.md`
  on the `livespec` template to "bootstrap-minimum" authoring;
  the other three (`propose-change.md`, `revise.md`,
  `critique.md`) stay at Phase 2's "minimum-viable" level.
  Phase 7's first dogfooded cycle uses those three minimum
  prompts to author the FULL final prompt content for the
  `livespec` template — including (recursively) authoring the
  very prompts being used. Sub-par prompt scaffolding
  propagates into the shipped final prompts.

## Proposal: Q1 — `minimal` template sub-spec structure contradicts the framing

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
  (§"SPECIFICATION directory structure — Template
  sub-specifications", specifically the framing line "Sub-spec
  tree shape (structurally identical to a main spec tree per
  the template's own conventions):" and the `minimal` sub-spec
  diagram beneath it)
- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
  (§"`seed`" wrapper file-shaping work item 5, specifically
  the clause "Each sub-spec tree follows its OWN template's
  convention for whether a versioned `README.md` is captured")
- `brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`
  (Phase 6 — the per-tree post-seed contents description for
  the `minimal` sub-spec, currently "follows the `minimal`
  template's own convention — multi-file but with no
  sub-spec-root README and no per-version README")

`deferred-items.md` is NOT touched by this finding. The
`sub-spec-structural-formalization` entry's body describes the
mechanism (per-tree iteration, `--spec-target` flag, schema
extension, heading-coverage `spec_root` extension) and does
not assert anything that conflicts with the reframing here.
deferred-items.md remains frozen at v018.

### Summary

**Failure mode: incompleteness (logical contradiction at
boundary).** §"Template sub-specifications" frames the sub-spec
tree shape as *"structurally identical to a main spec tree per
the template's own conventions."* That framing holds for the
`livespec` sub-spec, whose diagram shows the multi-file layout
matching the `livespec` template's own multi-file convention.
It is false for the `minimal` sub-spec: the diagram in the
same section shows multi-file (spec.md, contracts.md,
constraints.md, scenarios.md) while the `minimal` template's
own convention is single-file (`SPECIFICATION.md` at
`spec_root: "./"`, per §"Built-in template: `minimal`"). The
PLAN Phase 6 description carries the same contradiction even
more starkly — its prose reads "follows the `minimal`
template's own convention — multi-file but with no
sub-spec-root README and no per-version README", which
self-contradicts within a single sentence: minimal's own
convention is single-file, not multi-file.

A literal implementer reaches Phase 6 with two incompatible
instructions: produce a multi-file sub-spec for `minimal` per
the diagram, OR produce a single-file sub-spec per the framing.
Either choice falsifies the other authority. Phase 6 then
migrates §"Template sub-specifications" verbatim into
`SPECIFICATION/contracts.md`, baking the contradiction into
the seeded oracle.

The contradiction is not surface wording — it reflects an
unstated design choice. Sub-specs of livespec-shipped
templates serve a different purpose than the templates they
describe: a sub-spec is a livespec-managed spec tree governing
the template's behavior, not an exemplar of how end users
write specs with that template. Because livespec-the-project
uses the `livespec` template for its own specs, livespec's
multi-file layout is the natural structure for any sub-spec
livespec governs. The `minimal` template, viewed as a livespec
sub-spec, ought to use the same multi-file layout — not its
own end-user-facing single-file convention.

### Failure mode

Incompleteness — logical contradiction at boundary
(framing-vs-diagram, mirrored into PLAN Phase 6).

### Resolution options

**Option A (recommended): Reframe sub-specs as livespec-internal
artifacts that always use the multi-file livespec layout,
regardless of the template they describe.**

§"Template sub-specifications" drops the "structurally
identical to a main spec tree per the template's own
conventions" framing and replaces it with: "Sub-specs are
livespec-internal spec trees and use the multi-file livespec
layout uniformly. The sub-spec layout decouples from the
end-user-facing convention of the template the sub-spec
describes — a sub-spec governs the template's behavior, not
the shape of specs end users author with that template."

The `minimal` sub-spec diagram stays multi-file (spec.md,
contracts.md, constraints.md, scenarios.md) and is no longer
in tension with the framing. The README question (whether the
sub-spec ships a sub-spec-root README and per-version README)
is resolved uniformly across all sub-specs in concert with this
option: README-always-present, mirroring livespec's main-spec
convention. The `minimal` sub-spec gains a sub-spec-root
`README.md` and a per-version `README.md` it did not have in
v019.

PLAN Phase 6's per-tree description for the `minimal` sub-spec
loses the self-contradicting "follows the `minimal` template's
own convention — multi-file but with no sub-spec-root README"
sentence. Both sub-specs are described uniformly: multi-file,
sub-spec-root README, per-version README, `proposed_changes/`,
`history/v001/` with frozen spec files + empty
`proposed_changes/`.

PROPOSAL.md §"`seed`" wrapper file-shaping work item 5 (which
currently says "Each sub-spec tree follows its OWN template's
convention for whether a versioned `README.md` is captured")
is amended to: "Each sub-spec tree uniformly captures a
sub-spec-root `README.md` AND a per-version `README.md` —
sub-spec README presence is decoupled from the described
template's end-user convention, per §"Template
sub-specifications"."

Pros:
- Resolves the contradiction without re-litigating
  multi-file-vs-single-file as a per-template policy.
- Sub-spec layout becomes a single, simple rule: livespec
  multi-file, README always present.
- The per-template asymmetry vanishes — every sub-spec under
  `SPECIFICATION/templates/<name>/` has the same shape,
  simplifying doctor-static per-tree iteration, the
  prompt-QA harness, and Phase 7 / Phase 8 handling.
- Honors the `feedback_brainstorming_no_history_obsession`
  preference: prefer clean breaks over backwards-compatible
  options.

Cons:
- The `minimal` sub-spec's structure no longer "looks like"
  the minimal template's end-user output. This is intentional
  but worth surfacing — readers who conflate "sub-spec for
  template X" with "exemplar usage of template X" will need
  the framing change to recalibrate.
- The minimal sub-spec gains a README it did not have in v019.

**Option B: Make the `minimal` sub-spec actually single-file.**

§"Template sub-specifications" preserves the "structurally
identical to a main spec tree per the template's own
conventions" framing. The `minimal` sub-spec diagram is
amended to a single file: `SPECIFICATION/templates/minimal/
SPECIFICATION.md` (no `spec.md` / `contracts.md` /
`constraints.md` / `scenarios.md` split), plus
`proposed_changes/` and `history/`. The minimal sub-spec's
content (template positioning, prompt interview intents,
delimiter-comment format contract, single-file constraint)
collapses into one file with internal headings.

Pros:
- Preserves the "sub-spec follows template convention" framing
  literally.

Cons:
- Loses the four-file separation (spec / contracts /
  constraints / scenarios) for content that benefits from it
  — the delimiter-comment format contract is naturally a
  contracts.md concern and gets buried inside a single-file
  spec.
- doctor-static per-tree iteration becomes asymmetric across
  sub-spec trees: one sub-spec has four spec files to iterate
  over, the other has one.
- The Phase 7 prompt-QA "Per-prompt semantic-property
  catalogue" subsection (currently in each sub-spec's
  contracts.md) has nowhere to go in a single-file minimal
  sub-spec.
- Phase 6's seed intent block becomes more complex (different
  file lists per sub-spec).

**Option C: Keep both and document the asymmetry.**

§"Template sub-specifications" amends the framing to: "Sub-spec
tree shape — structurally identical to a main spec tree per
the template's own conventions, EXCEPT that the inner spec-file
split is uniformly multi-file regardless of the template's
single-vs-multi-file convention." The `minimal` sub-spec
diagram stays as it is (multi-file, no README); the wording
acknowledges the partial inheritance.

Pros:
- Minimal diff to v019 PROPOSAL.md and PLAN.

Cons:
- The "EXCEPT" clause is a verbal patch on a structural
  contradiction; it documents the asymmetry without resolving
  it.
- Future readers and v2+ template authors face the same
  "which conventions do sub-specs inherit?" question Option A
  cleanly closes.
- The README asymmetry stays per-template, so two unrelated
  per-template asymmetries (multi-file inheritance, README
  inheritance) coexist with no unifying rule.

### Recommended disposition

**Accept Option A.** The framing change "sub-specs are
livespec-internal artifacts" is the smallest substantive
reframing that resolves the contradiction at its root rather
than patching the surface text. Sub-spec layout becomes a
single rule (multi-file livespec layout, README always
present) that applies uniformly to all v1 sub-specs and
extends naturally to v2+ sub-specs (whether livespec-shipped
or user-template-authored).

Concretely, v020 amends:

- §"Template sub-specifications" framing line and `minimal`
  sub-spec diagram (README added at sub-spec root; multi-file
  layout reframed as livespec-internal default).
- §"`seed`" wrapper file-shaping item 5 (uniform README
  capture per sub-spec).
- PLAN Phase 6 per-tree description for the `minimal`
  sub-spec (uniform multi-file + README description).

## Proposal: Q2 — `livespec` template's seed prompt unconditionally emits `sub_specs[]`, hurting end users

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
  (§"`seed`" pre-seed-template-selection paragraph and the
  paragraph immediately after the `seed_input.schema.json`
  example, "Sub-specs payload (v018 Q1)")
- `brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`
  (Phase 2 — `livespec` template's `prompts/seed.md` minimum
  scaffolding mention; Phase 3 — `prompts/seed.md`
  bootstrap-minimum authoring scope; Phase 6 seed intent
  block — explicit "yes, this project ships templates" answer
  to the new pre-seed question)

`deferred-items.md` is NOT touched. The
`sub-spec-structural-formalization` entry remains accurate.

### Summary

**Failure mode: shipped-contract defect (end-user-facing).**
PROPOSAL.md §"`seed`" specifies that the `livespec` template's
seed prompt emits `sub_specs[]` payloads for BOTH built-in
templates whenever the active main-spec template is `livespec`,
"so the seeded repo carries full sub-spec trees ready for Phase
7 agent-generation." The "ready for Phase 7 agent-generation"
clause is specific to livespec-the-project's own bootstrap.
But the `livespec` template's seed prompt is a SHIPPED
artifact, used by end-user projects that pick the `livespec`
template for their own specs. The same prompt fires in both
cases. End users get spurious
`SPECIFICATION/templates/livespec/` and
`SPECIFICATION/templates/minimal/` trees they did not ask for,
do not need, and cannot meaningfully consume — they aren't
shipping templates of their own.

The seed prompt has no signal to distinguish "this project
ships its own livespec templates" from "this project just uses
livespec to manage its own application's spec." Phase 6 hides
the defect because it executes in livespec's own repo (where
"yes, ships templates" is the correct answer), but the shipped
contract is wrong as written.

§"`seed`" tries to soften this with "When the active main-spec
template is `minimal` (single-file), the seed prompt MAY emit
an empty `sub_specs: []`" — but that "MAY" applies only to the
`minimal` template, not to the `livespec` template. Under the
`livespec` template, the prompt is described as
unconditionally emitting both sub-spec payloads.

### Failure mode

Shipped-contract defect — end-user projects using the
`livespec` template receive spurious sub-spec trees.

### Resolution options

**Option A (recommended): Make sub-spec emission opt-in via the
pre-seed dialogue.**

§"`seed`" pre-seed-template-selection paragraph (already
specifies a dialogue prompt asking the user which template to
use) gains an additional question, asked AFTER template
selection and only when the selected template is one whose
seed prompt is capable of emitting sub-specs (the `livespec`
built-in is the v1 example):

> "Does this project ship its own livespec templates that
> should be governed by sub-spec trees under
> `SPECIFICATION/templates/<name>/`? (default: no)"

On "no" (the default, and the typical end-user case), the seed
prompt emits `sub_specs: []`. On "yes," the dialogue collects
the list of template directory names under the project's
`.claude-plugin/specification-templates/` (or equivalent
location for projects that ship templates differently), and
the prompt emits one `sub_specs[]` entry per named template
with the sub-spec content the LLM authors from the project's
own template descriptions.

§"`seed`" sub_specs-payload paragraph is amended:

> When the user has answered "yes" to the pre-seed
> "ships own livespec templates" question, the seed prompt
> emits one `sub_specs[]` entry per named template, each
> entry's `files[]` carrying the sub-spec's spec-file content
> at `SPECIFICATION/templates/<template_name>/<spec-file>`.
> When the user has answered "no" (the default), the seed
> prompt emits `sub_specs: []`. The shipped seed prompt's
> behavior is uniform across templates and does not assume
> any specific main-spec template name; the per-template
> dispatch in v019 (where the `livespec` template emits
> sub-specs and the `minimal` template emits empty) is
> superseded by the user-driven dialogue answer.

Phase 2 of the bootstrap plan: the `livespec` template's
minimum-viable `prompts/seed.md` includes the new pre-seed
dialogue question (it must, since Phase 6's seed needs to
answer "yes"). Phase 3's bootstrap-minimum widening of
`prompts/seed.md` makes the dialogue rigorous (handles "yes"
+ template-name enumeration, handles "no" → empty sub_specs).
Phase 6's seed intent block is explicit: the LLM driving the
seed dialogue answers "yes" and names `livespec` and
`minimal` as the two shipped templates.

Pros:
- Single shipped prompt; no end-user-vs-meta-project
  divergence.
- The pre-seed dialogue already exists; extending it by one
  question is the smallest interface change.
- v2+ extension point: any project that ships livespec
  templates of its own gets sub-spec governance for them via
  the same mechanism, with no special "this is a meta-project"
  flag.
- Default ("no") is correct for the overwhelming majority of
  use cases.

Cons:
- The `livespec` template's seed prompt grows by one dialogue
  question (a small but real authoring change at Phase 3).

**Option B: Ship two distinct seed prompts.**

`prompts/seed.md` becomes the end-user-facing prompt (always
emits `sub_specs: []`); a new `prompts/seed-meta.md` is
shipped alongside, used by projects that ship livespec
templates. Phase 6 invokes `seed-meta.md` directly. The
template loader / SKILL.md prose chooses between the two
prompts.

Pros:
- Each prompt is single-purpose and simpler to author.

Cons:
- Two prompts to maintain that share most of their content.
- The choice between them is a project-property decision that
  ought to live in the dialogue, not a hidden prompt-loader
  decision.
- Forces the SKILL.md prose to know about the meta-vs-end-user
  distinction at template-resolution time.
- v2+ user-shipped templates that author their own
  `prompts/seed-meta.md` would have to clone the entire
  shipped seed-meta prompt rather than answer one extra
  dialogue question.

**Option C: Phase-6-only bypass.**

The shipped `prompts/seed.md` always emits empty `sub_specs[]`
(matching end-user expectations). Phase 6 of the bootstrap
plan bypasses the prompt entirely for sub-spec content,
hand-crafting the `seed_input.schema.json` payload's
`sub_specs[]` field and feeding it directly to `bin/seed.py
--seed-json <path>`.

Pros:
- The shipped seed prompt has the simplest possible behavior.

Cons:
- Phase 6 bypass sits outside the governed loop and outside
  the v018 Q2 / v019 Q1 bootstrap-exception clause, which is
  scoped to imperative landings that produce the seed but
  does not contemplate hand-crafting the seed payload itself.
  The bootstrap-exception clause would need a separate carve-
  out for "Phase-6 seed-payload hand-crafting", growing the
  exception window in a new direction.
- The capability "this project ships templates governed by
  sub-specs" stops being a v1+ first-class feature and
  becomes a livespec-internal-only special case. v2+
  user-shipped-template authors who want sub-spec governance
  for their templates have no documented path to get it.

**Option D: Infer from intent text.**

The seed prompt parses the `<intent>` text for cues that the
project ships templates ("our project ships custom livespec
templates", "this is a meta-project authoring templates",
etc.) and emits `sub_specs[]` accordingly.

Pros:
- No dialogue change.

Cons:
- LLM heuristic on freeform text is unreliable for a
  structural decision; misclassification produces silently-
  wrong on-disk artifacts.
- Phase 6's intent block would need to be carefully worded to
  trip the heuristic correctly.
- A user who happens to mention "templates" in their intent
  for unrelated reasons (e.g., "we use Jinja templates")
  could trip the heuristic in error.

### Recommended disposition

**Accept Option A.** Extending the existing pre-seed dialogue
by one question is the smallest interface change that makes
sub-spec emission a deliberate user choice rather than an
implicit default. The shipped seed prompt stays single-purpose
and serves both end users and meta-projects via one explicit
question. Phase 6's seed intent block answers "yes" and names
the two built-ins, matching v019's Phase 6 intent block almost
verbatim with just the new dialogue answer added.

Concretely, v020 amends:

- §"`seed`" pre-seed-template-selection paragraph (adds the
  "ships own livespec templates" dialogue question after
  template selection).
- §"`seed`" sub_specs-payload paragraph (replaces the
  per-template hard-coded behavior with the user-answer-driven
  behavior).
- PLAN Phase 2 (the `livespec` template's minimum-viable
  `prompts/seed.md` includes the new dialogue question).
- PLAN Phase 3 (widens `prompts/seed.md` to handle the
  dialogue answer rigorously).
- PLAN Phase 6 (seed intent block explicitly answers "yes"
  and names the two built-ins).

## Proposal: Q3 — Phase 3 sub-spec routing is unexercised before Phase 7 leans on it

### Target specification files

- `brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`
  (Phase 3 — exit criterion's throwaway-fixture round-trip
  block, currently exercises only `--spec-target
  <tmp>/SPECIFICATION`)

PROPOSAL.md is NOT touched by this finding; the
`--spec-target` flag's contract per §"Template
sub-specifications" is correct as written. The gap is
plan-level test coverage at the Phase 3 boundary.

`deferred-items.md` is NOT touched.

### Summary

**Failure mode: incompleteness (test coverage gap at phase
boundary).** Phase 3's exit-criterion smoke test asserts that
the throwaway-fixture round-trip files a propose-change against
`<tmp>/SPECIFICATION` (the main tree) and revises it via
`<tmp>/SPECIFICATION` — the main tree only. `--spec-target`
sub-spec routing
(`--spec-target <tmp>/SPECIFICATION/templates/livespec`) is not
exercised end-to-end at Phase 3's exit. Phase 6's seed produces
the sub-spec trees on disk (per Phase 3's existing exit text),
but no propose-change / revise cycle touches a sub-spec tree
until Phase 7, where every template's content is generated
through that exact code path.

A bug in `--spec-target` sub-spec routing — incorrect spec-root
resolution, wrong `proposed_changes/` directory selection,
missed `history/vNNN/` cut, mis-validated path argument — would
escape Phase 3's narrow gate and only manifest deep into Phase
7's dogfooded cycles. Phase 7's dogfood discipline ("zero
imperative landings") makes recovery from such a bug expensive:
the fix itself must flow through propose-change / revise,
which is the very thing that's broken.

The fix is mechanical: extend Phase 3's smoke test by one
additional propose-change / revise cycle targeting the
sub-spec tree.

### Failure mode

Incompleteness — test coverage gap at phase boundary;
sub-spec routing untested before its primary consumer relies
on it.

### Resolution options

**Option A (recommended): Extend Phase 3's exit-criterion
smoke test with a sub-spec-targeted cycle.**

After Phase 3's existing main-tree propose-change / revise
smoke (which lands at `<tmp>/SPECIFICATION/history/v002/`),
file a second propose-change / revise cycle:

```
/livespec:propose-change --spec-target <tmp>/SPECIFICATION/templates/livespec
/livespec:revise         --spec-target <tmp>/SPECIFICATION/templates/livespec
```

Confirm `<tmp>/SPECIFICATION/templates/livespec/history/v002/`
materializes alongside the main tree's `history/v002/`. Same
code path as the main-tree smoke; different `--spec-target`
argument. The throwaway fixture grows by a few additional
asserts, no new fixtures or test infrastructure.

Pros:
- Smallest possible change — one extra invocation in the
  smoke test.
- Catches sub-spec routing bugs at Phase 3's boundary, where
  recovery is imperative-landing (cheap), instead of Phase
  7's boundary where recovery requires the broken governed
  loop.
- Symmetric with the existing main-tree smoke; no new
  pattern.

Cons:
- Phase 3's exit criterion grows by one bullet — minor
  authoring overhead.

**Option B: Skip; rely on Phase 7's first dogfooded cycle.**

Phase 7's first work item is "widen propose-change to full
feature parity via propose-change/revise cycle against the
seed." The first such cycle is mechanically the first
sub-spec-routing exercise. If sub-spec routing is broken,
Phase 7's first cycle fails and the executor diagnoses there.

Pros:
- Zero plan change.

Cons:
- A broken sub-spec routing surfaces inside the dogfood
  discipline. Recovery requires either (a) bypassing the
  dogfood discipline imperatively to fix the routing
  (violating v019 Q1's "Phase 7 has zero imperative
  landings" assertion), or (b) attempting to fix the routing
  via the very dogfood mechanism that's broken (circular).
- The throwaway-fixture environment is a much cleaner debug
  surface than the live livespec repo at Phase 7.

**Option C: Move the smoke check to Phase 6 (after the real
seed produces real sub-spec trees).**

Phase 6's exit criterion grows a single smoke cycle:
`--spec-target SPECIFICATION/templates/livespec`
propose-change + revise against the real seeded sub-spec
tree, not a throwaway fixture.

Pros:
- The smoke runs against real seeded content rather than
  throwaway content.

Cons:
- Phase 6 is intentionally narrow (one seed invocation, one
  doctor run). Adding a propose-change / revise cycle to
  Phase 6's exit criterion pulls "first dogfooded cycle"
  into Phase 6 rather than Phase 7.
- Bugs surface one phase later than Option A — Phase 6's
  imperative-landing window is closed by then per v018 Q2,
  so recovery semantics are awkward (technically the same
  problem as Option B, just shifted by one phase).

### Recommended disposition

**Accept Option A.** Phase 3's exit criterion grows one
propose-change / revise cycle targeting the sub-spec tree,
asserting `<tmp>/SPECIFICATION/templates/livespec/history/v002/`
materializes. This is the smallest possible change and
catches sub-spec routing bugs in the phase where they're
mechanically recoverable.

Concretely, v020 amends:

- PLAN Phase 3's exit criterion (adds a sub-spec-targeted
  propose-change / revise cycle to the throwaway-fixture
  round-trip block).

## Proposal: Q4 — Phase 6 widens only `prompts/seed.md`; Phase 7's heaviest semantic work runs through still-stub propose-change/revise/critique prompts

### Target specification files

- `brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`
  (Phase 3 — "Required implementation surface" enumeration of
  the `livespec` template's prompts, which currently widens
  only `prompts/seed.md`)

PROPOSAL.md is NOT touched by this finding; the prompt-content
wording is plan-level scoping, not proposal-level.

`deferred-items.md` is NOT touched.

### Summary

**Failure mode: under-specification at phase boundary leading
to quality risk in dogfooded output.** Phase 2 of the bootstrap
plan authors all four `livespec`-template prompts at "minimum-
viable" level — "just enough for the Phase 3 / Phase 6
bootstrap seed to succeed against this repo." Phase 3 then
widens **only** `prompts/seed.md` to "bootstrap-minimum
authoring sufficient for the Phase 6 seed LLM round-trip to
produce a schema-valid `seed_input.schema.json` payload covering
the main spec AND the two template sub-specs." The remaining
three (`prompts/propose-change.md`, `prompts/revise.md`,
`prompts/critique.md`) stay at Phase 2's "minimum-viable" level
through Phases 3, 4, 5, and 6.

Phase 7 then uses those three minimum prompts to drive the
dogfooded propose-change / revise cycles that author the FULL
final prompt content for the `livespec` template — its
heaviest semantic work, including (recursively) authoring the
very prompts being used. The prompts driving the LLM to
generate high-quality final prompts are themselves under-
specified, so the final prompt content quality suffers.

This is not a logical contradiction — Phase 7's mechanism is
mechanically sound — but it is a foreseeable quality risk
that the plan currently does not acknowledge or mitigate.

### Failure mode

Under-specification at phase boundary — Phase 2 / Phase 3
prompt-authoring scope is asymmetric across the four
`livespec`-template prompts in a way that leaves the
non-seed prompts thin precisely where Phase 7 leans on them
hardest.

### Resolution options

**Option A (recommended): Widen all four `livespec`-template
prompts to bootstrap-minimum at Phase 3, mirroring the existing
seed.md widening.**

Phase 3's "Required implementation surface" enumeration grows
from one prompt-authoring item ("The `livespec` template's
`prompts/seed.md` — bootstrap-minimum authoring ...") to four:

- `prompts/seed.md` — bootstrap-minimum authoring sufficient
  for the Phase 6 seed LLM round-trip (per v019 wording).
- `prompts/propose-change.md` — bootstrap-minimum authoring
  sufficient for Phase 7's first dogfooded cycle to file
  full-fidelity propose-change files (handling sub-spec
  routing via `--spec-target`, full front-matter authoring,
  reserve-suffix awareness for `-critique` etc.).
- `prompts/revise.md` — bootstrap-minimum authoring sufficient
  for Phase 7's first dogfooded cycle to drive per-proposal
  decisions, write paired revision files, and trigger version
  cuts.
- `prompts/critique.md` — bootstrap-minimum authoring
  sufficient for Phase 7's first dogfooded cycle to invoke
  critique-as-internal-delegation against either a main-spec
  or sub-spec target.

Phases 6 and 7 are unchanged: Phase 6 still uses only the
seed prompt; Phase 7 uses the now-bootstrap-minimum
propose-change / revise / critique prompts to author final
prompt content via dogfooded cycles. The wording mirrors the
existing seed.md widening exactly — "bootstrap-minimum
authoring sufficient for [the next consumer phase]" — so
implementer scope expansion is small and parallel.

Pros:
- Mirrors the existing v019 pattern for seed.md exactly; no
  new authoring philosophy.
- Resolves the quality risk at its source (the prompts that
  drive Phase 7's heaviest work are themselves of comparable
  bootstrap-minimum quality).
- Keeps Phase 7 strictly dogfood (no in-phase prompt
  hand-widening).
- Honors the v018 Q2 / v019 Q1 bootstrap-exception boundary
  unchanged (all hand-authoring stays inside the imperative
  window).

Cons:
- Phase 3 authoring scope grows by three prompts. Each is
  small (bootstrap-minimum, not full-featured), but the
  authoring lift is real.

**Option B: Skip; accept the quality risk.**

Phase 7 iterates on prompt quality through multiple dogfood
cycles. The first cycle produces a thin final prompt; later
cycles widen it. Convergence is acceptable given Phase 7 is
already iterative.

Pros:
- Zero plan change.

Cons:
- The first-pass output of Phase 7's dogfood is the canonical
  artifact landing in `SPECIFICATION/templates/livespec/
  history/v002/`. Iterating later means landing thin content
  first and widening it across multiple revisions, which is
  more audit-trail churn than necessary.
- The recursion (using thin propose-change/revise prompts to
  widen propose-change/revise prompts) is fragile in a way
  that's hard to reason about until it fails.

**Option C: Insert a Phase 6.5 to widen the three prompts via
dogfood.**

A new explicit phase ("Phase 6.5") between Phase 6 and Phase
7 widens `propose-change.md`, `revise.md`, `critique.md` via
dogfooded cycles — using the still-Phase-2-minimum versions
of those very prompts to do the widening.

Pros:
- Keeps Phase 3 narrow.

Cons:
- The circular bootstrap (using thin prompts to widen those
  same prompts) is the very pattern Option A avoids; Phase
  6.5 just relocates the problem.
- Adds a phase to the plan — net authoring overhead is larger
  than Option A.

**Option D: Allow hand-editing of the prompts at Phase 7 as a
documented bootstrap-exception extension.**

The v018 Q2 / v019 Q1 bootstrap-exception clause is amended
to permit one additional carve-out: prompt-content
hand-widening at Phase 7 is a permitted imperative landing.

Pros:
- Removes the recursion.

Cons:
- Re-opens the bootstrap-exception boundary that v018 Q2 /
  v019 Q1 spent two revision passes to nail down. Even a
  scoped carve-out broadens the exception's footprint.
- Introduces a precedent for "per-phase imperative carve-outs"
  that future revisions would have to defend against.

### Recommended disposition

**Accept Option A.** Widening all four prompts at Phase 3
mirrors the existing v019 pattern for seed.md, resolves the
quality risk at its source, and keeps the v018 Q2 / v019 Q1
bootstrap-exception boundary unchanged. Phase 3 authoring
grows by three prompts; each is bootstrap-minimum (not
full-featured), so the lift is small.

Concretely, v020 amends:

- PLAN Phase 3's "Required implementation surface" — the
  prompt-authoring item grows from one (seed.md) to four
  (seed.md + propose-change.md + revise.md + critique.md),
  each with parallel "bootstrap-minimum authoring sufficient
  for [next consumer phase]" wording.

Phase 6 and Phase 7 are unchanged.

## Cross-cutting notes

- All four findings are mutually independent; each can be
  accepted, rejected, or modified separately. Q1 and Q2 both
  edit PROPOSAL.md §"Template sub-specifications" / §"`seed`"
  but in different paragraphs and on different concerns
  (structure vs. payload-emission).
- Q1 and Q2 together resolve the "v018 Q1 left two
  ambiguities" status of the template-sub-specification
  mechanism: Q1 closes the structural ambiguity (sub-spec
  layout), Q2 closes the prompt-emission ambiguity (when does
  the prompt emit sub-spec payloads).
- Q3 and Q4 are PLAN-only and do not touch PROPOSAL.md.
- `deferred-items.md` is frozen at v018 per the bootstrap
  plan's Preconditions; this pass does not open or close any
  deferred entries. The `sub-spec-structural-formalization`
  entry's body remains accurate under all four resolutions.
- This pass leaves the v018 Q2 / v019 Q1 bootstrap-exception
  clause unchanged. Q4's Option D was the only resolution that
  would have weakened it; that option was rejected.
