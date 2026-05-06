---
topic: minimal-critique-prompt-regeneration
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T02:10:20Z
---

## Proposal: Minimal critique-prompt catalogue widening

### Target specification files

- SPECIFICATION/templates/minimal/contracts.md

### Summary

Widen the minimal-template critique-prompt catalogue with target_is_single_specification_md (reused from propose-change) + new prioritizes_ambiguity_over_style.

### Motivation

Phase 7 sub-step (d).5 closes the per-prompt regeneration cycle for the minimal template's REQUIRED prompts (seed/propose-change/revise/critique now all widened). Closes (d).5; (d).6 single-file starter content remains for Phase 7.

### Proposed Changes

One atomic edit to **SPECIFICATION/templates/minimal/contracts.md** §"Per-prompt semantic-property catalogue → prompts/critique.md" (the placeholder block remaining after sub-step (d).4 split off revise).

Replace:

> ### `prompts/critique.md`
>
> Bootstrap-minimum at Phase 6 (continued): the prompt's catalogue is a single placeholder property — "the prompt MUST emit valid `<schema>`-conforming JSON when given a well-formed user-described change". Phase 7 sub-step (d).5 widens this subsection independently per the in-line widening rule.

with:

> ### `prompts/critique.md`
>
> - `target_is_single_specification_md` — the prompt MUST emit per-finding `target_spec_files` containing exactly `["SPECIFICATION.md"]` (the minimal template's single-file output). **Assertion function**: every entry in `replayed_response.findings[]`'s `target_spec_files` array equals exactly `["SPECIFICATION.md"]`. Reuses the same registry entry as the propose-change subsection — single-file targeting is uniform across both critique and propose-change findings since both consume the `proposal_findings.schema.json` shape.
> - `prioritizes_ambiguity_over_style` — the prompt SHOULD prioritize ambiguities and contradictions over wording-style suggestions. **Assertion function**: every entry in `replayed_response.findings[]`'s `motivation` field contains at least one of the keywords from the ambiguity / contradiction lexicon (`ambiguity`, `ambiguous`, `contradiction`, `contradicts`, `contradictory`, `unclear`, `inconsistent`, `inconsistency`, `silent`, `undefined`) — case-insensitive substring match. Same assertion shape as the livespec-template `prioritizes_ambiguity_over_style` property.
> - **Assertion-function contract** + **Catalogue widening rule.** Same shape as the livespec-template catalogue contracts.

