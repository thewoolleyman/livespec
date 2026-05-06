---
topic: minimal-propose-change-prompt-regeneration
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T02:01:12Z
---

## Proposal: Minimal propose-change-prompt catalogue widening

### Target specification files

- SPECIFICATION/templates/minimal/contracts.md

### Summary

Widen the catalogue's `prompts/propose-change.md` subsection at SPECIFICATION/templates/minimal/contracts.md from the bootstrap-minimum placeholder to two named properties (`target_is_single_specification_md` and `bcp14_in_proposed_changes`) with assertion-function contracts.

### Motivation

Phase 7 sub-step (d).3 lands the in-line per-prompt regeneration cycle for the minimal template's prompts/propose-change.md per Plan §3543-3550.

### Proposed Changes

One atomic edit to **SPECIFICATION/templates/minimal/contracts.md** §"Per-prompt semantic-property catalogue → prompts/propose-change.md, prompts/revise.md, prompts/critique.md" (the shared placeholder block at lines 33-35).

The current section bundles all three remaining minimal-template prompts under a single placeholder bullet:

> ### `prompts/propose-change.md`, `prompts/revise.md`, `prompts/critique.md`
>
> Bootstrap-minimum at Phase 6: each prompt's catalogue is a single placeholder property documenting the Phase 7 widening intent. The placeholder property is "the prompt MUST emit valid `<schema>`-conforming JSON when given a well-formed user-described change". Phase 7 widens each catalogue to the full assertion surface.

This proposal splits the bundled placeholder into a per-prompt subsection and widens ONLY the propose-change subsection (sub-step (d).3); the revise + critique subsections retain placeholder framing until their own sub-step ((d).4 / (d).5) cycles widen them.

Replace the bundled placeholder with:

> ### `prompts/propose-change.md`
>
> - `target_is_single_specification_md` — the prompt MUST emit per-finding `target_spec_files` containing exactly `["SPECIFICATION.md"]` (the minimal template's single-file output). **Assertion function**: every entry in `replayed_response.findings[]`'s `target_spec_files` array equals exactly `["SPECIFICATION.md"]` (length 1, single element matching the literal string).
> - `bcp14_in_proposed_changes` — the prompt SHOULD apply BCP14 normative language (`MUST`, `SHOULD`, `MAY`, `MUST NOT`, `SHOULD NOT`, `MAY NOT`) in the `proposed_changes` prose so the resulting propose-change file flows into the spec under the same discipline. **Assertion function**: every entry in `replayed_response.findings[]`'s `proposed_changes` string contains at least one BCP14 keyword (whole-word match, uppercase).
> - **Assertion-function contract.** Same shape as the livespec-template catalogue contracts.
> - **Catalogue widening rule.** Same shape as the livespec-template rule.
>
> ### `prompts/revise.md`, `prompts/critique.md`
>
> Bootstrap-minimum at Phase 6 (continued): each prompt's catalogue is a single placeholder property — "the prompt MUST emit valid `<schema>`-conforming JSON when given a well-formed user-described change". Phase 7 sub-steps (d).4 / (d).5 widen each subsection independently per the in-line widening rule.

