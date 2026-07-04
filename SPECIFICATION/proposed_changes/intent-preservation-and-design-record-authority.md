---
topic: intent-preservation-and-design-record-authority
author: claude-fable-5
created_at: 2026-07-04T05:52:59Z
---

## Proposal: Intent preservation and design-record authority — fleet-wide generalization

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/scenarios.md

### Summary

Add a new `## Intent preservation and design-record authority` section to `SPECIFICATION/spec.md` (inserted immediately BEFORE §"Sub-command lifecycle") binding every livespec-governed specification tree fleet-wide: (1) every load-bearing semantic definition MUST carry its plain-English rationale and MUST cite its design record with a repo-qualified citation, and a definition without a reachable design record is incomplete, not merely unadorned; (2) when ratified statements conflict, the cited design record — the recorded maintainer intent — is the tiebreaker, and consistency with the shipped implementation is NEVER the tiebreaker; (3) a conflict with no cited or reachable design record is itself a finding that MUST be surfaced to the maintainer and MUST NOT be self-resolved in either direction; (4) operationally, `critique` MUST surface conflicts together with the cited design record's position, and `revise` MUST NOT ratify a resolution contradicting a cited design record without the maintainer explicitly acknowledging the contradiction in the decision. A paired `scenarios.md` H2 gives the new behavior clauses their Given/When/Then home. The proposal records the ratification-time co-edits: `tests/heading-coverage.json` for the two added H2 headings, and the operational prose artifacts `.claude-plugin/prose/critique.md` / `.claude-plugin/prose/revise.md`, all riding the same revise `resulting_files[]`.

### Motivation

Fleet-wide generalization of the intent-preservation clauses proven necessary by the 2026-07-03/04 intent-inversion incident in repo `thewoolleyman/livespec-orchestrator-beads-fabro`. The maintainer's locked design (approval IS the `pending-approval → ready` transition; decisions 26 and 32 in repo `thewoolleyman/livespec` at `plan/archive/work-item-state-machine/research/03-decision-log.md`) was faithfully encoded in that repo's v020 contracts — but the SAME revision ratified a scenario expressed in legacy vocabulary that contradicted the contracts beside it; the implementation was then built from the scenario; a later critique found the contradiction and the v023 revise resolved it TOWARD the shipped code — the opposite of the recorded intent; and a follow-up proposal nearly completed the drift before the maintainer caught it (rejected at that repo's `SPECIFICATION/history/v027/`). Root cause: the spec records rules but not meaning or rationale, carries no link to the design record that does, and its authority model gives corrupted ratified text precedence over preserved intent — so an agent resolving an ambiguity converges on whatever the implementation already does. The maintainer's directive (2026-07-04): fix whatever the gaps were to "clearly describe the intent and ensure that it is preserved", so that "this sort of thing doesn't happen in the future". The orchestrator repo's pending per-repo fix (its `SPECIFICATION/proposed_changes/approval-is-the-pending-approval-to-ready-transition.md`, section G) binds that spec tree only and explicitly defers the fleet-wide generalization to livespec core — this proposal is that generalization. Placement reasoning: the rules bind every project GOVERNED by livespec, so by the boundary litmus (`non-functional-requirements.md` §"Boundary") they belong in the user-facing functional files, not `non-functional-requirements.md`; they carry no wire shape (no CLI argv, exit code, or JSON schema), so not `contracts.md`; they are authority semantics of the specification model and its lifecycle operations — not a mechanically-checkable content-format rule like BCP14 or heading taxonomy — so `spec.md` rather than `constraints.md`; and §"Self-application" covers only this repository's own tree, while these rules bind every governed tree, so a new dedicated H2 (placed directly after §"Lifecycle", whose authority-of-intent terminology it extends) is the correct home. The in-spec rationale requirement deliberately keeps each tree readable standalone, preserving the purpose of `constraints.md` §"Reference discipline"; the new section states that interaction explicitly.

### Proposed Changes

**A. New `## Intent preservation and design-record authority` section in `SPECIFICATION/spec.md`.**

A new `## ` H2 section MUST be inserted into `SPECIFICATION/spec.md` immediately BEFORE §"Sub-command lifecycle" (so it directly follows §"Lifecycle", whose terminology it extends), with exactly this content:

```markdown
## Intent preservation and design-record authority

A ratified specification records rules; the meaning of those rules — why the maintainer chose them — lives in the design record that produced them. When the two are severed, an agent resolving an ambiguity converges on whatever the implementation already does, and recorded intent silently inverts. This section binds every livespec-governed specification tree, including this repository's own tree (per §"Self-application"), so that preserved maintainer intent — never shipped code — settles what a contested statement means.

**Vocabulary.** A **design record** is a durable artifact preserving the maintainer intent behind a specification statement: a planning thread, a decision log, a design document, or a preserved conversation transcript. A **repo-qualified citation** names the owning repository and the record's path within it, in plain text — for example: repo `thewoolleyman/livespec`, `plan/archive/work-item-state-machine/research/03-decision-log.md`, decisions 26 and 32 — plus decision identifiers wherever the record numbers its decisions. A **load-bearing semantic definition** is a statement fixing what a state, transition, term, or invariant MEANS — a statement other statements are subordinate to, such that reading it differently would change conforming behavior.

**Rationale-and-citation requirement.** Every load-bearing semantic definition in a livespec-governed specification tree MUST carry its rationale — the WHY, in plain English, quoting the deciding conversation where one is preserved — and MUST cite its design record with a repo-qualified citation. A semantic definition without a reachable design record is incomplete, not merely unadorned: its next reader inherits a rule whose meaning cannot be recovered, and unrecoverable meaning is the precondition for drift.

**The intent tiebreaker.** When ratified statements of a specification are found to conflict — by critique, doctor, revise, or any reader — the cited design record, the recorded maintainer intent, is the tiebreaker. Consistency with the shipped implementation is NEVER the tiebreaker: an implementation built from one side of a contradiction is evidence of nothing but the contradiction's age. A conflict resolution MUST be derived from the cited design record's position, not from which side the code implements.

**Missing record is a maintainer finding.** If no design record is cited or reachable for the conflicting statements, that absence is itself a finding that MUST be surfaced to the maintainer together with the conflict. The conflict MUST NOT be self-resolved in either direction.

**Operational reach.** These rules bind the lifecycle operations concretely:

- `critique` MUST surface every detected conflict between ratified statements together with the cited design record's position on it, when such a record exists — not merely the fact of the conflict.
- `revise` MUST NOT ratify a resolution that contradicts a cited design record unless the maintainer explicitly acknowledges the contradiction in the revision record's decision (the `## Decision and Rationale` body naming the departed-from record and the deliberate departure).
- `doctor`'s LLM-driven phases, and any other reader that detects a conflict, MUST apply the same tiebreaker and the same missing-record escalation.

**Interaction with reference discipline.** The in-spec rationale carries the meaning, so the tree stays readable standalone — the same purpose `constraints.md` §"Reference discipline" protects. A design-record citation is a plain-text repo-qualified pointer: it MUST NOT be a URL, and it MUST NOT use the `§"…"` cross-spec heading-reference form for a sibling repository's spec content except via the reference-discipline allowlist.

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

**C. Prose co-update at ratification (recorded choice).**

Core's prose artifacts `.claude-plugin/prose/critique.md` and `.claude-plugin/prose/revise.md` carry the operational instructions for the two operations the "Operational reach" clauses bind, and they MUST be co-updated when this proposal ratifies: critique's finding-assembly steps MUST instruct surfacing each detected conflict together with the cited design record's position; revise's decision-capture steps MUST instruct refusing to ratify a resolution that contradicts a cited design record unless the maintainer explicitly acknowledges the contradiction in the decision. Recorded choice, following this repository's established convention (precedent: the v107 revision record's `## Resulting Changes` carried `../.claude-plugin/prose/next.md`): the prose co-update MUST ride the SAME revise `resulting_files[]`, with paths spelled `../.claude-plugin/prose/critique.md` and `../.claude-plugin/prose/revise.md` (the `../` prefix makes the revise wrapper's `spec_target / path` join resolve them project-root-relative when `--spec-target` is the main `SPECIFICATION/` tree), so the ratification commit lands the spec text and the operational prose atomically. No separate work-item is filed for the prose edit.

**D. Ratification-time `tests/heading-coverage.json` co-edit.**

This proposal ADDS two `## ` H2 headings: `## Intent preservation and design-record authority` in `spec.md` and `## Conflicting ratified statements resolve toward the cited design record` in `scenarios.md`. Per the revise co-edit discipline (`spec.md` §"Self-application"), ratification MUST land the `tests/heading-coverage.json` co-edit via the same revise `resulting_files[]` (path spelled `../tests/heading-coverage.json`): one new entry per added heading (`test` MAY be `"TODO"` with a non-empty `reason`, per the established pattern), and `clauses[]` links binding each new load-bearing `MUST` clause's gap-id to the new `scenarios.md` H2 section, so the clause-to-scenario map stays in lockstep with the spec.

