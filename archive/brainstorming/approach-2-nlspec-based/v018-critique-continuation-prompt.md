# Critique-continuation interview prompt (v017 → v018)

Paste the body below into a new Claude Code session rooted at
`/data/projects/livespec/` to continue the in-progress v018
critique-and-interview pass.

This prompt is NOT the generic critique-interview-prompt.md template.
It is specific to v018 because there is already an in-progress
critique file on disk (with one item, Q1, captured) plus a list of
candidate additional items that were surfaced during a bootstrap-
plan review in a prior session. The continuation session extends
the critique, interviews the user, and applies the full dogfood
lifecycle.

Version knobs (locked, not parameterized):

- Current version: **v017**
- Next version: **v018**
- Critique sequence number: **v17** (critique file basename is
  `proposal-critique-v17`)

Everything below the `---` is the prompt body to paste.

---

I want to continue the in-progress livespec v017→v018 critique-
and-interview pass.

## Current state

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md` is v017
  (frozen); it MUST be byte-identical to
  `brainstorming/approach-2-nlspec-based/history/v017/PROPOSAL.md`.
  Confirm this before doing anything else; if they diverge, stop
  and ask.
- An in-progress critique lives at
  `brainstorming/approach-2-nlspec-based/proposed_changes/
  v018-proposed-change-proposal-critique-v17.md` with **one item
  captured so far** (Q1 — built-in templates lack sufficient
  specifications for agentic regeneration; recommended Option A
  adopts nested sub-specifications under
  `SPECIFICATION/templates/<name>/`).
- The bootstrap plan at
  `brainstorming/approach-2-nlspec-based/
  PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` has ALREADY been
  updated with Q1-Option-A's plan-side implications (Phase 2/3/5/6/
  7/8 edits, Risks widening, execution-prompt dogfooding-rule
  extension). Do not re-apply those; verify they're present.
- `deferred-items.md` has NOT yet been edited for Q1; the
  `template-prompt-authoring` entry is unchanged, and no
  `sub-spec-structural-formalization` entry exists yet.
  Both are part of the v018 revision's scope.

## Required reading

Load everything the generic critique-interview-prompt.md at
`brainstorming/approach-2-nlspec-based/critique-interview-prompt.md`
§"Required reading" lists:

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md` (v017)
- `brainstorming/approach-2-nlspec-based/livespec-nlspec-spec.md`
- `prior-art/nlspec-spec.md`
- `brainstorming/approach-2-nlspec-based/goals-and-non-goals.md`
- `brainstorming/approach-2-nlspec-based/subdomains-and-unsolved-routing.md`
- `brainstorming/approach-2-nlspec-based/prior-art.md`
- `brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`
- All four `2026-04-19-nlspec-*.md` lifecycle / terminology docs
- `brainstorming/approach-2-nlspec-based/history/README.md`
- Every `history/vNNN/PROPOSAL.md`, every
  `history/vNNN/proposed_changes/*.md`, and every
  `history/vNNN/conversation.json` that exists. Skim
  `history/vNNN/retired-documents/` READMEs to understand what
  was retired; do NOT load retired docs themselves.

Additionally load (specific to this continuation):

- `brainstorming/approach-2-nlspec-based/proposed_changes/
  v018-proposed-change-proposal-critique-v17.md` — the in-progress
  critique (Q1 captured).
- `brainstorming/approach-2-nlspec-based/
  PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` — the Q1-Option-A-
  aligned bootstrap plan. Read it to understand what the plan
  already assumes about the v018 outcome, so the interview
  does not accidentally un-do that alignment.

## Candidate additional critique items (bootstrap-plan review)

The following candidate items were surfaced by a prior session's
review of the bootstrap plan against PROPOSAL.md v017. They are
SUGGESTIONS — the user decides which, if any, become v018
critique items. Each is stated below as a potential gap against
PROPOSAL.md (not the plan; the plan is a separate artifact).
Do NOT treat them as pre-accepted. Do NOT interview on them
until the user has said which they want to pursue.

**Critical (execution-blocking unless resolved):**

- **C-1: Self-application bootstrap paradox for `propose-change`
  and `revise`.** PROPOSAL.md §"Self-application" mandates that
  every change lands via propose-change/revise. But the FIRST
  landing of the propose-change and revise sub-commands
  themselves has nowhere to flow through. PROPOSAL.md does not
  articulate a bootstrap exception. Candidate fix: add a
  "bootstrap exception" clause in §"Self-application" stating
  that initial sub-command implementations land imperatively,
  and the loop applies from the second change onward.

- **C-2: Initial-vendoring mechanism for `_vendor/` libraries.**
  PROPOSAL.md §"Vendoring discipline" names `just vendor-update
  <lib>` as "the only blessed mutation path". That recipe
  invokes Python through `livespec.parse.jsonc`, which imports
  the vendored `jsoncomment`. First-time vendoring of
  `jsoncomment` itself has no documented path. Candidate fix:
  PROPOSAL.md explicitly sanctions a one-time manual-vendoring
  procedure (git clone + checkout + cp + LICENSE capture) for
  initial population, distinct from the blessed update path.

- **C-3: Typechecker + `returns`-plugin disposition deferred at
  spec level.** PROPOSAL.md defers
  `returns-pyright-plugin-disposition` and
  `basedpyright-vs-pyright` to `deferred-items.md` without
  decision criteria. Deferred items without criteria cannot be
  closed agentically. Candidate fix: either the decision lands
  in v018 with a concrete choice, OR PROPOSAL.md specifies
  objective criteria (e.g., "typechecker MUST support
  `Result[...]` inference without type: ignore in X% of pure
  modules; pick whichever tool meets the bar").

**High (quality / rework risk):**

- **H-1: `tests/heading-coverage.json` population mechanism
  unspecified.** PROPOSAL.md §"Testing approach" describes the
  meta-test that catches drift but doesn't specify who
  populates initial entries. Candidate fix: add a section
  naming the population procedure (automated via a
  `dev-tooling/` helper script vs. commit-time convention
  vs. skill-prose responsibility).

- **H-2: Seed-prompt LLM round-trip correctness unverifiable
  pre-integration-test.** PROPOSAL.md's prompt I/O contracts
  describe output schema but don't specify how prompt behavior
  is verified before the end-to-end integration test runs. A
  silently-wrong prompt produces garbage SPECIFICATION/ output.
  Candidate fix: add a prompt-QA subsection to testing approach
  (e.g., a tiny deterministic fake_claude used for prompt-level
  tests, separate from the e2e harness).

- **H-3: Companion-doc migration policy under-specified.**
  PROPOSAL.md's seeding model implies every companion doc finds
  a home during self-seeding, but the policy per doc is not
  prescribed. Candidate fix: PROPOSAL.md § names each companion
  doc's destination class (MIGRATED-to-SPEC-file /
  SUPERSEDED-by-section / ARCHIVE-ONLY).

**Medium (ambiguity / gap):**

- **M-1: `python3 >= 3.10` without patch-version guidance.**
  PROPOSAL.md §"Runtime dependencies" pins only the minor
  version floor. Candidate fix: either name a specific minimum
  patch or state an explicit patch-agnostic policy (e.g.,
  "latest-patch of the 3.10 line at mise-pinning time").

- **M-2: `plugin.json` shape not specified in PROPOSAL.md.**
  Candidate fix: add a Plugin metadata section or point to an
  authoritative reference.

**Low (nits):**

- **L-1: Repo-root README.md relationship to SPECIFICATION/ not
  addressed in PROPOSAL.md.**
- **L-2: `brainstorming/approach-2-nlspec-based/proposed_changes/`
  directory lifecycle after brainstorming-freeze not addressed
  (empty today; relationship to seeded
  `SPECIFICATION/proposed_changes/` not stated).**

## What to produce

1. **Summarize current state to the user.** Start by reading all
   required files, then surface: what Q1 captures, what the plan
   already assumes, what candidate items exist, and whether
   `deferred-items.md` edits are pending for v018.

2. **Ask the user which candidate items to promote into the
   critique** (and invite them to raise any the list misses).
   Every promoted item becomes a new `## Proposal:` section in
   `proposed_changes/v018-proposed-change-proposal-critique-
   v17.md`, numbered Q2, Q3, … in user-chosen order. Use the
   established multi-proposal format: YAML front-matter at the
   file level, flat `## Proposal: Q<N> — <title>` sections with
   `### Target specification files`, `### Summary` (lead with
   failure-mode label: ambiguity / malformation /
   incompleteness / incorrectness), `### Motivation`,
   `### Proposed Changes` (option list with a Recommended and
   rationale).

3. **Interview the user through every item** in Q-order (Q1
   first, then Q2, …), one question at a time. Follow the
   generic prompt's rules verbatim:
   - Print each item's sub-options visibly BEFORE asking.
   - Ask exactly ONE question per turn. Never batch.
   - Lead every question with a Recommended option and say why.
   - Push back when the user is wrong or conflicts with
     decisions already in PROPOSAL.md or any prior revision
     file under `history/`.
   - Do not obsess over v017 compatibility during brainstorming;
     propose cleaner breaks when they're better.
   - If the user asks to clarify, clarify before re-asking.
   - If the user rewrites a companion doc mid-interview, append
     new critique items for any gaps that rewrite opens up
     against PROPOSAL.md before finishing.

4. **After the interview, do the full dogfood lifecycle apply**
   per critique-interview-prompt.md §4 (reproduced in spirit
   below — follow that file's exact wording for anything
   ambiguous here):
   - Write
     `history/v018/proposed_changes/proposal-critique-v17-
     revision.md` capturing per-item decisions (accept /
     modify / reject + rationale).
   - Rewrite top-level `PROPOSAL.md` to v018 incorporating all
     decisions. Apply matching edits to every companion doc the
     decisions touch — typically
     `python-skill-script-style-requirements.md` and always
     `deferred-items.md` for this pass (Q1 alone requires a new
     `sub-spec-structural-formalization` entry + closure of
     `template-prompt-authoring`; further items may require
     more).
   - **Run multiple careful-review passes BEFORE the byte-
     identical history copy.** Minimum 2; continue until a
     pass lands no load-bearing fixes. Follow the generic
     prompt's pass-checklist exactly (ripple effects,
     stale references, cross-doc counts, example-vs-rule
     alignment, revision-file drift).
   - **Run a dedicated deferred-items-consistency pass** per
     the generic prompt's §"Run a dedicated deferred-items-
     consistency pass". Source-line drift, layout-tree drift,
     cross-reference validity, example-vs-rule alignment.
   - Create `history/v018/PROPOSAL.md` as a byte-identical
     copy of the working `PROPOSAL.md` (verify via
     `diff -q`).
   - Move the critique from
     `brainstorming/approach-2-nlspec-based/proposed_changes/
     v018-proposed-change-proposal-critique-v17.md` to
     `history/v018/proposed_changes/
     proposal-critique-v17.md`.
   - Update `history/README.md` with a v018 entry summarizing
     structural changes + careful-review findings per pass +
     dedicated deferred-items-pass findings; update the
     "Pointer" paragraph to v018.
   - Capture the session's turns into
     `history/v018/conversation.json`.

5. **Apply plan-file updates for new decisions.** The bootstrap
   plan at `PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`
   already reflects Q1-Option-A. For every NEW decision landed
   in this interview (Q2+), mirror plan-side implications into
   the plan file AT dogfood-apply time (same discipline as the
   Q1-Option-A plan pass). If a decision invalidates parts of
   the Q1-aligned plan text, re-align those sections; leave a
   brief comment in this session's summary flagging the
   re-alignment.

## Known constraints to honor

From critique-interview-prompt.md §"Known constraints to honor"
(fully applies here):

- Do NOT reopen decisions already in PROPOSAL.md or any prior
  `history/vNNN/proposed_changes/*-revision.md` unless the user
  explicitly raises them.
- The latest revision file
  (`history/v017/proposed_changes/proposal-critique-v16-revision.md`)
  is authoritative for what was most recently settled. Read it
  first.

Additional constraints specific to this continuation pass:

- Q1 as captured in
  `proposed_changes/v018-proposed-change-proposal-critique-v17.md`
  is authoritative. Do not re-open its options or recommended
  disposition unless the user explicitly raises it.
- The candidate items list above is SUGGESTIONS only; the user
  drives which become Q2+.
- The bootstrap plan at
  `PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` already
  assumes Q1-Option-A. If the interview leads to revising Q1
  (unlikely), the plan MUST be re-aligned as part of the
  dogfood-apply step.

Start by reading all required files, confirm v017 byte-
identity, summarize current state, then ask the user which
candidate items (if any) to promote before opening the
interview.
