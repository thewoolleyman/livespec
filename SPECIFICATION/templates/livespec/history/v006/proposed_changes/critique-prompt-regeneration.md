---
topic: critique-prompt-regeneration
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T00:42:28Z
---

## Proposal: Critique-prompt catalogue widening with property keys + assertion contract

### Target specification files

- SPECIFICATION/templates/livespec/contracts.md

### Summary

Widen the catalogue's `prompts/critique.md` subsection at SPECIFICATION/templates/livespec/contracts.md by assigning explicit string-key names to its two existing semantic properties (`findings_grounded_in_spec_target` and `prioritizes_ambiguity_over_style`) and documenting their assertion-function contracts.

### Motivation

Phase 7 sub-step (c).4 lands the in-line per-prompt regeneration cycle for prompts/critique.md per Plan §3543-3550. Mirrors (c).1 / (c).2 / (c).3.

### Proposed Changes

One atomic edit to **SPECIFICATION/templates/livespec/contracts.md** §"Per-prompt semantic-property catalogue → prompts/critique.md" (the bullet block).

Replace the two existing bullets:

> - The prompt MUST ground each finding against the spec target's current state. Critique findings MUST carry `target_spec_files` referencing files that exist in the target tree.
> - The prompt SHOULD prioritize ambiguities and contradictions over wording-style suggestions; the latter belong in a separate cleanup-style propose-change cycle.

with the following four-bullet block (two property names + the assertion-function contract for each):

> - `findings_grounded_in_spec_target` — the prompt MUST ground each finding against the spec target's current state. Critique findings MUST carry `target_spec_files` referencing files that exist in the target tree. **Assertion function**: every entry in `replayed_response.findings[]`'s `target_spec_files` array is a path string present in `input_context.current_spec_files[]` (the harness-passed enumeration of files that exist in the spec target at invocation time).
> - `prioritizes_ambiguity_over_style` — the prompt SHOULD prioritize ambiguities and contradictions over wording-style suggestions; the latter belong in a separate cleanup-style propose-change cycle. **Assertion function**: every entry in `replayed_response.findings[]`'s `motivation` field contains at least one of the keywords from the ambiguity / contradiction lexicon (`ambiguity`, `ambiguous`, `contradiction`, `contradicts`, `contradictory`, `unclear`, `inconsistent`, `inconsistency`, `silent`, `undefined`) — case-insensitive substring match. The lexicon is heuristic and intentionally permissive; richer semantic checks live in the doctor LLM-driven subjective phase.
> - **Assertion-function contract.** Same shape as the v003/v004/v005 catalogue contracts.
> - **Catalogue widening rule.** Same shape as v003/v004/v005.

