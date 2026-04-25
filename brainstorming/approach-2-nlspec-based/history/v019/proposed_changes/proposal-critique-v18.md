---
topic: proposal-critique-v18
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-25T08:00:00Z
---

# Proposal-critique v18

A targeted, fast-track critique pass over v018 `PROPOSAL.md`
surfacing one self-contained logical contradiction in
§"Self-application". The contradiction was uncovered while
reviewing the bootstrap plan
(`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`) for execution
correctness against PROPOSAL.md v018 and confirming that the
bootstrap-exception clause (Q2) and the step-by-step bootstrap
ordering close cleanly with no gaps.

This is a **single-issue critique**: one finding, one disposition.

Findings in this pass:

- **Critical execution-blocking gap (1 item):** Q1
  (self-application step 4 requires `propose-change` /
  `revise` to already exist, but step 4 itself is where they
  are implemented; the Q2 bootstrap-exception window closes
  before step 4 begins, producing a logical impossibility).

## Proposal: Q1 — §"Self-application" steps 2/4 + Q2 bootstrap-exception clause encode a chicken-and-egg

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
  (§"Self-application" steps 2, 4, and the trailing
  "Bootstrap exception (v018 Q2)" paragraph)

`deferred-items.md` is NOT touched by this pass. No new deferred
entries open; no existing entries close. The fix is internal to
PROPOSAL.md.

### Summary

**Failure mode: incompleteness (logical contradiction at
boundary).** The §"Self-application" section establishes a
six-step bootstrap ordering and a "Bootstrap exception (v018
Q2)" clause. Read literally, the three load-bearing sentences
contradict each other:

- **Step 2** says: "Implement the plugin skeleton: ... and the
  minimum subset of the `livespec` template needed to consume
  PROPOSAL.md as seed input." The literal scope is "enough to
  invoke seed" — i.e., `bin/seed.py`, `commands/seed.py`,
  the `livespec` template's `prompts/seed.md`, and supporting
  parse/validate/io modules. Step 2 explicitly does NOT include
  `propose-change`, `critique`, or `revise` implementations.

- **Step 4** says: "Implement remaining sub-commands
  (`propose-change`, `critique`, `revise`, `prune-history`,
  doctor's LLM-driven phase at the skill layer), **using
  `propose-change` / `revise` cycles** against the seeded spec
  trees." Read literally, step 4 requires `propose-change` and
  `revise` to already exist as functioning sub-commands when
  step 4 begins.

- **Bootstrap exception (Q2)** says: "The bootstrap ordering
  above (steps 1-4, ending with the first `livespec seed`
  invocation in step 3) lands imperatively. The governed
  propose-change → revise loop becomes operable starting at
  step 4 — after seed has produced the working `SPECIFICATION/`
  tree." Read literally, the imperative window closes at the
  end of step 3; from step 4 onward the governed loop is
  MANDATORY.

The three statements together produce a logical impossibility:
step 4 must use propose-change/revise to implement
propose-change/revise, but propose-change/revise don't exist
when step 4 starts, AND the imperative window has already
closed so they can't be hand-implemented either.

The recreatability test fails here in a specific way: a
competent implementer reaches step 4 with seed produced and
SPECIFICATION/ in hand, but no governed-loop tool to land any
further code change, and no permitted fast-path to land the
governed-loop tool itself.

This is a self-contained PROPOSAL.md bug, not a plan-level gap.
Any plan-level workaround (e.g., quietly hand-implementing
propose-change/revise in the post-seed phase) propagates the
contradiction into `SPECIFICATION/` at Phase 6 of the bootstrap
plan, because Phase 6 migrates §"Self-application" verbatim
into `SPECIFICATION/spec.md`. The seeded SPECIFICATION would
then carry the same logical contradiction as its starting
oracle. The fix MUST land in PROPOSAL.md before the seed.

### Failure mode

Incompleteness — logical contradiction at boundary.

### Resolution options

**Option A (recommended): Widen step 2's scope to include
minimum-viable propose-change/critique/revise alongside seed.**

Step 2 is amended to enumerate, alongside the existing seed
implementation surface, the minimum-viable implementations of
`propose-change`, `critique`, and `revise` necessary to file
the first dogfooded change cycle against the seeded
SPECIFICATION/. "Minimum-viable" means: the wrappers, the
command modules, and the schemas/dataclasses they need to
parse a propose-change file, write a revision file, and cut a
new history version — at the level of correctness sufficient
for the FIRST dogfooded cycle, not full-feature parity.

Step 4 is amended to **widen** the existing minimum-viable
sub-commands to full-feature (topic canonicalization,
reserve-suffix discipline, collision disambiguation, full
critique/revise prompt-driven flows, etc.) AND implement the
remaining sub-commands not present in step 2 (`prune-history`,
doctor's LLM-driven phase), all via dogfooded
propose-change/revise cycles.

The Q2 bootstrap-exception clause stays substantively
unchanged: imperative landing ends at the first seed (end of
step 3); step 4 onward is governed-loop-mandatory. The
widened step 2 places the imperative landing of
minimum-viable sub-commands BEFORE the seed, so the
exception window's closing point doesn't move.

Pros:
- Smallest substantive change — three paragraphs amended.
- Bootstrap-exception clause's "ends at first seed" boundary
  stays clean; doesn't introduce a fuzzier "operable" criterion.
- Phase 7 of the bootstrap plan becomes purely dogfood (zero
  imperative landings after seed), matching the spirit of Q2.
- Honors livespec's `feedback_brainstorming_no_history_obsession`
  preference: prefer clean breaks over backwards-compatible
  options.

Cons:
- Phase 3 of the bootstrap plan widens (expected — that's the
  point); the plan must mirror the v019 step-2 scope.

**Option B: Extend the bootstrap-exception window past the
first seed.**

Step 2 stays narrow (seed only). Step 4's "using
propose-change/revise cycles" is qualified with: "After
hand-implementing minimum-viable propose-change and revise
imperatively, widen via dogfooded cycles." The Q2 clause is
amended to read "imperative window ends when propose-change
and revise are operable" rather than "imperative window ends
at the first seed."

Pros:
- Step 2 stays minimal (matches the literal "minimum subset
  needed to consume PROPOSAL.md as seed input" phrasing).

Cons:
- The bootstrap-exception boundary becomes fuzzier: "operable"
  is a definitional criterion rather than a phase-boundary
  criterion.
- The imperative window straddles the seed, which is the
  opposite of the cleaner "imperative-then-governed" cutover
  Q2 was originally designed to express.
- Phase 7 of the bootstrap plan acquires a small imperative
  prefix.

**Option C: Reframe step 4 as in-step bootstrap.**

Step 4 explicitly permits in-step hand-bootstrapping of
propose-change/revise to a minimum-viable level, with the
caveat that the FIRST dogfooded cycle is filed against the
just-implemented sub-commands. The Q2 clause is amended to
read "imperative landing ends at the first dogfooded cycle"
rather than "ends at the first seed."

Pros:
- Step 4 reads more like the actual mechanical reality.

Cons:
- Verbal — the chicken-and-egg is still present, just
  legitimized as an "in-step bootstrap."
- The Q2 boundary moves further past the seed (now ending at
  the first dogfooded cycle), making the imperative window
  even larger than Option B.
- Worst alignment with the existing bootstrap-exception
  framing.

### Recommended disposition

**Accept Option A.** The fix is the smallest substantive
change that resolves the contradiction without weakening the
bootstrap-exception boundary. Phase 3 of the bootstrap plan
mirrors v019's widened step 2 naturally; Phases 6-7 mirror
v019's clarified step 4 (Phase 6 is purely the seed; Phase 7
is purely dogfooded widening + remaining-sub-command
implementation).

Concretely, v019 amends three paragraphs in PROPOSAL.md:
- Step 2's closing clause widens from "the minimum subset of
  the `livespec` template needed to consume PROPOSAL.md as
  seed input" to "the minimum subset of the `livespec`
  template needed to consume PROPOSAL.md as seed input,
  AND minimum-viable implementations of `propose-change`,
  `critique`, and `revise` sufficient to file the first
  dogfooded cycle against the seeded SPECIFICATION/."
- Step 4's verb changes from "Implement remaining
  sub-commands" to "Widen the minimum-viable sub-commands
  (`propose-change`, `critique`, `revise`) to full feature
  parity, and implement the remaining sub-commands
  (`prune-history`, doctor's LLM-driven phase at the skill
  layer)."
- Q2 bootstrap-exception paragraph adds one sentence
  acknowledging that the widened step 2 places minimum-viable
  sub-commands BEFORE the seed, so the imperative window's
  closing point at "end of step 3" stays unmoved.

No deferred-items entries open or close. No companion docs
touched. No `python-skill-script-style-requirements.md`
ripple. Plan-side ripple (Phase 3 widening, Phase 7
re-narrative as pure dogfood) is captured in the bootstrap
plan revision that follows this revision.
