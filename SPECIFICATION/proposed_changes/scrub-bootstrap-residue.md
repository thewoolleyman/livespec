---
topic: scrub-bootstrap-residue
author: claude-opus-4-7
created_at: 2026-05-10T08:10:11Z
---

## Proposal: Scrub bootstrap-process residue from spec.md

### Target specification files

- SPECIFICATION/spec.md

### Summary

spec.md carries two bootstrap-process residue references that have outlived their purpose now that bootstrap closed at Phase 11: line 104 forecasts Phase 3 → Phase 7 widening of `prune-history`; line 185 frames the self-application as a Phase-6-bound event with a Phase-6-closed imperative window. Restate both in present tense without the phase pointers. Tracking issue: li-i4h.

### Motivation

Both lines reference the bootstrap-process phase numbering (Phase 3, Phase 6, Phase 7) that is no longer load-bearing — the bootstrap plan is archived under `archive/`, the phases have all closed, and the spec should describe the current contract in present tense rather than the contract's authoring history. The Phase-N pointers add reader-archaeology cost (a new contributor must understand what each phase was, when it closed, and whether the forecasted widening landed) and bit-rot risk (the spec drifts from reality as referenced phases complete or shift).

### Proposed Changes

Two edits in `SPECIFICATION/spec.md`:

**Edit 1 — line 104 trailing sentence.** Delete the trailing sentence `Phase 3 lands the parser-only stub; Phase 7 widens it to the actual pruning mechanic.` from §"Pruning history". The preceding sentence already states the contract ("`prune-history` MAY remove the oldest contiguous block of `history/v*/` directories down to a caller-specified retention horizon while preserving the contiguous-version invariant for the remaining tail."); the deleted sentence adds only authoring-history information that is not part of the live contract.

**Edit 2 — line 185, §"Self-application".** Replace the existing paragraph:

> `livespec` is self-applied: this very `SPECIFICATION/` tree is the seeded output of running `/livespec:seed` against the project's own brainstorming archive. The Phase 6 self-application was bootstrap-only; the imperative window closed at the Phase 6 seed commit and remains closed. All subsequent mutations to this `SPECIFICATION/` MUST flow through `/livespec:propose-change` → `/livespec:revise` against this tree (or, for the two sub-spec trees under `templates/`, against the corresponding sub-spec target).

With the present-tense rewrite:

> `livespec` is self-applied: this very `SPECIFICATION/` tree was seeded by running `/livespec:seed` against the project's own brainstorming archive. The initial bootstrap self-application is closed. All mutations to this `SPECIFICATION/` MUST flow through `/livespec:propose-change` → `/livespec:revise` against this tree (or, for the two sub-spec trees under `templates/`, against the corresponding sub-spec target).

No other change is required; the load-bearing rules (self-application, propose-change/revise as the only mutation path, the sub-spec-target carve-out) are preserved verbatim minus the Phase-6 phase reference.

## Proposal: Scrub bootstrap-process residue from contracts.md

### Target specification files

- SPECIFICATION/contracts.md

### Summary

contracts.md carries two bootstrap-process residue references: line 17's Wrapper CLI surface table cell for `resolve-template` says `(Phase-3-min required; Phase-7 widens to optional)`; line 166 references `Phase 7 items (c) and (d)` describing per-prompt regeneration cycles. Restate both in present tense. Tracking issue: li-i4h.

### Motivation

The Phase-3-min / Phase-7 framing in the Wrapper CLI surface table forecasts a contract change (required → optional) that was tied to the bootstrap plan; today the spec MUST describe the current contract directly. Whether `--template` is currently required or optional is a single-bit fact that the table cell should state outright. Similarly, line 166's `Phase 7 items (c) and (d)` reference points to a closed bootstrap step rather than a current rule.

### Proposed Changes

Two edits in `SPECIFICATION/contracts.md`:

**Edit 1 — line 17, Wrapper CLI surface table row for `resolve-template`.** Delete the parenthetical `(Phase-3-min required; Phase-7 widens to optional)` from the "Required flags" cell. The cell's content for `resolve-template` becomes simply `--template <value>`. The current implementation requires `--template` (verifiable by running `bin/resolve_template.py` without it — the wrapper exits 2). If a future revision changes that contract, the table cell gets updated then; today the table MUST reflect today's contract.

**Edit 2 — line 166, end of §"Prompt-QA harness contract".** Replace the existing sentence:

> Per-prompt regeneration cycles in Phase 7 items (c) and (d) update fixtures alongside their prompts — if a regenerated prompt no longer satisfies the per-template catalogue's properties, the prompt-QA test fails and the regeneration is rejected.

With the present-tense rewrite:

> When per-prompt regeneration cycles update fixtures alongside their prompts, the prompt-QA test fails the regeneration if the regenerated prompt no longer satisfies the per-template catalogue's properties.

The load-bearing rule (regeneration coupled to fixture update; QA test rejects mismatched regenerations) is preserved; the Phase-7-bound `items (c) and (d)` reference is dropped.

## Proposal: Scrub bootstrap-process residue from constraints.md

### Target specification files

- SPECIFICATION/constraints.md

### Summary

constraints.md carries two bootstrap-process residue references: line 78's vendoring procedure cites `at Phase 2 of the bootstrap plan` as a temporal anchor; line 227's heading-coverage check rule frames its current-state behavior in `Pre-Phase-6` / `from the Phase 6 seed forward` terms. Restate both in present tense. Tracking issue: li-i4h.

### Motivation

The vendoring-procedure line uses `Phase 2 of the bootstrap plan` as a temporal anchor, but the bootstrap plan is archived; new contributors reading this paragraph need a present-tense description of when initial vendoring runs, not a back-pointer to a closed phase. The heading-coverage paragraph describes a now-permanent rule (empty `[]` array is a failure) but frames it as a transition from `Pre-Phase-6` behavior; the transition is now history and the live rule is what matters.

### Proposed Changes

Two edits in `SPECIFICATION/constraints.md`:

**Edit 1 — line 78, §"Vendoring procedure" Initial-vendoring bullet.** Replace the existing parenthetical:

> **Initial vendoring** is a one-time MANUAL procedure (the v018 Q3 exception, executed once per livespec repo at Phase 2 of the bootstrap plan):

With:

> **Initial vendoring** is a one-time MANUAL procedure (the v018 Q3 exception, executed once per livespec repo when the vendored tree is first established):

The `v018 Q3 exception` reference is a spec-revision decision-ID cross-reference, which is permitted in spec prose per `non-functional-requirements.md` §"Comment discipline" scope-exemption (b); only the `Phase 2 of the bootstrap plan` clause is bootstrap-process residue and gets dropped.

**Edit 2 — line 227, end of §"Heading taxonomy".** Replace the existing sentence:

> Pre-Phase-6 the check tolerated an empty `[]` array; from the Phase 6 seed forward (this revision and later), emptiness is a failure if any spec tree exists.

With:

> An empty `[]` array is a failure if any spec tree exists.

The transition narrative (Pre-Phase-6 → Phase-6-seed-forward) is no longer load-bearing; the live rule is the single sentence that remains.

## Proposal: Scrub bootstrap-process residue from non-functional-requirements.md

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

non-functional-requirements.md carries four bootstrap-process residue references: line 88 frames the Definition of Done as a `Bootstrap-minimum` set; line 90 forecasts Phase-7 DoD widening; line 94 anchors the self-application closure to `Phase 0–6` and `Phase 6 seed commit`; line 432 labels an Import-Linter overlay as `(Phase 4 sub-step 26 reconciliation)`. Restate all four in present tense. Tracking issue: li-i4h.

### Motivation

The four lines together carry the same bootstrap-process residue pattern: each frames a current rule with a phase-pointer or bootstrap-plan reference that has outlived its purpose. The `Bootstrap-minimum:` framing in §"Definition of Done" suggests the listed set is a temporary placeholder, but those items ARE the live DoD today. The `Phase 7 dogfooded propose-change cycles` clause forecasts a widening that has already happened (the spec has been widened many times via dogfooded cycles since v001). The `Phase 0–6 imperative window` framing in §"Self-application bootstrap exception" duplicates the spec.md line 185 issue. The `(Phase 4 sub-step 26 reconciliation)` label adds no information that the surrounding paragraph doesn't already convey. Note: line 583's phase/cycle references inside the §"Comment discipline" rule's example list are EXAMPLES of forbidden references (the rule's content), not actual references — they MUST be preserved verbatim.

### Proposed Changes

Four edits in `SPECIFICATION/non-functional-requirements.md`:

**Edit 1 — line 88, §"Definition of Done".** Replace the existing sentence:

> A `livespec` change MUST satisfy the Definition of Done (above) before merge. Bootstrap-minimum: `just check` aggregate passes, paired tests exist for every new source file, the CLAUDE.md coverage check passes, the heading-coverage check passes against `tests/heading-coverage.json`, and the v034 D3 replay-hook trailers are present on `feat:` / `fix:` commits.

With:

> A `livespec` change MUST satisfy the Definition of Done (above) before merge. The DoD comprises: `just check` aggregate passes, paired tests exist for every new source file, the CLAUDE.md coverage check passes, the heading-coverage check passes against `tests/heading-coverage.json`, and the v034 D3 replay-hook trailers are present on `feat:` / `fix:` commits.

**Edit 2 — line 90, §"Definition of Done" trailing sentence.** Replace:

> The full DoD widens via Phase 7 dogfooded propose-change cycles when individual DoD items surface as needing more rigorous specification.

With:

> The DoD widens via dogfooded propose-change cycles when individual DoD items surface as needing more rigorous specification.

**Edit 3 — line 94, §"Self-application bootstrap exception".** Replace:

> The Phase 0–6 imperative window closed at the Phase 6 seed commit and remains closed. Every mutation to this `SPECIFICATION/` MUST flow through `/livespec:propose-change` → `/livespec:revise` against the appropriate spec target. Hand-edits to spec files outside the propose-change/revise loop are forbidden and would be caught by `dev-tooling/checks` plus the doctor static phase.

With:

> The initial bootstrap imperative window is closed. Every mutation to this `SPECIFICATION/` MUST flow through `/livespec:propose-change` → `/livespec:revise` against the appropriate spec target. Hand-edits to spec files outside the propose-change/revise loop are forbidden and would be caught by `dev-tooling/checks` plus the doctor static phase.

The section heading itself (`### Self-application bootstrap exception`) MAY remain as-is — `bootstrap` here describes the historical event that the closed imperative window references, and the rest of the section's prose now stands cleanly without phase numbering.

**Edit 4 — line 432, Import-Linter overlay paragraph.** Replace the leading bold label:

> **Implementation overlay (Phase 4 sub-step 26 reconciliation).** Two items from rule 1 — `returns.io` and `pathlib` — are intentionally absent from the realized `pyproject.toml` `forbidden_modules` list per the architecture-vs-mechanism principle.

With:

> **Implementation overlay.** Two items from rule 1 — `returns.io` and `pathlib` — are intentionally absent from the realized `pyproject.toml` `forbidden_modules` list per the architecture-vs-mechanism principle.

The rest of the paragraph (the per-item rationale for `returns.io` and `pathlib`) is preserved unchanged.

**Out-of-scope clarification.** Line 583 inside §"Comment discipline" Rule 2 reads `Comments MUST NOT cite version numbers ("v033", "v034 D2"), decision IDs ("Per v036 D1", "v037 D1"), phase numbers ("Phase 4"), cycle numbers ("cycle 117"), commit references ("this commit", "the previous PR")...`. Those phase/cycle references are the rule's example-list of forbidden patterns, not actual project references — they MUST remain verbatim and are explicitly NOT part of this scrub.
