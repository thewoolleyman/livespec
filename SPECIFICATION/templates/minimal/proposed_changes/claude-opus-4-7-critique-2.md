---
topic: claude-opus-4-7-critique
author: claude-opus-4-7
created_at: 2026-05-18T08:36:40Z
---

## Proposal: Scrub bootstrap-process residue from templates/minimal/spec.md

### Target specification files

- SPECIFICATION/templates/minimal/spec.md

### Summary

templates/minimal/spec.md lines 7, 19, 23, 27 carry Phase-5/6/7/9 and Bootstrap-minimum framing on the template root spec, the REQUIRED prompts stub note, the e2e test-suite scenario, and the specification-template starter shape. Each occurrence MUST be restated in present tense, matching the main-spec v061 scrub.

### Motivation

The phase numbering scattered across this sub-spec's spec.md is inconsistent with the v061 main-spec scrub and creates ambiguity about which forecasts have landed (e.g., the e2e harness `fake_claude.py` exists today; was Phase 9 already filled in?) versus which remain pending. The contradiction between forecast-style phase framing and the live state of the template tree should be resolved.

### Proposed Changes

Walk each Phase-N reference in templates/minimal/spec.md and apply the v061 scrub discipline. Line 7's REQUIRED-prompts stub-and-widen sentence MUST restate the current state of the minimal template's prompts. Line 19's 'Phase 6 stubbed / Phase 7 widens' framing MUST be scrubbed and replaced with a present-tense statement of the prompts' current coverage. Line 23's e2e test-suite reference to 'Phase 9 work' and 'Phase 5 lands the placeholder, Phase 9 fills' MUST be re-evaluated (the `tests/e2e/fake_claude.py` file exists today; the e2e test suite is described in non-functional-requirements.md §'E2E harness contract' in present tense) and restated accordingly. Line 27's specification-template starter-shape paragraph's '(Phase 7 widening; Phase 6 placeholder)' label MUST be dropped; the rule about delimiter comments and end-user overwrite is the load-bearing rule and is preserved. As with the main-spec scrub, the architecture-vs-mechanism discipline guides whether a forecast is dropped (now-realized), deleted (now-stale), or re-anchored on a non-phase trigger (genuinely incomplete).

## Proposal: Scrub bootstrap-process residue from templates/minimal/contracts.md

### Target specification files

- SPECIFICATION/templates/minimal/contracts.md

### Summary

templates/minimal/contracts.md lines 45, 53, 57 frame the e2e mock harness, the REQUIRED-prompts schema-binding, and the per-prompt catalogue as Phase-6/7/9 forecasts. Restate each in present tense.

### Motivation

The three paragraphs make the wire-contract surface ambiguous about which Phase-6 bootstrap-minimum shape is current versus historical. Line 45's 'Phase 9' reference to `tests/e2e/fake_claude.py` contradicts the present-tense framing of the same file in the main spec's non-functional-requirements.md §'E2E harness contract'. The inconsistency should be resolved by present-tense restatement.

### Proposed Changes

Walk lines 45, 53, 57 of templates/minimal/contracts.md and apply the v061 scrub discipline. Line 45's 'Phase 9 `tests/e2e/fake_claude.py` mock harness' MUST drop the Phase 9 forecast (the harness exists today). Line 53's 'Bootstrap-minimum scope at Phase 6: stubs ... Phase 7 widens to full operational prompts.' MUST restate the current scope without phase pointers. Line 57's per-prompt-catalogue 'Phase 6 lands bootstrap-minimum ... Phase 7 widens.' MUST restate the catalogue's current scope. The load-bearing rules (the schema bindings, the catalogue's per-prompt assertion mapping) MUST be preserved verbatim.

## Proposal: Scrub bootstrap-process residue from templates/minimal/constraints.md

### Target specification files

- SPECIFICATION/templates/minimal/constraints.md

### Summary

templates/minimal/constraints.md lines 17, 23, 29 frame the gherkin-blank-line-format check, the BCP14 well-formedness check, and the delimiter-comment format as Phase-7 forecasts. Restate each in present tense without the phase pointers.

### Motivation

Three rules on lines 17, 23, 29 carry '(Phase 7 widening)' or 'Pre-Phase-7' framing that makes the constraints' current enforcement state ambiguous. A reader cannot tell whether the rule is live today or pending Phase 7. The inconsistency with the present-tense pattern the main-spec v061 scrub established should be resolved here as well.

### Proposed Changes

Drop the parenthetical '(Phase 7 widening)' from lines 17 and 23 — each rule's load-bearing content stands cleanly in present tense. Line 29's 'When the Phase 7 delimiter-comment format lands ... Pre-Phase-7, end-user content MAY omit delimiter markers entirely.' MUST be re-evaluated and restated: if the delimiter-comment format has landed, replace the conditional with the present-tense rule; if it has not, re-anchor on a non-phase trigger ('Once the delimiter-comment format is defined ...') without the Phase-7 framing.

## Proposal: Scrub bootstrap-process residue from templates/minimal/scenarios.md

### Target specification files

- SPECIFICATION/templates/minimal/scenarios.md

### Summary

templates/minimal/scenarios.md line 3 (opening) and line 90 (the `fake_claude.py` mock-harness paragraph) carry Phase 5/6/9 framing. Restate each in present tense.

### Motivation

The opening sentence at line 3 is ambiguous about whether the scenarios below are Phase-6 structural outlines or Phase-9 filled-in fixtures. Line 90's 'Phase 5 lands the placeholder; Phase 9 fills in the operational implementation' contradicts the present-tense state of `tests/e2e/fake_claude.py` (which is operational today per the main spec's non-functional-requirements.md §'E2E harness contract').

### Proposed Changes

Rewrite line 3 to state the scenarios file's current coverage in present tense (drop both the 'Phase 6 lands' and 'Phase 9 fills' forecasts). Rewrite line 90's `fake_claude.py` paragraph to describe the harness's current operational shape in present tense, dropping the 'Phase 5 lands the placeholder; Phase 9 fills' forecast. The load-bearing rules (mock-harness obligations: deterministic per-prompt responses, wrapper exit-code / stdout / stderr capture) MUST be preserved verbatim.
