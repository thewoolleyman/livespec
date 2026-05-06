---
topic: minimal-revise-prompt-regeneration
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T02:05:00Z
---

## Proposal: Minimal revise-prompt catalogue widening

### Target specification files

- SPECIFICATION/templates/minimal/contracts.md

### Summary

Widen the minimal-template revise-prompt catalogue with named properties walks_every_pending_proposal + per_proposal_disposition_with_rationale. Same assertion shape as livespec-template registry; per-template independence per v014 fixture pattern.

### Motivation

Phase 7 sub-step (d).4 lands the per-prompt regeneration cycle for minimal revise per Plan §3543-3550.

### Proposed Changes

One atomic edit to **SPECIFICATION/templates/minimal/contracts.md** §"Per-prompt semantic-property catalogue → prompts/revise.md, prompts/critique.md" (the bundled placeholder block remaining after sub-step (d).3 split off propose-change).

Replace:

> ### `prompts/revise.md`, `prompts/critique.md`
>
> Bootstrap-minimum at Phase 6 (continued): each prompt's catalogue is a single placeholder property — "the prompt MUST emit valid `<schema>`-conforming JSON when given a well-formed user-described change". Phase 7 sub-steps (d).4 / (d).5 widen each subsection independently per the in-line widening rule.

with the following two-subsection block (revise widened; critique still placeholder):

> ### `prompts/revise.md`
>
> - `walks_every_pending_proposal` — the prompt MUST walk every pending proposed-change file under `<spec-target>/proposed_changes/` (excluding the skill-owned `README.md`) before composing the revise-input JSON. Skipping a pending proposal is a silent-data-loss bug. **Assertion function**: the set of topic-stems extracted from `input_context.pending_proposals[]` is a subset of `replayed_response.decisions[].proposal_topic`'s set. Same assertion shape as the livespec-template `walks_every_pending_proposal` property; per-template `_assertions.py` registries hold independent function definitions (with identical behavior) per the v014 fixture-pattern.
> - `per_proposal_disposition_with_rationale` — the prompt MUST emit a per-proposal disposition (`accept`, `reject`, or `modify`) with a non-empty rationale per disposition. **Assertion function**: every entry in `replayed_response.decisions[]` has a `decision` field in `{"accept", "modify", "reject"}` AND a non-empty whitespace-stripped `rationale` field.
> - **Assertion-function contract** + **Catalogue widening rule.** Same shape as the livespec-template catalogue contracts.
>
> ### `prompts/critique.md`
>
> Bootstrap-minimum at Phase 6 (continued): the prompt's catalogue is a single placeholder property — "the prompt MUST emit valid `<schema>`-conforming JSON when given a well-formed user-described change". Phase 7 sub-step (d).5 widens this subsection independently per the in-line widening rule.

