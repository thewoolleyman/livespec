---
topic: minimal-seed-prompt-regeneration
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T00:56:42Z
---

## Proposal: Minimal seed-prompt catalogue widening with property keys + assertion contract

### Target specification files

- SPECIFICATION/templates/minimal/contracts.md

### Summary

Widen the catalogue's `prompts/seed.md` subsection at SPECIFICATION/templates/minimal/contracts.md by assigning explicit string-key names to its two existing semantic properties (`sub_specs_always_empty` and `single_specification_md_file`) and documenting their assertion-function contracts.

### Motivation

Phase 7 sub-step (d).2 lands the in-line per-prompt regeneration cycle for the minimal template's prompts/seed.md per Plan §3543-3550. Mirrors the (c).1 pattern.

### Proposed Changes

One atomic edit to **SPECIFICATION/templates/minimal/contracts.md** §"Per-prompt semantic-property catalogue → prompts/seed.md" (the bullet block).

Replace the two existing bullets:

> - The prompt MUST emit `sub_specs: []` regardless of any pre-seed dialogue input. (Asserts the v020 Q2 opt-out for the `minimal` template.)
> - The prompt MUST emit a single `files[]` entry whose path is `SPECIFICATION.md` per the template's `spec_root: "./"` + single-file positioning.

with the following four-bullet block (two property names + the assertion-function contract for each):

> - `sub_specs_always_empty` — the prompt MUST emit `sub_specs: []` regardless of any pre-seed dialogue input. Asserts the v020 Q2 opt-out for the `minimal` template. **Assertion function**: `replayed_response.sub_specs` is the empty list, regardless of `input_context.ships_own_templates` or `input_context.named_templates`.
> - `single_specification_md_file` — the prompt MUST emit a single `files[]` entry whose path is `SPECIFICATION.md` per the template's `spec_root: "./"` + single-file positioning. **Assertion function**: `replayed_response.files[]` has exactly one entry whose `path` field equals `"SPECIFICATION.md"`.
> - **Assertion-function contract.** Same shape as the livespec-template catalogue contracts (sub-spec v003+): each property's assertion function lives in `tests/prompts/minimal/_assertions.py` keyed by the property's string name in the `ASSERTIONS` dict, accepts keyword-only `*, replayed_response: object, input_context: object`, and raises `AssertionError` on violation.
> - **Catalogue widening rule.** Same shape as the livespec-template rule: future per-prompt regeneration cycles MAY add properties; each new property's assertion function lands in `_assertions.py` in the same revise commit per the in-line widening rule (Plan §3543-3550).

