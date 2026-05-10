---
topic: scrub-bootstrap-residue
author: claude-opus-4-7
created_at: 2026-05-10T08:18:03Z
---

## Proposal: Scrub bootstrap-process residue from templates/minimal/spec.md

### Target specification files

- SPECIFICATION/templates/minimal/spec.md

### Summary

templates/minimal/spec.md carries four bootstrap-process residue references on lines 7, 19, 23, and 27 — each frames a current rule with `Phase 5` / `Phase 6` / `Phase 7` / `Phase 9` / `bootstrap-minimum` pointers that have outlived their purpose. Restate each in present tense. Tracking issue: li-i4h.

### Motivation

Each affected line bundles a load-bearing rule (template root layout, REQUIRED-prompt stub state, end-to-end test fixture mandate, starter-content scaffold) with phase pointers that anchor the rule to a closed bootstrap process. The spec MUST describe the current contract directly.

### Proposed Changes

Four edits in `SPECIFICATION/templates/minimal/spec.md`:

**Edit 1 — line 7, §"Template root layout" trailing sentence.** Replace:

> The template MAY ship a `prompts/seed.md` for the seed flow, but the other REQUIRED prompts (`propose-change`, `critique`, `revise`) are stubbed at this revision and widen in Phase 7.

With:

> The template MAY ship a `prompts/seed.md` for the seed flow; the other REQUIRED prompts (`propose-change`, `critique`, `revise`) are currently stubbed.

**Edit 2 — line 19, §"Reduced prompt interview intents" trailing sentence.** Replace:

> The other REQUIRED prompts (`propose-change`, `critique`, `revise`) at Phase 6 are stubbed at the bootstrap-minimum scope; Phase 7 widens them to full feature parity with the `livespec` template's prompts, adapted for single-file specs.

With:

> The other REQUIRED prompts (`propose-change`, `critique`, `revise`) are currently stubbed at minimal scope; future propose-change cycles MAY widen them toward full feature parity with the `livespec` template's prompts, adapted for single-file specs.

**Edit 3 — line 23, §"End-to-end integration test fixture".** Replace:

> The `minimal` template is the canonical fixture for `tests/e2e/`'s end-to-end integration test (Phase 9 work). The test MUST exercise (a) seed against an empty fixture repo, (b) propose-change → revise round-trip, (c) doctor static phase, (d) retry-on-exit-4 path, (e) doctor-static-fail-then-fix recovery, and (f) prune-history no-op against a single-version history. `tests/e2e/fake_claude.py` is the test harness's mock Claude Code surface; Phase 5 lands the placeholder, Phase 9 fills in the real e2e content.

With:

> The `minimal` template is the canonical fixture for `tests/e2e/`'s end-to-end integration test. The test MUST exercise (a) seed against an empty fixture repo, (b) propose-change → revise round-trip, (c) doctor static phase, (d) retry-on-exit-4 path, (e) doctor-static-fail-then-fix recovery, and (f) prune-history no-op against a single-version history. `tests/e2e/fake_claude.py` is the test harness's mock Claude Code surface.

**Edit 4 — line 27, §"Starter-content policy".** Replace:

> The `minimal` template's `specification-template/SPECIFICATION.md` (Phase 7 widening; Phase 6 placeholder) provides a starter shape: heading skeleton plus delimiter-comment markers per the format defined in this sub-spec's contracts file. End users SHOULD overwrite the placeholder content with their domain prose; the delimiter comments MUST be preserved so subsequent propose-change/revise cycles can target named regions of the file.

With:

> The `minimal` template's `specification-template/SPECIFICATION.md` provides a starter shape: heading skeleton plus delimiter-comment markers per the format defined in this sub-spec's contracts file. End users SHOULD overwrite the placeholder content with their domain prose; the delimiter comments MUST be preserved so subsequent propose-change/revise cycles can target named regions of the file.

## Proposal: Scrub bootstrap-process residue from templates/minimal/contracts.md

### Target specification files

- SPECIFICATION/templates/minimal/contracts.md

### Summary

templates/minimal/contracts.md carries three bootstrap-process residue references on lines 45, 53, and 57 — each frames a current rule with `Phase 6` / `Phase 7` / `Phase 9` / `bootstrap-minimum` pointers that have outlived their purpose. Spec-revision decision-IDs (`v014-N9`) are preserved per the `SPECIFICATION/**` exemption. Tracking issue: li-i4h.

### Motivation

Each affected line ties a current rule (the e2e harness format alignment, the REQUIRED-prompt stub state, the per-prompt-property catalogue scope) to a phase-N forecast. Today the spec MUST describe the current state directly.

### Proposed Changes

Three edits in `SPECIFICATION/templates/minimal/contracts.md`:

**Edit 1 — line 45, §"Consumers" middle sentence.** Replace:

> The `minimal` template's `prompts/propose-change.md` and `prompts/revise.md` reference this format when emitting region-targeted edits. The Phase 9 `tests/e2e/fake_claude.py` mock harness parses against this same format. Future custom-template authors MAY adopt the same format unchanged or define their own; the format is not livespec-wide policy.

With:

> The `minimal` template's `prompts/propose-change.md` and `prompts/revise.md` reference this format when emitting region-targeted edits. The `tests/e2e/fake_claude.py` mock harness parses against this same format. Future custom-template authors MAY adopt the same format unchanged or define their own; the format is not livespec-wide policy.

**Edit 2 — line 53, §"Template-internal JSON contracts" trailing sentence.** Replace:

> The other REQUIRED prompts (`propose-change`, `critique`, `revise`) consume and emit the same payload schemas as the `livespec` template's corresponding prompts. Bootstrap-minimum scope at Phase 6: stubs with the v014-N9-style placeholder shape; Phase 7 widens to full operational prompts.

With:

> The other REQUIRED prompts (`propose-change`, `critique`, `revise`) consume and emit the same payload schemas as the `livespec` template's corresponding prompts; they are currently stubs with the v014-N9-style placeholder shape and MAY widen via future propose-change cycles.

**Edit 3 — line 57, §"Per-prompt semantic-property catalogue" intro.** Replace:

> This catalogue enumerates the testable semantic properties for the `minimal` template's REQUIRED prompts. Phase 6 lands bootstrap-minimum (1-2 properties per prompt); Phase 7 widens.

With:

> This catalogue enumerates the testable semantic properties for the `minimal` template's REQUIRED prompts. Future propose-change cycles MAY widen the catalogue toward the full assertion surface.

## Proposal: Scrub bootstrap-process residue from templates/minimal/constraints.md

### Target specification files

- SPECIFICATION/templates/minimal/constraints.md

### Summary

templates/minimal/constraints.md carries three bootstrap-process residue references on lines 17, 23, and 29 — `(Phase 7 widening)` parentheticals on doctor-static-check rules and a `When the Phase 7 delimiter-comment format lands` / `Pre-Phase-7` framing on the delimiter-comment well-formedness rule. Restate each in present tense. Tracking issue: li-i4h.

### Motivation

The two `(Phase 7 widening)` parentheticals (lines 17, 23) duplicate the same residue pattern fixed in `templates/livespec/constraints.md`: each describes a doctor-static-phase check that is now operable; the parenthetical adds no live information. Line 29's `When the Phase 7 delimiter-comment format lands` framing is a forecast that has already happened — the delimiter-comment format is defined in this sub-spec's contracts.md (HTML-comment markers, regex pin, paired open/close).

### Proposed Changes

Three edits in `SPECIFICATION/templates/minimal/constraints.md`:

**Edit 1 — line 17, §"Gherkin blank-line format check exemption" opening sentence.** Replace:

> The doctor static phase's `gherkin-blank-line-format` check (Phase 7 widening) MUST exempt `minimal`-rooted projects whose `SPECIFICATION.md` does NOT contain any fenced ` ```gherkin ` blocks.

With:

> The doctor static phase's `gherkin-blank-line-format` check MUST exempt `minimal`-rooted projects whose `SPECIFICATION.md` does NOT contain any fenced ` ```gherkin ` blocks.

**Edit 2 — line 23, §"BCP14 normative-keyword well-formedness" middle sentence.** Replace:

> End-user `SPECIFICATION.md` content for `minimal`-rooted projects MUST use BCP 14 (RFC 2119 + RFC 8174) requirement language for normative statements. The doctor static phase's BCP14 well-formedness check (Phase 7 widening) MUST detect malformed normative usage in `SPECIFICATION.md` regardless of the template chosen.

With:

> End-user `SPECIFICATION.md` content for `minimal`-rooted projects MUST use BCP 14 (RFC 2119 + RFC 8174) requirement language for normative statements. The doctor static phase's BCP14 well-formedness check MUST detect malformed normative usage in `SPECIFICATION.md` regardless of the template chosen.

**Edit 3 — line 29, §"Single-file delimiter-comment well-formedness".** Replace:

> When the Phase 7 delimiter-comment format lands (TBD per this sub-spec's contracts.md), `SPECIFICATION.md` content MUST satisfy the well-formedness invariants stated there: HTML-comment marker syntax, paired open/close, kebab-case region names, no nested-boundary crossing. Pre-Phase-7, end-user content MAY omit delimiter markers entirely.

With:

> Per the delimiter-comment format defined in this sub-spec's contracts.md, `SPECIFICATION.md` content MUST satisfy the well-formedness invariants stated there: HTML-comment marker syntax, paired open/close, kebab-case region names, no nested-boundary crossing. End-user content MAY omit delimiter markers when not needed.

## Proposal: Scrub bootstrap-process residue from templates/minimal/scenarios.md

### Target specification files

- SPECIFICATION/templates/minimal/scenarios.md

### Summary

templates/minimal/scenarios.md carries two bootstrap-process residue references on lines 3 and 90 — the preamble frames the scenario set as a `(Phase 9 work)` / `Phase 6 → Phase 9` outline-then-fill transition; line 90 trailing sentence forecasts `Phase 5 lands the placeholder; Phase 9 fills in the operational implementation`. Drop both. Tracking issue: li-i4h.

### Motivation

Both lines reference closed bootstrap phases. The preamble's `Phase 6 → Phase 9` framing tells the reader to expect future content rather than describing the current scope. Line 90's trailing sentence forecasts work that has either landed or is ongoing — either way, the harness's MUST requirements (already stated in the preceding sentences) are the load-bearing rule.

### Proposed Changes

Two edits in `SPECIFICATION/templates/minimal/scenarios.md`:

**Edit 1 — line 3, sub-spec preamble.** Replace:

> This sub-spec's scenarios outline the structural shape of `tests/e2e/`'s end-to-end integration test (Phase 9 work). Phase 6 lands the structural outline; Phase 9 fills in the test fixtures and harness invocations.

With:

> This sub-spec's scenarios outline the structural shape of `tests/e2e/`'s end-to-end integration test.

**Edit 2 — line 90, §"Test harness contract" trailing sentence.** Delete the trailing sentence `Phase 5 lands the placeholder; Phase 9 fills in the operational implementation.` The preceding sentences (`tests/e2e/fake_claude.py` MUST implement the mock surface; MUST support deterministic per-prompt response sequences; MUST capture exit codes / stdout / stderr) state the load-bearing contract; the deleted sentence forecasts authoring without describing a current rule.
