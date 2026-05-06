---
topic: revise-prompt-regeneration
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T00:37:57Z
---

## Proposal: Revise-prompt catalogue widening with property keys + assertion contract

### Target specification files

- SPECIFICATION/templates/livespec/contracts.md

### Summary

Widen the catalogue's `prompts/revise.md` subsection at SPECIFICATION/templates/livespec/contracts.md by assigning explicit string-key names to its two existing semantic properties (`walks_every_pending_proposal` and `per_proposal_disposition_with_rationale`) and documenting their assertion-function contracts.

### Motivation

Phase 7 sub-step (c).3 lands the in-line per-prompt regeneration cycle for prompts/revise.md per Plan §3543-3550. Mirrors (c).1 / (c).2.

### Proposed Changes

One atomic edit to **SPECIFICATION/templates/livespec/contracts.md** §"Per-prompt semantic-property catalogue → prompts/revise.md" (the bullet block at lines 32-33).

Replace the two existing bullets:

> - The prompt MUST walk every pending proposed-change file under `<spec-target>/proposed_changes/` (excluding the skill-owned `README.md`) before composing the revise-input JSON. Skipping a pending proposal is a silent-data-loss bug; the v018 Q5 harness MUST detect missing per-proposal entries.
> - The prompt MUST emit a per-proposal disposition (`accept` or `reject`) with a one-line rationale per disposition.

with the following four-bullet block (two property names + the assertion-function contract for each):

> - `walks_every_pending_proposal` — the prompt MUST walk every pending proposed-change file under `<spec-target>/proposed_changes/` (excluding the skill-owned `README.md`) before composing the revise-input JSON. Skipping a pending proposal is a silent-data-loss bug. **Assertion function**: the set of topic-stems extracted from `input_context.pending_proposals[]` (each path's filename stem; e.g., `quiet-flag.md` → `quiet-flag`) is a subset of `replayed_response.decisions[].proposal_topic`'s set. Missing topics fail the assertion; extras (decisions not in pending) are tolerated.
> - `per_proposal_disposition_with_rationale` — the prompt MUST emit a per-proposal disposition (`accept`, `reject`, or `modify`) with a non-empty rationale per disposition. **Assertion function**: every entry in `replayed_response.decisions[]` has a `decision` field in `{"accept", "modify", "reject"}` AND a non-empty whitespace-stripped `rationale` field. Schema validation already enforces field presence + the enum; this assertion strengthens the rationale check (whitespace-only rationales fail).
> - **Assertion-function contract.** Same shape as v003/v004 (sub-steps (c).1 / (c).2 catalogue contracts).
> - **Catalogue widening rule.** Same shape as v003/v004.

