---
topic: decisions-reference-pending-proposals
author: claude-opus-4-7
created_at: 2026-05-07T20:31:27Z
---

## Proposal: Replace walks_every_pending_proposal with inverse-only decisions_reference_pending_proposals

### Target specification files

- SPECIFICATION/templates/livespec/contracts.md

### Summary

Replace the `walks_every_pending_proposal` semantic property in the `prompts/revise.md` catalogue (livespec sub-spec) with a renamed inverse-only `decisions_reference_pending_proposals` assertion. The new property MUST verify only that every entry in `replayed_response.decisions[].proposal_topic` references an actually-pending proposed-change canonical topic under `input_context.pending_proposals[]`; the requirement that every pending proposal MUST appear in `decisions[]` is removed. This brings the prompt-QA harness into alignment with the v052 main-spec relaxation that permits selective per-proposal revise.

### Motivation

The v052 main-spec change (cut on 2026-05-07) relaxed the `revise` lifecycle clause (h) so a single revise pass MAY process a chosen subset of pending proposals. The wrapper-level rule changed; the prompt-QA harness assertion in this sub-spec catalogue did NOT — it still asserts the old subset-coverage relationship requiring every pending to appear in decisions[]. The two layers are now contradictory: the main spec permits selective subsets, but the catalogue rejects them as 'silent-data-loss bugs'. The catalogue assertion needs the same relaxation. The inverse direction (every decision MUST reference a pending) is still worth keeping — it catches typos and stale topic references in LLM-emitted JSON; it's the meaningful invariant once the subset requirement drops.

### Proposed Changes

The `prompts/revise.md` catalogue subsection in `SPECIFICATION/templates/livespec/contracts.md` MUST be revised in two places.

**Change 1 — replace the `walks_every_pending_proposal` bullet.** The current bullet — *"`walks_every_pending_proposal` — the prompt MUST walk every pending proposed-change file under `<spec-target>/proposed_changes/` (excluding the skill-owned `README.md`) before composing the revise-input JSON. Skipping a pending proposal is a silent-data-loss bug. **Assertion function**: the set of topic-stems extracted from `input_context.pending_proposals[]` (each path's filename stem; e.g., `quiet-flag.md` → `quiet-flag`) is a subset of `replayed_response.decisions[].proposal_topic`'s set. Missing topics fail the assertion; extras (decisions not in pending) are tolerated."* — MUST be replaced with the following:

> - `decisions_reference_pending_proposals` — the prompt MAY emit decisions for any subset of pending proposed-change files under `<spec-target>/proposed_changes/` (excluding the skill-owned `README.md`); selective per-proposal coverage is supported per `SPECIFICATION/spec.md` §"Sub-command lifecycle" (v052) revise lifecycle clause (h). Every entry in `replayed_response.decisions[].proposal_topic` MUST, however, reference an actually-pending proposed-change canonical topic — extras (decisions whose topic does NOT match any pending proposal stem) indicate stale or typo'd topic references and are a bug. **Assertion function**: every entry in `replayed_response.decisions[].proposal_topic` is a member of the topic-stem set extracted from `input_context.pending_proposals[]` (each path's filename stem; e.g., `quiet-flag.md` → `quiet-flag`). Decisions whose topic is NOT in pending fail the assertion; pending proposals NOT covered by decisions are tolerated (selective revise).

**Change 2 — preserve the rest of the catalogue.** All other catalogue entries in this subsection (specifically `per_proposal_disposition_with_rationale`, the **Assertion-function contract** and **Catalogue widening rule** trailers) MUST remain unchanged. The relaxation is scoped to the single property being renamed.

**Downstream code follow-ups (NOT part of this proposal; required before the prompt-QA harness can run cleanly).** After this proposal lands as a revision in the livespec sub-spec tree, three code-tier changes follow:

1. The `_assertions.py` registry under `tests/prompts/livespec/` MUST rename the registry key from `"walks_every_pending_proposal"` to `"decisions_reference_pending_proposals"` and update the function body to assert the inverse-only direction (every emitted topic in decisions[].proposal_topic is a member of input_context.pending_proposals[]'s topic-stem set; missing pendings are tolerated; extras fail).
2. The fixture under `tests/prompts/livespec/` that exercises the assertion MUST be updated to reflect the renamed property and inverse-only semantics.
3. The minimal sub-spec mirrors this same property under `SPECIFICATION/templates/minimal/contracts.md`; a parallel propose-change cycle MUST be filed against that sub-spec to bring it into alignment. (Filed separately as a sibling proposal.)
