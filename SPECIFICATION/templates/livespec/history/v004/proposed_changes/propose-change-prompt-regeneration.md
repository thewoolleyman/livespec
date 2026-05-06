---
topic: propose-change-prompt-regeneration
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T00:32:54Z
---

## Proposal: Propose-change-prompt catalogue widening with property keys + assertion contract

### Target specification files

- SPECIFICATION/templates/livespec/contracts.md

### Summary

Widen the catalogue's `prompts/propose-change.md` subsection at SPECIFICATION/templates/livespec/contracts.md by assigning explicit string-key names to its two existing semantic properties (`target_files_within_spec_target` and `bcp14_in_proposed_changes`) and documenting their assertion-function contracts.

### Motivation

Phase 7 sub-step (c).2 lands the in-line per-prompt regeneration cycle for prompts/propose-change.md per Plan §3543-3550. Mirrors the (c).1 pattern: catalogue widening + regenerated prompt + fixture update + assertion functions land atomically in the next revise commit. The two existing prose bullets become formal property names with mechanically-checkable assertion functions: target-files-within-spec-target verifies every finding's target_spec_files paths start with input_context.spec_target; bcp14-in-proposed-changes verifies the proposed_changes prose contains at least one BCP14 keyword.

### Proposed Changes

One atomic edit to **SPECIFICATION/templates/livespec/contracts.md** §"Per-prompt semantic-property catalogue → prompts/propose-change.md" (the bullet block at lines 27-28).

Replace the two existing bullets:

> - The prompt MUST elicit per-finding `target_spec_files` referencing the spec-file paths under the `--spec-target` tree. Findings whose `target_spec_files` reference paths outside `--spec-target` are malformed.
> - The prompt SHOULD apply BCP14 normative language (`MUST`, `SHOULD`, `MAY`) in the `proposed_changes` prose so the resulting propose-change file flows into the spec under the same discipline.

with the following four-bullet block (two property names + the assertion-function contract for each):

> - `target_files_within_spec_target` — the prompt MUST elicit per-finding `target_spec_files` referencing the spec-file paths under the `--spec-target` tree. Findings whose `target_spec_files` reference paths outside `--spec-target` are malformed. **Assertion function**: every entry in `replayed_response.findings[]`'s `target_spec_files` array is a path string whose prefix matches `input_context.spec_target` (treating both as POSIX-relative paths).
> - `bcp14_in_proposed_changes` — the prompt SHOULD apply BCP14 normative language (`MUST`, `SHOULD`, `MAY`, `MUST NOT`, `SHOULD NOT`, `MAY NOT`) in the `proposed_changes` prose so the resulting propose-change file flows into the spec under the same discipline. **Assertion function**: every entry in `replayed_response.findings[]`'s `proposed_changes` string contains at least one BCP14 keyword (whole-word match, uppercase).
> - **Assertion-function contract.** Same shape as the prompts/seed.md catalogue contract (sub-step (c).1, v003): each property's assertion function lives in `tests/prompts/livespec/_assertions.py` keyed by the property's string name in the `ASSERTIONS` dict, accepts keyword-only `*, replayed_response: object, input_context: object`, and raises `AssertionError` on violation.
> - **Catalogue widening rule.** Same shape as v003: future per-prompt regeneration cycles MAY add properties; each new property's assertion function lands in `_assertions.py` in the same revise commit.

