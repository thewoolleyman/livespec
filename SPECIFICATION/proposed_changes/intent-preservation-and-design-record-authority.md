---
topic: intent-preservation-and-design-record-authority
author: claude-fable-5
created_at: 2026-07-04T05:52:59Z
---

## Proposal: Intent preservation and design-record authority — fleet-wide generalization

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/scenarios.md
- SPECIFICATION/constraints.md

### Summary

Add a new `## Intent preservation and design-record authority` section to `SPECIFICATION/spec.md` (inserted immediately BEFORE §"Sub-command lifecycle") binding every livespec-governed specification tree fleet-wide: (1) every load-bearing semantic definition MUST carry its plain-English rationale and MUST cite its design record with a repo-qualified citation, and a definition without a reachable design record is incomplete, not merely unadorned; (2) when ratified statements conflict, the cited design record — the recorded maintainer intent — is the tiebreaker, and consistency with the shipped implementation MUST NOT be the tiebreaker; (3) a conflict with no cited or reachable design record is itself a finding that MUST be surfaced to the maintainer and MUST NOT be self-resolved in either direction; (4) operationally, `critique` MUST surface conflicts together with the cited design record's position, and `revise` MUST NOT ratify a resolution contradicting a cited design record without the maintainer explicitly acknowledging the contradiction in the decision. A paired `scenarios.md` H2 gives the new behavior clauses their Given/When/Then home. In the SAME proposal, `constraints.md` §"Reference discipline" gains a tightly scoped **design-record-citation carve-out** — without it, the citation mandate and the ratified prohibition on referencing non-`SPECIFICATION/` paths in sibling repos would be conflicting ratified statements. The proposal carries the ratification-ready verbatim edit text for the operational prose artifacts `.claude-plugin/prose/critique.md` and `.claude-plugin/prose/revise.md`, and records the ratification-time co-edits: `tests/heading-coverage.json` for the two added H2 headings, and the prose artifacts, all riding the same revise `resulting_files[]`.

### Motivation

Fleet-wide generalization of the intent-preservation clauses proven necessary by the 2026-07-03/04 intent-inversion incident in repo `thewoolleyman/livespec-orchestrator-beads-fabro`. The maintainer's locked design (approval IS the `pending-approval → ready` transition; decisions 26 and 32 in repo `thewoolleyman/livespec` at `plan/archive/work-item-state-machine/research/03-decision-log.md`) was faithfully encoded in that repo's v020 contracts — but the SAME revision ratified a scenario expressed in legacy vocabulary that contradicted the contracts beside it; the implementation was then built from the scenario; a later critique found the contradiction and the v023 revise resolved it TOWARD the shipped code — the opposite of the recorded intent; and a follow-up proposal nearly completed the drift before the maintainer caught it (rejected at that repo's `SPECIFICATION/history/v027/`). Root cause: the spec records rules but not meaning or rationale, carries no link to the design record that does, and its authority model gives corrupted ratified text precedence over preserved intent — so an agent resolving an ambiguity converges on whatever the implementation already does. The maintainer's directive (2026-07-04): fix whatever the gaps were to "clearly describe the intent and ensure that it is preserved", so that "this sort of thing doesn't happen in the future". The orchestrator repo's pending per-repo fix (its `SPECIFICATION/proposed_changes/approval-is-the-pending-approval-to-ready-transition.md`, section G) binds that spec tree only and explicitly defers the fleet-wide generalization to livespec core — this proposal is that generalization.

Placement reasoning: the rules bind every project GOVERNED by livespec, so by the boundary litmus (`non-functional-requirements.md` §"Boundary") they belong in the user-facing functional files, not `non-functional-requirements.md`; they carry no wire shape (no CLI argv, exit code, or JSON schema), so not `contracts.md`; they are authority semantics of the specification model and its lifecycle operations — not a mechanically-checkable content-format rule like BCP14 or heading taxonomy — so `spec.md` rather than `constraints.md`; and §"Self-application" covers only this repository's own tree, while these rules bind every governed tree, so a new dedicated H2 (placed directly after §"Lifecycle", whose authority-of-intent terminology it extends) is the correct home. The citation FORM, by contrast, IS reference-discipline (content-format) territory, so its carve-out (section C below) lands in `constraints.md` §"Reference discipline" beside the prohibitions it scopes.

Amendment provenance (2026-07-04): an independent read-only verification of the originally filed proposal returned one blocker — the fleet-wide citation mandate REQUIRES repo-qualified references to design records at non-`SPECIFICATION/` paths (in the citing repo and in sibling repos; the motivating case is the orchestrator repo's pending proposal citing repo `thewoolleyman/livespec`'s `plan/archive/work-item-state-machine/research/03-decision-log.md` from inside its own spec tree), but `constraints.md` §"Reference discipline" declared references to non-`SPECIFICATION/` paths in sibling repos "absolutely forbidden" with no allowlist escape, so ratifying as originally filed would have created conflicting ratified statements. This amendment adds `SPECIFICATION/constraints.md` to the target files and amends §"Reference discipline" in the same proposal (section C). The carve-out shape is preferred over routing design-record citations through the `external_references` allowlist because citations are meant to be ubiquitous and low-friction — a per-citation allowlist entry would tax exactly the behavior the mandate requires everywhere. The amendment also folds in the verifier's advisories: ratification-ready verbatim edit text for the two prose artifacts (section D), the shared-resulting-file merge note (section E), and BCP14-consistent emphasis (`MUST NOT`) in the new normative text.

### Proposed Changes

**A. New `## Intent preservation and design-record authority` section in `SPECIFICATION/spec.md`.**

A new `## ` H2 section MUST be inserted into `SPECIFICATION/spec.md` immediately BEFORE §"Sub-command lifecycle" (so it directly follows §"Lifecycle", whose terminology it extends), with exactly this content:

```markdown
## Intent preservation and design-record authority

A ratified specification records rules; the meaning of those rules — why the maintainer chose them — lives in the design record that produced them. When the two are severed, an agent resolving an ambiguity converges on whatever the implementation already does, and recorded intent silently inverts. This section binds every livespec-governed specification tree, including this repository's own tree (per §"Self-application"), so that preserved maintainer intent — never shipped code — settles what a contested statement means.

**Vocabulary.** A **design record** is a durable artifact preserving the maintainer intent behind a specification statement: a planning thread, a decision log, a design document, or a preserved conversation transcript. A **repo-qualified citation** names the owning repository and the record's path within it, in plain text — for example: repo `thewoolleyman/livespec`, `plan/archive/work-item-state-machine/research/03-decision-log.md`, decisions 26 and 32 — plus decision identifiers wherever the record numbers its decisions. A **load-bearing semantic definition** is a statement fixing what a state, transition, term, or invariant MEANS — a statement other statements are subordinate to, such that reading it differently would change conforming behavior.

**Rationale-and-citation requirement.** Every load-bearing semantic definition in a livespec-governed specification tree MUST carry its rationale — the WHY, in plain English, quoting the deciding conversation where one is preserved — and MUST cite its design record with a repo-qualified citation. A semantic definition without a reachable design record is incomplete, not merely unadorned: its next reader inherits a rule whose meaning cannot be recovered, and unrecoverable meaning is the precondition for drift.

**The intent tiebreaker.** When ratified statements of a specification are found to conflict — by critique, doctor, revise, or any reader — the cited design record, the recorded maintainer intent, is the tiebreaker. Consistency with the shipped implementation MUST NOT be the tiebreaker: an implementation built from one side of a contradiction is evidence of nothing but the contradiction's age. A conflict resolution MUST be derived from the cited design record's position, not from which side the code implements.

**Missing record is a maintainer finding.** If no design record is cited or reachable for the conflicting statements, that absence is itself a finding that MUST be surfaced to the maintainer together with the conflict. The conflict MUST NOT be self-resolved in either direction.

**Operational reach.** These rules bind the lifecycle operations concretely:

- `critique` MUST surface every detected conflict between ratified statements together with the cited design record's position on it, when such a record exists — not merely the fact of the conflict.
- `revise` MUST NOT ratify a resolution that contradicts a cited design record unless the maintainer explicitly acknowledges the contradiction in the revision record's decision (the `## Decision and Rationale` body naming the departed-from record and the deliberate departure).
- `doctor`'s LLM-driven phases, and any other reader that detects a conflict, MUST apply the same tiebreaker and the same missing-record escalation.

**Interaction with reference discipline.** The in-spec rationale carries the meaning, so the tree stays readable standalone — the same purpose `constraints.md` §"Reference discipline" protects. A design-record citation is PROVENANCE, not required reading: `constraints.md` §"Reference discipline" authorizes it, as a narrow exception, to name a non-`SPECIFICATION/` design-record path in the citing repo or in a sibling repo. The citation MUST NOT be a URL, and it MUST NOT use the `§"…"` cross-spec heading-reference form for a sibling repository's spec content except via the reference-discipline allowlist. An unreachable design record degrades to a maintainer-surfaced finding per the missing-record rule above — never to an unreadable tree.

**This section's own design record** (self-compliance): the incident that produced this policy — a maintainer-locked work-item state-machine design whose faithful contract text was eroded across successive revisions toward the shipped implementation, caught and reverted by the maintainer — has its locked design recorded in repo `thewoolleyman/livespec` at `plan/archive/work-item-state-machine/research/03-decision-log.md` (decisions 26 and 32), with the session's verbatim reasoning preserved in `plan/archive/work-item-state-machine/conversation/transcript.md`. The maintainer's deciding directive (2026-07-04): fix whatever the gaps were to "clearly describe the intent and ensure that it is preserved", so that "this sort of thing doesn't happen in the future".
```

**B. New scenario H2 in `SPECIFICATION/scenarios.md`.**

A new `## ` H2 section MUST be appended to `SPECIFICATION/scenarios.md` after §"Behavior clause lacking a scenario link is surfaced", with exactly this content (per the behavior ⇒ scenario authoring split, the new section's MUST clauses are load-bearing behavior and need a Given/When/Then home):

````markdown
## Conflicting ratified statements resolve toward the cited design record

```gherkin
Feature: Intent preservation — the cited design record is the tiebreaker
  As a maintainer whose recorded design decisions must outlive any one session
  I want conflicts between ratified statements resolved toward the cited design record
  So that a contradiction is never silently resolved toward whatever the implementation already does

Scenario: Critique surfaces a conflict together with the design record's position
  Given a ratified spec tree carries two statements that contradict each other
  And the load-bearing semantic definition involved cites a reachable design record
  When the user invokes the critique operation
  Then the critique finding states the conflict and the cited design record's position on it
  And the finding does not treat the shipped implementation's side as the presumed resolution

Scenario: Revise does not ratify a resolution that contradicts a cited design record
  Given a pending proposed change resolves a conflict against the cited design record's position
  When the user invokes the revise operation
  And the maintainer's decision does not explicitly acknowledge the contradiction
  Then the resolution is not ratified as filed
  And the cited design record's position is surfaced for the maintainer's explicit decision

Scenario: A conflict with no reachable design record is escalated, never self-resolved
  Given a ratified spec tree carries two statements that contradict each other
  And no design record is cited or reachable for either statement
  When any lifecycle operation detects the conflict
  Then the missing design record is surfaced to the maintainer as a finding alongside the conflict
  And the conflict is not self-resolved in either direction
```
````

**C. Design-record-citation carve-out in `SPECIFICATION/constraints.md` §"Reference discipline".**

Without this edit, the section-A citation mandate and the ratified reference-discipline prohibitions would be conflicting ratified statements — the exact condition this proposal exists to prevent. Three edits, each quoting its replace-target verbatim from the live file, plus one inserted subsection:

C1. In the `constraints.md` subsection §"Forbidden: references OUTSIDE the same `SPECIFICATION/` tree", the intro sentence

```markdown
A `SPECIFICATION/<file>.md` MUST NOT reference any of the following EXCEPT via the allowlist mechanism in §"Allowlist mechanism":
```

MUST be replaced with:

```markdown
A `SPECIFICATION/<file>.md` MUST NOT reference any of the following EXCEPT via the allowlist mechanism in §"Allowlist mechanism" or — for design-record citations only — the authorized exception in §"Design-record citations (authorized exception)":
```

C2. In the same subsection, the closing paragraph

```markdown
The invariant exists because a `SPECIFICATION/` tree MUST be readable standalone — a reader with only the tree's files in hand MUST be able to resolve every reference. Cross-repo coordination contracts inherently need to name parent-spec content; the allowlist mechanism is the supported escape hatch, NOT an open license to scatter cross-repo citations through prose.
```

MUST be replaced with:

```markdown
The invariant exists because a `SPECIFICATION/` tree MUST be readable standalone — a reader with only the tree's files in hand MUST be able to resolve every reference the tree's meaning depends on. Cross-repo coordination contracts inherently need to name parent-spec content; the allowlist mechanism is the supported escape hatch, NOT an open license to scatter cross-repo citations through prose. Design-record citations are the one further exception, per §"Design-record citations (authorized exception)" below: they are provenance pointers whose accompanying in-tree rationale keeps the tree readable standalone.
```

C3. A new H3 subsection §"Design-record citations (authorized exception)" MUST be inserted immediately after §"Forbidden: references OUTSIDE the same `SPECIFICATION/` tree" (i.e., between it and the source-code-citation subsection that follows), with exactly this content:

```markdown
### Design-record citations (authorized exception)

A **design-record citation** — the plain-text, repo-qualified pointer to the design record behind a load-bearing semantic definition, required by `spec.md` §"Intent preservation and design-record authority" (repository name plus the record's path within it, plus decision identifiers where the record numbers its decisions) — is an authorized exception to the prohibition on referencing non-`SPECIFICATION/` paths in sibling repos, and equally covers non-`SPECIFICATION/` design-record paths in the citing repo itself (e.g., a `plan/<topic>/` thread archive). No allowlist entry is required: design-record citations are meant to be ubiquitous and low-friction, and a per-citation allowlist entry would tax exactly the behavior the mandate requires everywhere.

The exception does NOT weaken standalone readability, because a design-record citation is PROVENANCE, not required reading: the rationale itself MUST still be carried (quoted or summarized) in-tree beside the definition, so a reader with only the tree's files in hand loses nothing; an unreachable design record degrades to a maintainer-surfaced finding (per the missing-record rule of `spec.md` §"Intent preservation and design-record authority"), never to an unreadable tree.

The exception is narrow: it covers design-record citations ONLY. It does NOT authorize general prose links, implementation-tree paths, work-item identifiers, epic phase identifiers, version-control identifiers, or URLs; a design-record citation itself MUST NOT be a URL and MUST NOT use the `§"…"` heading-reference form (which stays governed by §"Allowlist mechanism").
```

C4. In §"Allowlist mechanism", the closing sentence

```markdown
Any `§"…"` reference to a sibling-repo spec heading MUST appear in the allowlist; references to non-`SPECIFICATION/` paths in sibling repos remain absolutely forbidden.
```

MUST be replaced with:

```markdown
Any `§"…"` reference to a sibling-repo spec heading MUST appear in the allowlist; references to non-`SPECIFICATION/` paths in sibling repos remain forbidden EXCEPT for design-record citations per §"Design-record citations (authorized exception)".
```

**D. Prose co-update at ratification (recorded choice, with ratification-ready text).**

Core's prose artifacts `.claude-plugin/prose/critique.md` and `.claude-plugin/prose/revise.md` carry the operational instructions for the two operations the "Operational reach" clauses bind, and they MUST be co-updated when this proposal ratifies. Recorded choice, following this repository's established convention (precedent: the v107 revision record's `## Resulting Changes` carried `../.claude-plugin/prose/next.md`): the prose co-update MUST ride the SAME revise `resulting_files[]`, with paths spelled `../.claude-plugin/prose/critique.md` and `../.claude-plugin/prose/revise.md` (the `../` prefix makes the revise wrapper's `spec_target / path` join resolve them project-root-relative when `--spec-target` is the main `SPECIFICATION/` tree), so the ratification commit lands the spec text and the operational prose atomically. No separate work-item is filed for the prose edit. The verbatim edits (anchors quoted exactly from the live files; indentation matches the surrounding numbered-list/bullet style):

D1. `.claude-plugin/prose/critique.md`, §Steps step 4 ("**Generate findings JSON.**"): immediately after the step's final line

```markdown
   resolves it per the four-step precedence.
```

a new paragraph MUST be appended to the same step:

```markdown

   Per `SPECIFICATION/spec.md` §"Intent preservation and
   design-record authority", when a finding reports a
   conflict between ratified statements, the finding MUST
   state the cited design record's position on the conflict
   when such a record exists (not merely the fact of the
   conflict), MUST NOT treat consistency with the shipped
   implementation as the presumed resolution, and — when no
   design record is cited or reachable for the conflicting
   statements — MUST surface that absence as part of the
   finding for the maintainer instead of self-resolving the
   conflict in either direction.
```

D2. `.claude-plugin/prose/revise.md`, §Steps step 5 ("**Per-proposal decision dialogue.**"): immediately after the first bullet's final line

```markdown
     `accept` / `modify`) the updated `resulting_files[]`.
```

a new bullet MUST be inserted (before the "**Prompt the user for confirmation.**" bullet):

```markdown
   - **Intent-preservation gate** (per `SPECIFICATION/spec.md`
     §"Intent preservation and design-record authority").
     Before presenting a decision that resolves a conflict
     between ratified statements, check the resolution
     against the design record cited by the load-bearing
     semantic definition involved. A resolution that
     contradicts a cited design record MUST NOT be presented
     for ratification unless the presentation names the
     contradiction explicitly and the maintainer's confirmed
     decision acknowledges it (the acknowledgment lands in
     the revision record's `## Decision and Rationale` body,
     naming the departed-from record and the deliberate
     departure). When no design record is cited or reachable
     for the conflicting statements, surface that absence to
     the maintainer together with the conflict; the dialogue
     MUST NOT self-resolve it in either direction — and the
     "delegate remaining proposals to the LLM" toggle never
     delegates this acknowledgment: a delegated pass reaching
     such a contradiction MUST fall back to the explicit
     per-proposal confirmation for that proposal.
```

D3. `.claude-plugin/prose/revise.md`, §Post-CLI, the revision-file-format bullet: the line

```markdown
  `## Decision and Rationale` (always),
```

MUST be replaced with:

```markdown
  `## Decision and Rationale` (always; when the accepted
  resolution departs from a cited design record, this body
  MUST name the departed-from record and the deliberate
  departure, per SPECIFICATION/spec.md §"Intent preservation
  and design-record authority"),
```

**E. Ratification-time `tests/heading-coverage.json` co-edit (and shared-file merge note).**

This proposal ADDS two `## ` H2 headings: `## Intent preservation and design-record authority` in `spec.md` and `## Conflicting ratified statements resolve toward the cited design record` in `scenarios.md`. The `constraints.md` edit (section C) adds NO `## ` H2 heading and renames none — it adds one `### ` H3 subsection and edits prose within existing subsections — so it contributes no heading-coverage entry change. Per the revise co-edit discipline (`spec.md` §"Self-application"), ratification MUST land the `tests/heading-coverage.json` co-edit via the same revise `resulting_files[]` (path spelled `../tests/heading-coverage.json`): one new entry per added heading (`test` MAY be `"TODO"` with a non-empty `reason`, per the established pattern), and `clauses[]` links binding each new load-bearing `MUST` clause's gap-id to the new `scenarios.md` H2 section, so the clause-to-scenario map stays in lockstep with the spec. The section-C carve-out's new normative clauses in `constraints.md` are content-format rules; where one maps to a scenario (the missing-record degradation maps to the third scenario block of the new `scenarios.md` H2), ratification SHOULD add the corresponding `clauses[]` link, and any clause left unlinked lands in the existing warn-mode backlog surfaced by the `behavior_scenario_link` check.

Shared-resulting-file merge note: if this proposal ratifies in the SAME revise pass as the pending `fleet-merged-branch-cleanup.md`, and both decisions carry `../tests/heading-coverage.json` in their `resulting_files[]`, the file content MUST merge BOTH proposals' deltas — a later decision's full-content write MUST NOT silently drop the earlier decision's entries. (That sibling proposal's own missing `clauses[]` co-edit is its own gap, reported to the maintainer separately; it is deliberately NOT fixed here.)
