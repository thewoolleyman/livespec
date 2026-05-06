---
topic: seed-prompt-regeneration
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T00:17:43Z
---

## Proposal: Seed-prompt catalogue widening with property keys + assertion contract

### Target specification files

- SPECIFICATION/templates/livespec/contracts.md

### Summary

Widen the catalogue's `prompts/seed.md` subsection at SPECIFICATION/templates/livespec/contracts.md by assigning explicit string-key names to its two existing semantic properties (`headings_derived_from_intent` and `asks_v020_q2_question`) and documenting the per-property assertion-function contract that the prompt-QA harness consumes. The keys land in `tests/prompts/livespec/_assertions.py`'s `ASSERTIONS` dict and in the seed prompt's fixture `expected_semantic_properties` lists.

### Motivation

Phase 7 sub-step (c).1 lands the in-line per-prompt regeneration cycle for the seed prompt per Plan §3543-3550. Catalogue widening is the spec-side change; the regenerated prompts/seed.md, the fixture's `expected_semantic_properties` list, and the per-template `_assertions.py` ASSERTIONS dict are the impl-side changes that land alongside this revise atomically. The bootstrap-minimum catalogue had 2 properties stated in prose; this widening assigns them explicit string-key names suitable for `expected_semantic_properties` and documents what each property's assertion function MUST verify against the canonical replayed_response.

### Proposed Changes

One atomic edit to **SPECIFICATION/templates/livespec/contracts.md** §"Per-prompt semantic-property catalogue → prompts/seed.md" (the bullet block at lines 19-21).

Replace the two existing bullets:

> - The prompt MUST derive top-level `#` headings within each spec file from intent nouns, NOT from a fixed taxonomy. (Asserts the v020 Q4 starter-content policy; aligns with SPECIFICATION/constraints.md §"Heading taxonomy" line 47 which pins intent-derivation to level 1.)
> - The prompt MUST ask the v020 Q2 sub-spec-emission question and route emission by the user's answer — `sub_specs: []` on "no", one `SubSpecPayload` per named template on "yes".

with the following four-bullet block (two property names + the assertion-function contract for each):

> - `headings_derived_from_intent` — the prompt MUST derive top-level `#` headings within each spec file from intent nouns, NOT from a fixed taxonomy. (Asserts the v020 Q4 starter-content policy; aligns with SPECIFICATION/constraints.md §"Heading taxonomy" line 47 which pins intent-derivation to level 1.) **Assertion function**: every entry in `replayed_response.files[]` has a non-empty content body whose first non-blank line begins with `# ` (an H1 header).
> - `asks_v020_q2_question` — the prompt MUST ask the v020 Q2 sub-spec-emission question and route emission by the user's answer — `sub_specs: []` on "no", one `SubSpecPayload` per named template on "yes". **Assertion function**: when `input_context.ships_own_templates` is true (with `input_context.named_templates` listing N entries), `replayed_response.sub_specs` carries exactly N entries; otherwise `replayed_response.sub_specs` is the empty list.
> - **Assertion-function contract.** Each property's assertion function lives in `tests/prompts/livespec/_assertions.py` keyed by the property's string name in the `ASSERTIONS` dict. The function accepts keyword-only arguments `*, replayed_response: object, input_context: object` per SPECIFICATION/contracts.md §"Prompt-QA harness contract" (v014); it raises `AssertionError` on any property violation. The fixture's `expected_semantic_properties` list MAY contain any subset of the property names above; absent properties are not asserted.
> - **Catalogue widening rule.** Future per-prompt regeneration cycles MAY add properties to this list; each new property's assertion function MUST land in `_assertions.py` in the same revise commit per the in-line widening rule (Plan §3543-3550).

