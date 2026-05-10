---
topic: scrub-bootstrap-residue
author: claude-opus-4-7
created_at: 2026-05-10T08:15:40Z
---

## Proposal: Scrub bootstrap-process residue from templates/livespec/spec.md

### Target specification files

- SPECIFICATION/templates/livespec/spec.md

### Summary

templates/livespec/spec.md carries four bootstrap-process residue references on lines 7, 19, 29, and 41 — each frames a current rule with `Phase 6` / `Phase 7` / `bootstrap-minimum` pointers that have outlived their purpose. Restate each in present tense. Tracking issue: li-i4h.

### Motivation

Each affected line bundles a load-bearing rule (template root layout, regenerated-prompt invariants, revise-prompt scope, starter-content policy) with a Phase-N forecast or `bootstrap-minimum` framing that is no longer load-bearing. The phase pointers reference a closed bootstrap process; today's spec MUST describe the current contract without those temporal anchors.

### Proposed Changes

Four edits in `SPECIFICATION/templates/livespec/spec.md`:

**Edit 1 — line 7, §"Template root layout".** Delete the trailing sentence `Phase 7 widens the starter-content policy from the current `.gitkeep` placeholder.` from the paragraph. The prior sentence already enumerates the template root contents; the deleted sentence forecasts work without describing a current rule.

**Edit 2 — line 19, §"Seed interview flow" trailing sentence.** Replace:

> The seed prompt regenerated from this sub-spec in Phase 7 MUST preserve this user-answer-driven behavior; Phase 7's revise step MUST reject regenerated prompts that hard-code emission per v019's now-superseded contract.

With:

> Any regenerated seed prompt MUST preserve this user-answer-driven behavior; the revise step MUST reject regenerated prompts that hard-code emission per v019's now-superseded contract.

(The `v019` decision-ID cross-reference is preserved per the v050 §"Comment discipline" `SPECIFICATION/**` exemption; only the `Phase 7` framings drop.)

**Edit 3 — line 29, §"Revise interview flow" trailing sentence.** Delete the trailing sentence `Phase 7 widens the prompt to handle multi-finding proposals plus partial accepts.` The prior sentences state the current rule; the deleted sentence forecasts work that has either landed or is a future propose-change cycle either way.

**Edit 4 — line 41, §"Starter-content policy".** Replace the existing paragraph:

> Per Phase 7 widening: when the seed prompt generates initial content for a new spec tree, the starter content SHOULD reflect the user's intent rather than a fixed boilerplate. Bootstrap-minimum starter shape (this revision): the seed-input JSON `files[]` array enumerates the spec-file paths and content; the `specification-template/` scaffolding under the template root is currently a `.gitkeep` placeholder pending Phase 7 work.

With:

> When the seed prompt generates initial content for a new spec tree, the starter content SHOULD reflect the user's intent rather than a fixed boilerplate. The seed-input JSON `files[]` array enumerates the spec-file paths and content; the `specification-template/` scaffolding under the template root is currently a `.gitkeep` placeholder.

The load-bearing rules (intent-driven starter content; files[] array as the canonical enumeration; `.gitkeep` as the current scaffolding state) are preserved; the `Per Phase 7 widening:` prefix and the `Bootstrap-minimum starter shape (this revision):` framing are dropped, along with the `pending Phase 7 work` trailing clause.

## Proposal: Scrub bootstrap-process residue from templates/livespec/contracts.md

### Target specification files

- SPECIFICATION/templates/livespec/contracts.md

### Summary

templates/livespec/contracts.md carries five bootstrap-process residue references on lines 16, 23, 29, 36, and 48 — each frames a rule with `Phase 6` / `Phase 7` / `bootstrap-minimum` / `Plan §...` / `sub-step (c).1` pointers that have outlived their purpose. Spec-revision decision-IDs (`v003`, `v004`, `v005`, `v018 Q5`) are preserved per the v050 §"Comment discipline" `SPECIFICATION/**` exemption. Tracking issue: li-i4h.

### Motivation

Each affected line bundles a load-bearing rule (catalogue scope, widening discipline, assertion-function contract shape, doctor-LLM-prompt declaration) with a Phase-N forecast, `bootstrap-minimum` framing, `Plan §...` reference, or bootstrap-Plan `sub-step` pointer. The decision-ID cross-references (e.g., `Same shape as v003/v004/v005`) are spec-internal audit trail and remain.

### Proposed Changes

Five edits in `SPECIFICATION/templates/livespec/contracts.md`:

**Edit 1 — line 16, §"Per-prompt semantic-property catalogue" intro.** Replace:

> This catalogue enumerates the testable semantic properties for each REQUIRED prompt in the `livespec` template. Phase 6 lands bootstrap-minimum (1-2 properties per prompt); Phase 7's first propose-change against this sub-spec widens the catalogue to the full assertion surface that the v018 Q5 prompt-QA harness asserts against.

With:

> This catalogue enumerates the testable semantic properties for each REQUIRED prompt in the `livespec` template. Future propose-change cycles against this sub-spec MAY widen the catalogue toward the full assertion surface that the v018 Q5 prompt-QA harness asserts against.

**Edit 2 — line 23, `prompts/seed.md` Catalogue widening rule.** Replace:

> - **Catalogue widening rule.** Future per-prompt regeneration cycles MAY add properties to this list; each new property's assertion function MUST land in `_assertions.py` in the same revise commit per the in-line widening rule (Plan §3543-3550).

With:

> - **Catalogue widening rule.** Future per-prompt regeneration cycles MAY add properties to this list; each new property's assertion function MUST land in `_assertions.py` in the same revise commit.

**Edit 3 — line 29, `prompts/propose-change.md` Assertion-function contract.** Replace:

> - **Assertion-function contract.** Same shape as the prompts/seed.md catalogue contract (sub-step (c).1, v003): each property's assertion function lives in `tests/prompts/livespec/_assertions.py` keyed by the property's string name in the `ASSERTIONS` dict, accepts keyword-only `*, replayed_response: object, input_context: object`, and raises `AssertionError` on violation.

With:

> - **Assertion-function contract.** Same shape as the prompts/seed.md catalogue contract (v003): each property's assertion function lives in `tests/prompts/livespec/_assertions.py` keyed by the property's string name in the `ASSERTIONS` dict, accepts keyword-only `*, replayed_response: object, input_context: object`, and raises `AssertionError` on violation.

**Edit 4 — line 36, `prompts/revise.md` Assertion-function contract.** Replace:

> - **Assertion-function contract.** Same shape as v003/v004 (sub-steps (c).1 / (c).2 catalogue contracts).

With:

> - **Assertion-function contract.** Same shape as v003/v004 catalogue contracts.

**Edit 5 — line 48, §"Doctor-LLM-subjective-checks prompt".** Replace:

> The `template.json` `doctor_llm_subjective_checks_prompt: "prompts/doctor-llm-subjective-checks.md"` field declares the prompt the doctor LLM-driven subjective phase invokes. The prompt MUST emit `doctor_findings.schema.json`-conforming output. Phase 7 brings this prompt to operability; Phase 6's bootstrap-minimum stub at `prompts/doctor-llm-subjective-checks.md` documents the contract without implementing the full subjective check logic.

With:

> The `template.json` `doctor_llm_subjective_checks_prompt: "prompts/doctor-llm-subjective-checks.md"` field declares the prompt the doctor LLM-driven subjective phase invokes. The prompt MUST emit `doctor_findings.schema.json`-conforming output.

The deleted trailing sentences are pure bootstrap-process forecast/stub framing; the live rule (template.json field declaration + prompt's wire contract) is preserved unchanged.

## Proposal: Scrub bootstrap-process residue from templates/livespec/constraints.md

### Target specification files

- SPECIFICATION/templates/livespec/constraints.md

### Summary

templates/livespec/constraints.md carries two bootstrap-process residue references on lines 9 and 15 — each frames a current doctor-static-check rule with `(Phase 7 widening; Phase 6 stub)` / `(Phase 7 widening)` parentheticals. Drop the parentheticals; the surrounding rule remains intact. Tracking issue: li-i4h.

### Motivation

Both affected lines describe doctor-static-phase checks (`bcp14_keyword_wellformedness`, `gherkin_blank_line_format`) that are now operable in the implementation — verifiable by running `bin/doctor_static.py` and inspecting findings. The `Phase 7 widening` / `Phase 6 stub` framings reference closed bootstrap phases and add no live information.

### Proposed Changes

Two edits in `SPECIFICATION/templates/livespec/constraints.md`:

**Edit 1 — line 9, §"BCP14 normative-keyword well-formedness" trailing sentence.** Replace:

> The `livespec-nlspec-spec.md` doc enumerates the keyword-matching rules in detail (token boundaries, embedded-uppercase-word distinctions, etc.). The doctor static phase's BCP14 well-formedness check (Phase 7 widening; Phase 6 stub) MUST detect malformed normative usage.

With:

> The `livespec-nlspec-spec.md` doc enumerates the keyword-matching rules in detail (token boundaries, embedded-uppercase-word distinctions, etc.). The doctor static phase's BCP14 well-formedness check MUST detect malformed normative usage.

**Edit 2 — line 15, §"Gherkin blank-line convention" trailing sentence.** Replace:

> The `dev-tooling/checks` layer's gherkin-blank-line-format check (Phase 7 widening) MUST detect violations of the convention. Sub-specs that reuse the gherkin format inherit the constraint via this sub-spec's NLSpec discipline.

With:

> The `dev-tooling/checks` layer's gherkin-blank-line-format check MUST detect violations of the convention. Sub-specs that reuse the gherkin format inherit the constraint via this sub-spec's NLSpec discipline.

Both edits drop only the parenthetical phase-framing; the load-bearing MUST clauses are preserved verbatim.

## Proposal: Scrub bootstrap-process residue from templates/livespec/scenarios.md

### Target specification files

- SPECIFICATION/templates/livespec/scenarios.md

### Summary

templates/livespec/scenarios.md line 3 frames the sub-spec's scenario-set scope with a `Phase 6 lands one happy-path scenario per REQUIRED prompt plus the v020 Q2 sub-spec-emission branches; Phase 7 widens this to the full edge-case surface.` clause. Restate in present tense. Tracking issue: li-i4h.

### Motivation

The line frames the scenario-set's scope as a phase-N transition (Phase 6 → Phase 7) rather than describing the current scope. The scope today is in fact `one happy-path scenario per REQUIRED prompt plus the v020 Q2 sub-spec-emission branches`; future propose-change cycles MAY widen via the standard governed loop without needing the spec to forecast that.

### Proposed Changes

One edit in `SPECIFICATION/templates/livespec/scenarios.md`:

**Edit 1 — line 3, sub-spec preamble.** Replace:

> This sub-spec's scenarios enumerate the canonical user-facing flows for the `livespec` template's prompt interview surface. Phase 6 lands one happy-path scenario per REQUIRED prompt plus the v020 Q2 sub-spec-emission branches; Phase 7 widens this to the full edge-case surface.

With:

> This sub-spec's scenarios enumerate the canonical user-facing flows for the `livespec` template's prompt interview surface — currently one happy-path scenario per REQUIRED prompt plus the v020 Q2 sub-spec-emission branches. Future propose-change cycles MAY widen this toward the full edge-case surface.

The v020 Q2 decision-ID cross-reference is preserved; the Phase 6 / Phase 7 framings drop.
