---
topic: claude-opus-4-7-critique
author: claude-opus-4-7
created_at: 2026-05-18T08:36:23Z
---

## Proposal: Scrub bootstrap-process residue from templates/livespec/spec.md

### Target specification files

- SPECIFICATION/templates/livespec/spec.md

### Summary

templates/livespec/spec.md carries multiple Phase-7 / Phase-6 / Bootstrap-minimum references (lines 7, 19, 29, 41) that frame the current contract text as historical phase forecasts. The bootstrap plan is archived and the phases have all closed. Each occurrence MUST be restated in present tense (the per-occurrence rule is the same the main-spec v061 scrub-bootstrap-residue cycle just landed).

### Motivation

The phase-numbering scattered through this sub-spec's spec.md is inconsistent with the main-spec scrub just completed in v061. Each reference forecasts a widening that is either ambiguous (did it land? is it pending?) or is silent on the present-tense rule the spec MUST convey. New contributors reading the sub-spec are forced into reader-archaeology to decide whether 'Phase 7 widens X' describes current contract, closed history, or pending work — the same ambiguity the main-spec scrub solved for.

### Proposed Changes

Walk every Phase-N reference in templates/livespec/spec.md (notably lines 7, 19, 29, 41) and resolve each occurrence per the same discipline applied to the main spec in v061 (scrub-bootstrap-residue tracking issue li-i4h). Per occurrence, judge whether the forecasted widening has (a) already landed — in which case restate the rule in present tense and drop the phase pointer; (b) been superseded — in which case remove the now-stale forecast; or (c) is still pending — in which case re-anchor on a non-phase trigger ('when the seed prompt widens the starter-content policy beyond a `.gitkeep` placeholder' rather than 'Phase 7 widens'). Specifically: line 7's `.gitkeep` starter-content sentence, line 19's seed-prompt regeneration paragraph, line 29's revise-prompt widening sentence, and line 41's starter-content section MUST each be re-evaluated and restated. The section heading at line 41 (`### Specification template starter content`) and the surrounding load-bearing rules MUST be preserved; only the phase pointers and `Bootstrap-minimum:` framing get scrubbed.

## Proposal: Scrub bootstrap-process residue from templates/livespec/contracts.md

### Target specification files

- SPECIFICATION/templates/livespec/contracts.md

### Summary

templates/livespec/contracts.md lines 16 and 48 frame the per-prompt semantic-property catalogue and the doctor-llm-subjective-checks prompt as Phase-6 bootstrap-minimum / Phase-7 widening forecasts. The phases have closed; the catalogue and the prompt either have widened (restate in present tense) or have not (re-anchor on a non-phase trigger). The current framing is ambiguous and inconsistent with the main-spec v061 scrub.

### Motivation

Two prose paragraphs in this sub-spec's contracts.md make the wire contract's current shape ambiguous — a reader cannot tell whether the stated 'Phase 6 bootstrap-minimum' shape is the live catalogue or a now-superseded scaffold. The contradiction between 'Phase 7 widens' forecasts and the actual current state of the prompt and catalogue files in the template tree should be resolved by present-tense restatement.

### Proposed Changes

Walk lines 16 and 48 of templates/livespec/contracts.md and apply the v061 scrub discipline per occurrence. Line 16's per-prompt-catalogue paragraph MUST restate the current catalogue scope in present tense without 'Phase 6 lands bootstrap-minimum / Phase 7's first propose-change widens' framing. Line 48's doctor-llm-subjective-checks prompt paragraph MUST restate the prompt's operability in present tense without 'Phase 7 brings this prompt to operability / Phase 6's bootstrap-minimum stub' framing. The load-bearing rules (catalogue shape, prompt-QA harness binding, doctor-LLM subjective-phase prompt field name) MUST be preserved verbatim; only the phase pointers and bootstrap-minimum framing get scrubbed.

## Proposal: Scrub bootstrap-process residue from templates/livespec/constraints.md

### Target specification files

- SPECIFICATION/templates/livespec/constraints.md

### Summary

templates/livespec/constraints.md lines 9 and 15 carry parenthetical '(Phase 7 widening; Phase 6 stub)' and '(Phase 7 widening)' labels after the BCP14 well-formedness check and the gherkin-blank-line-format check rules. The phase labels frame the current rule as if it were pending; restate in present tense without the parenthetical.

### Motivation

The parenthetical phase labels on lines 9 and 15 make the doctor-static-check rules' current state unclear — a reader cannot tell whether the rule is enforced today or pending. The inconsistency with the present-tense pattern the main-spec v061 scrub established should be resolved here as well.

### Proposed Changes

Drop the parenthetical '(Phase 7 widening; Phase 6 stub)' from line 9 and '(Phase 7 widening)' from line 15. Each rule's load-bearing content (BCP14 well-formedness check; gherkin-blank-line-format check) is already stated in normative present tense — removing the parenthetical leaves the rule cleanly readable. No other content changes.

## Proposal: Scrub bootstrap-process residue from templates/livespec/scenarios.md

### Target specification files

- SPECIFICATION/templates/livespec/scenarios.md

### Summary

templates/livespec/scenarios.md line 3 opens the file with 'Phase 6 lands one happy-path scenario per REQUIRED prompt plus the v020 Q2 sub-spec-emission branches; Phase 7 widens this to the full edge-case surface.' Restate in present tense without the phase pointers.

### Motivation

The opening sentence's phase-numbered scoping is ambiguous about the current scenario set — a reader cannot tell whether the scenarios below are the Phase-6 happy-path subset or the Phase-7 widened set. The reference to 'Phase 7 widens this' forecasts a transition that has either happened (restate) or has not (re-anchor on a non-phase trigger).

### Proposed Changes

Rewrite line 3 to state the scenarios file's current coverage in present tense. One acceptable rewrite: 'This sub-spec's scenarios enumerate the canonical user-facing flows for the `livespec` template's prompt interview surface, including happy-path coverage per REQUIRED prompt and the v020 Q2 sub-spec-emission branches.' If the edge-case widening is genuinely incomplete, re-anchor on a non-phase trigger rather than 'Phase 7 widens' — but the proposal's default disposition is to drop the forecast and restate current coverage.
