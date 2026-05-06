---
topic: proposal-critique-v02
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-21T00:00:00Z
target_partitions:
  - PROPOSAL.md
---

# Proposal Critique v02 — Completeness for Bootstrapping a SPECIFICATION

## Purpose

Evaluates the v002 `PROPOSAL.md` and its companion files against:

> *Is this material sufficient, today, to seed a working `SPECIFICATION/`
> for `livespec` itself, such that a competent implementer (or agent) could
> proceed without making load-bearing guesses?*

Yardstick: the embedded `livespec-nlspec-spec.md` — behavioral
completeness, unambiguous interfaces, explicit defaults, mapping tables,
testable acceptance criteria, conceptual fidelity, spec economy,
intentional vs accidental ambiguity, and the recreatability test.

Failure mode labels (per Appendix A): **ambiguity**, **malformation**
(self-contradiction), **incompleteness** (scope gap), **incorrectness**
(likely-wrong as stated).

---

## What Is Strong (new or preserved in v002)

- **Lifecycle artifact set and governed loop.** Preserved cleanly; the
  detailed lifecycle diagram now covers `critique` and both `doctor`
  phases, matching the resolution of v001 critique's smaller-issue #8.
- **Versioning edge cases.** The all-reject revise rule (cut a version
  anyway; spec files byte-identical; history preserves proposals +
  rejection acks) is precise and defensible.
- **Doctor static-check inventory.** 13 enumerated checks with exit-code
  semantics; the pass-only/no-warning tier is principled.
- **Proposed-change and acknowledgement formats.** Both have concrete
  front-matter and heading contracts with decision-gated required
  sections.
- **Definition of Done (v1).** 11 concrete, checkable items — the
  proposal now holds itself to the guidelines' own standard.
- **Honest non-goals, now stated inline.** Section "v1 non-goals" names
  five concrete deferrals with rationale. Promotes intentional
  ambiguity to visible.
- **Dogfood order.** Self-application's 5-step bootstrap is explicit.

---

## Major Gaps That Block Seeding

### M1. Claude Code skill execution model is under-specified — **incompleteness**

The proposal commits to "a Claude Code skill" but never specifies:

- Skill packaging contract (is there a `SKILL.md`? frontmatter?
  `allowed-tools`?).
- How the skill dispatches sub-commands from the `args` parameter
  (grep the LLM's instructions? a shell router? a parser spec?).
- How the skill invokes the static-phase script (language, entry-point
  path, invocation idiom, relative-to-skill-root vs project-root).
- How the skill prompts the user (seed's "prompts for a seed";
  `propose-change`'s overwrite confirmation; `revise`'s per-proposal
  confirmation). In a Claude Code skill these prompts are LLM-mediated,
  not traditional CLI — that coupling needs to be stated.
- Where `livespec`'s own skill bundle lives during dogfooded development
  (is the bootstrap build stored at
  `<project-root>/.claude/skills/livespec/` and consumed from there?).

Two implementers would build incompatible skills from this proposal
alone. *This was the single largest gap in v001; it is narrowed but not
closed.*

### M2. Static-phase script is specified by behavior but not by form — **incompleteness**

The proposal says the static phase "is a code script" and is invoked via
"shell execution for the `doctor` static phase," but:

- Implementation language is not pinned ("Implementation language is
  not pinned by this proposal" — testing section, line 547).
- The script's stdout/stderr contract is undefined (what is "doctor
  output"? JSON? human-readable? both?).
- The script's inter-process interaction with the skill (prompt for
  out-of-band-edit auto-proposal in check #9) is unresolvable — a
  script cannot interactively prompt through a Claude Code skill; only
  the LLM wrapper can. Check #9's "SHOULD prompt" therefore crosses a
  phase boundary that is not defined.

The static phase either needs a pinned language + output contract, or
an explicit "phase-A returns structured findings, phase-B (LLM) handles
prompting" split.

### M3. `revise`'s modification mechanism is undefined — **incompleteness / ambiguity**

When a per-proposal decision is `modify`:

- Who authors the modified diff — the LLM, the user, or both in
  dialogue?
- Does the modified proposal file get rewritten before being moved to
  history, or is the original preserved and the acknowledgement's
  `## Modifications` section carries the delta?
- The acknowledgement's `## Modifications` is required on `modify`, but
  the format — prose, unified diff, before/after blocks — is
  unspecified.

Similarly: "Optional `<freeform text>` is treated as an additional
intent input applied alongside (not overriding) the per-proposal
decisions." If freeform text produces spec modifications, the only
lifecycle-consistent way to record them is as a proposed-change file —
but the rule "`proposed_changes/` MUST be empty after a successful
`revise`" combined with "every proposal is moved to the new history
version" means a freeform-only revise has no proposal to anchor its
acknowledgement to. Either auto-create an ephemeral
`vNNN-proposed-change-freeform-<timestamp>.md`, or change the rule.
The proposal does neither.

### M4. Dangling reference: progressive-disclosure mapping — **malformation**

In the `doctor` LLM-driven phase description:

> NLSpec conformance check: evaluates each spec partition against the
> embedded `livespec-nlspec-spec.md` **per the progressive-disclosure
> mapping below**.

There is no mapping below. The v001 critique's M9 was resolved by
deciding "the 40 KB guidelines load unconditionally; partitioning is
not a v1 concern" (NLSpec conformance section), which removed
progressive disclosure from v1 — but the dependent clause in the
`doctor` section was not updated. Vestigial reference; delete or
replace with "against the full embedded guidelines."

### M5. `critique` ↔ `propose-change` output-shape contract is missing — **incompleteness**

`critique` "MUST then call the `propose-change` sub-command with topic
`<author>-critique` and the critique content." But:

- `propose-change` requires a file with YAML front-matter (`topic`,
  `author`, `created_at`, `target_partitions`) plus `## Summary`,
  `## Motivation`, `## Proposed Changes` sections.
- The critique prompt is bundled inside the skill; its output format
  contract is not defined.
- Is the critique prompt required to emit a fully conformant
  proposed-change file end-to-end? Or does `critique` wrap the LLM's
  free-form critique output into the required structure — and if so,
  by what rule (e.g., "entire critique output becomes `## Proposed
  Changes`; `## Summary` / `## Motivation` are generated from the
  prompt; `target_partitions` inferred by the LLM")?

Doctor's static check of the proposed-change format (implied by
"Doctor MUST validate the front-matter and the presence of the
required headings") will fail on outputs from a critique prompt that
does not know this contract. The coupling needs to be spelled out.

### M6. `openspec` reservation creates a silent-failure path — **ambiguity**

- Doctor check #13 explicitly allows `template: "openspec"` (the
  failure applies only to custom-template paths).
- DoD item #3 says selecting `openspec` "produces a clear 'not yet
  implemented' message."
- But no sub-command is named as the message source, and no timing is
  given. An implementer might place the error in `seed` only, meaning
  `propose-change`, `critique`, or `revise` run against a non-existent
  template shape and fail late with cryptic errors.

Pin the error-source command and exact failure mode for `openspec` in
v1 (suggested: fail in *every* sub-command except `help` at the
template-resolution step, with a fixed message string). Alternatively,
move `openspec` to the same failure-class as custom templates in
doctor check #13.

### M7. `seed`'s freeform-input handling is under-specified — **ambiguity / incompleteness**

The seed sub-command:

- Accepts freeform text that "MAY include references to existing
  specifications, examples, projects, or other context."
- Produces `spec.md` with "top-level headings derived from the seed
  input (one heading per major topic identified by the LLM), each with
  a one-sentence description placeholder."

Gaps:

- Does the seed text persist anywhere (e.g., `history/v001/v001-seed.md`)?
  Currently no — the seed is lost after use. The guidelines'
  recreatability test would benefit from preserving it; absent such
  preservation, the seed is an input the spec cannot recreate.
- What if seed text references files by path (`"seed from
  brainstorming/PROPOSAL.md"`)? Does `seed` dereference references, or
  consume only the literal text?
- "One heading per major topic identified by the LLM" — no ceiling, no
  floor, no deterministic tie-break for what a "major topic" is. Two
  implementers will produce different seeded spec skeletons from the
  same input. This is accidental ambiguity at the bootstrap step.

### M8. `.livespec.jsonc` on-disk defaults — **ambiguity**

"`seed` MUST create `.livespec.jsonc` with explicit defaults" — but the
written content is not shown. Options include:

- Write the entire schema block from the "Configuration" section
  verbatim (with comments, preserving documentation value).
- Write only the explicit key/value pairs without comments.
- Write keys with non-default values only (empty file otherwise, since
  defaults apply when absent).

This matters because the file is committed to the repo and reviewed by
humans; the format choice is load-bearing for downstream editing
conventions.

---

## Significant Gaps That Should Be Closed Before Seeding

### S9. Doctor check #10 (BCP 14 well-formedness) is undecidable by static code — **ambiguity**

"No lowercase `must` / `should` / etc. used as a normative term outside
code blocks" requires semantic judgment ("normative term") that a
static script cannot make. Options:

- Tighten to "no lowercase `must`/`shall`/`should`/`may` tokens at all
  outside fenced code and inline `code`" (crude but deterministic).
- Move this check to the LLM-driven phase.
- Require an explicit escape (e.g., `{non-normative}` tag before
  suspect lowercase uses).

Current wording makes the check impossible to implement faithfully.

### S10. Doctor check #11 (Gherkin spacing) will false-positive on prose — **ambiguity**

The rule matches "any line whose first non-whitespace token is a
Gherkin keyword." But prose sentences commonly begin with `And` or
`But`. Constrain the match to lines inside a scenario block (i.e.,
after a `Scenario:` and before the next blank-line-terminated non-step),
or require a specific token pattern (`And\s` + `<Gherkin step shape>`).
The current rule is a false-positive trap for anyone writing prose
explanations adjacent to scenarios in `scenarios.md`.

### S11. `reviser` identity resolution mirrors critique's unsolved author-detection — **incompleteness**

`critique` specifies fallback logic (`unknown-llm` + warning) for
author detection. The acknowledgement's `reviser: <author-id>` field
is introduced without a detection rule. Apply the same fallback logic
to `reviser`, or specify a different one.

### S12. Cross-file reference rule boundaries — **incompleteness**

"Cross-file references between partitions MUST use the GitHub-flavored
anchor form `[link text](contracts.md#section-name)`." But:

- Does the rule apply to `SPECIFICATION/README.md` linking into
  partitions?
- Does the rule apply to proposed-change files referencing spec
  sections?
- Does the rule apply to within-file anchors (e.g., a table-of-contents
  in `spec.md`)?
- Is the path relative to the file containing the link, or to
  `SPECIFICATION/`?
- Does the anchor-resolution check (doctor #12) scan proposed-change
  files?

Without these, the "no dangling references" invariant is under-enforced.

### S13. `SPECIFICATION/README.md` content contract — **incompleteness**

Auto-generated READMEs in `proposed_changes/` and `history/` have a
defined content contract (purpose paragraph + naming convention +
pointer to `SPECIFICATION/README.md`). `SPECIFICATION/README.md` itself
has a content contract described only for the `livespec` template
seed-time output ("overview that lists the partition files, their
purpose, the BCP 14 convention, and the Gherkin convention"). But:

- Is `SPECIFICATION/README.md` auto-regenerated on every `revise`
  (like the subdirectory READMEs) or authored?
- If authored, it should not be in the "humans SHOULD NOT edit them"
  set. If auto-generated, its content needs to stay stable under
  versioning (to avoid gratuitous diffs).

Pick one and state it.

### S14. Versioning width transition — **ambiguity**

"Width MAY grow beyond three digits as needed" with no rule for when or
how:

- Does `v1000` sort correctly against `v999` in directory listings?
  (Numeric vs lexical sort differs.)
- Does doctor's contiguity check (#6) parse numerically or lexically?
- Do historic `v001-`-prefixed files get renamed when width grows?
  (Almost certainly not — that would break immutability — but the rule
  is not stated.)

Recommend: specify numeric parsing everywhere, specify that width is
max(existing-widths, 3), and that historic files keep their original
widths (so a single `history/` can contain `v099-spec.md` alongside
`v1000-spec.md`).

### S15. Interaction between `propose-change` freeform text and the proposed-change format — **ambiguity**

`propose-change <topic> <freeform text>` produces a file whose body
MUST match the proposed-change format (Summary / Motivation / Proposed
Changes). Does the skill wrap arbitrary freeform text into that
structure, require the user to supply already-conformant text, or
prompt the LLM to reshape? The answer is load-bearing for user
experience and is not specified.

### S16. Seed input preservation — **incompleteness**

The seed text is not preserved after `seed` runs. Consider:
`history/v001/v001-seed.md` preserving the original seed input, so
that (a) the `v001` spec is traceable to its origin and (b) the
recreatability test at v001 is well-defined (you have both the seed
and the output).

### S17. Prior-art attribution obligations — **incompleteness**

`livespec-nlspec-spec.md` references "`prior-art/nlspec-spec.md`" — a
path that doesn't exist in the current brainstorming layout and is
expected to exist after seed (per the acknowledgement's outstanding
follow-ups). The proposal itself does not state the seed-time contract
for copying `nlspec-spec.md` to `SPECIFICATION/prior-art/`. Also: is
there a license/attribution obligation propagated from the upstream
NLSpec repo? Unspecified.

### S18. Doctor LLM-driven phase termination — **ambiguity**

"The LLM-driven phase is skill behavior … has no exit codes." Fine,
but when is it done? After all four check categories have surfaced at
least one finding each? After every finding has received a user
decision (accept / defer / dismiss)? On post-step doctor after a
`revise`, can the user "defer" findings, and if so where is the
deferral state persisted (in-memory? file?)?

Without a termination contract, post-step doctor after every
`seed`/`revise` risks long, non-converging interactive loops.

---

## Smaller Issues, Inconsistencies, and Clean-Ups

### C19. Post-step doctor cascade risk

Post-step doctor may trigger check #9's out-of-band-edit auto-proposal
flow after *every* `revise`. State explicitly whether the post-step
suppresses check #9 (expected: yes, since revise just reconciled the
working tree with `history/vNNN/`).

### C20. `custom_critique_prompt` path existence check

Schema validation (check #1) does not check that the referenced file
exists. Add a separate static check or state that missing-file is an
LLM-phase finding.

### C21. Timestamp precision

"UTC ISO-8601" does not specify precision. Pin to seconds
(`YYYY-MM-DDTHH:MM:SSZ`) for determinism and diff cleanliness.

### C22. `propose-change` overwrite confirmation asymmetry

`propose-change` prompts on collision; `critique` auto-disambiguates.
Either is fine, but the inconsistency is worth calling out — or make
`critique`'s collision rule apply to `propose-change` too (auto-append
disambiguator, never prompt).

### C23. DoD item 6: "four LLM-driven `doctor` check categories"

Enumeration elsewhere yields four top-level categories (NLSpec
conformance, template compliance, drift, internal self-consistency) —
with drift split into three sub-checks. Either the count should say
"four categories, with drift comprising three sub-checks," or
re-enumerate.

### C24. `scenarios.md` seed content explicit example missing

The seed content contract for `scenarios.md` is described in prose; a
fenced example of the *exact* stub would be high-value since Gherkin
blank-line rules are easy to get wrong.

### C25. `proposed_changes/` README regeneration

"Their content is regenerated on every `revise`" — but `revise` that
is a no-op (no proposals, empty freeform) should presumably not touch
these. State the no-op behavior explicitly.

### C26. `revise`'s post-step doctor runs on newly-empty `proposed_changes/`

Check #8 ("Every file in `proposed_changes/` follows the naming
convention") trivially passes on empty; fine, but worth a one-line
note.

### C27. Lifecycle diagram coverage of out-of-band flow

The detailed diagram shows `doctor_static → propose_cmd` via
deterministic findings, but does not specifically depict the check-#9
out-of-band-edit prompt flow. Either add it or state it as an example
of the deterministic-findings edge.

### C28. "A custom template SHOULD NOT use `intent` as a filename"

SHOULD NOT, but custom templates are rejected in v1 entirely (check
#13). The rule is therefore inert in v1 and adds surface area. Either
remove or move to a v2-looking-forward note.

### C29. `scenarios.md` block-rendering contract

The contract is "renders predictably as Markdown paragraphs" with no
fenced `gherkin` info-string. State what renderer surface this is
being contracted against (GitHub's GFM? CommonMark?). This was
partially addressed but the renderer target is still ambiguous.

### C30. Meta-test heading-reference mechanism

"Reference by exact heading text" — is the reference a string literal
in the test, a decorator/annotation, or a registry file?
Underspecified.

### C31. Intent taxonomy → sub-command mapping

"Observations" vs "implementation feedback" vs "external requirements"
(guidelines' intent taxonomy) are not mapped to sub-commands.
Everything flows through `propose-change` or `critique` in practice —
state this explicitly so the taxonomy doesn't appear to promise more
than the skill provides.

---

## Application of the Recreatability Test

> *If the implementation were destroyed and only the specification
> remained, could a competent implementer faithfully recreate the
> system?*

Applied to the v002 corpus:

- **Recreatable:** the conceptual model, directory shape, versioning
  rules, doctor static-check inventory, proposed-change and
  acknowledgement file formats, the Definition of Done.
- **Not recreatable without load-bearing guesses:** the skill's Claude
  Code packaging form, the static-phase script's language and output
  contract, the critique prompt's output-shape contract, the user-
  prompt mediation (seed input, revise confirmation, out-of-band edit
  flow), the `modify`-decision diff authoring flow, the `openspec`
  partial-implementation error path, and the exact content of
  `SPECIFICATION/README.md` and the initial `.livespec.jsonc` on disk.

**Verdict: v002 is materially closer to seedable than v001.** It now
has a Definition of Done, a template contract, a versioning contract,
and an acknowledged list of non-goals with rationale. But the
recreatability test still fails at the **skill-implementation contract
layer** and at **several LLM-phase / static-phase handoff points**. A
seed run today would produce a `spec.md` that is conceptually coherent
but operationally vague at exactly the boundaries where two
implementers would make incompatible choices.

---

## Recommended Path to a Seedable Spec

Blockers (do in this round):

1. Define the Claude Code skill packaging contract — SKILL.md (or its
   equivalent), `allowed-tools`, script invocation idiom. At minimum a
   one-section "Skill packaging contract" that names the file layout
   inside `.claude/skills/livespec/` and the dispatch model.
2. Pin the static-phase script's language (or explicitly leave it
   "implementer's choice but must satisfy this output contract" and
   specify the output contract — structured JSON with `check_id`,
   `status`, `message`, `path`, `line` fields is the natural choice).
3. Specify the `critique` output-shape contract: does the critique
   prompt produce a conformant proposed-change file end-to-end, or
   does the skill wrap raw critique output into the required
   structure?
4. Specify the `modify`-decision flow: who authors the modification,
   what goes into `## Modifications`, whether the proposed-change file
   is rewritten.
5. Specify `openspec`'s v1 partial-implementation error path (which
   sub-command, which message, which check code).
6. Delete the "per the progressive-disclosure mapping below" dangling
   reference.
7. Tighten doctor checks #10 and #11 to rules that can actually be
   implemented by a static script.
8. Specify on-disk content of `.livespec.jsonc` on first `seed`.
9. Specify whether seed input is preserved (`v001-seed.md` under
   `history/v001/`).
10. Specify whether `revise` with freeform-only modifications
    auto-creates an ephemeral proposed-change, or state that
    freeform-only revise is disallowed (must go through
    `propose-change` first).

Not blockers (defer to first post-seed `propose-change` batch):

- Items 12–18 in the Significant Gaps section (cross-file reference
  scope, timestamp precision, LLM-phase termination, version-width
  transition rules, attribution licensing, etc.).
- Lifecycle diagram coverage of the out-of-band edit flow.
- All Smaller Issues items.

Items that this critique recommends **not** accepting:

- Nothing outright. The v1 non-goal boundary (subdomain routing,
  multi-spec-per-project, git integration, custom-template loading,
  holdout runner) should stay held.

---

## Notes on Material Outside `PROPOSAL.md`

- `livespec-nlspec-spec.md` is the main dependency and should remain
  intact. Its reference to `prior-art/nlspec-spec.md` needs the
  seed-time file-move contract stated in `PROPOSAL.md` itself, not
  only in the v002 acknowledgement's follow-up list.
- `goals-and-non-goals.md` and `subdomains-and-unsolved-routing.md`
  remain the strongest companion documents for preserving rationale.
  Their post-seed migration plan (into a Boundary Clarification
  appendix in `spec.md` / a reference in `SPECIFICATION/README.md`) is
  correctly listed in the v002 acknowledgement but should be promoted
  to a named item in PROPOSAL.md's Self-application step sequence
  (currently step 5 is "Land the v1 DoD items" — too coarse).
- `2026-04-19-nlspec-lifecycle-diagram-detailed.md` is accurate and
  useful. Embed it (not the simpler diagram) in the seeded `spec.md`,
  with the out-of-band-edit flow added.
- The `history/v001/` and `history/v002/` backfill is an excellent
  worked example of the mechanism. Keep it after seed as a prior-art
  artifact demonstrating the lifecycle in anger.
