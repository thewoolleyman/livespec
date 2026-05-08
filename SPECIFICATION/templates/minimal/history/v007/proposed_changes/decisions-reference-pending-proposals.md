---
topic: decisions-reference-pending-proposals
author: claude-opus-4-7
created_at: 2026-05-07T20:31:59Z
---

## Proposal: Replace walks_every_pending_proposal with inverse-only decisions_reference_pending_proposals (minimal template)

### Target specification files

- SPECIFICATION/templates/minimal/contracts.md

### Summary

Mirror the livespec sub-spec catalogue change in the minimal sub-spec: replace `walks_every_pending_proposal` in the `prompts/revise.md` catalogue with a renamed inverse-only `decisions_reference_pending_proposals` assertion. Same shape and semantics as the parallel livespec-template proposal; per-template `_assertions.py` registries hold independent function definitions per the v014 fixture-pattern. This brings the minimal-template prompt-QA harness into alignment with the v052 main-spec relaxation that permits selective per-proposal revise.

### Motivation

The v052 main-spec change (cut on 2026-05-07) relaxed the `revise` lifecycle clause (h) so a single revise pass MAY process a chosen subset of pending proposals. The wrapper-level rule changed; the prompt-QA harness assertion in this minimal sub-spec catalogue did NOT — it still asserts the old subset-coverage relationship requiring every pending to appear in decisions[]. The two layers are now contradictory: the main spec permits selective subsets, but the catalogue rejects them as 'silent-data-loss bugs'. The catalogue assertion needs the same relaxation. The inverse direction (every decision MUST reference a pending) is still worth keeping — it catches typos and stale topic references in LLM-emitted JSON; it's the meaningful invariant once the subset requirement drops. The minimal template carries the same property as the livespec template (per the v014 fixture-pattern) so the relaxation MUST land symmetrically across both sub-specs.

### Proposed Changes

The `prompts/revise.md` catalogue subsection in `SPECIFICATION/templates/minimal/contracts.md` MUST be revised in two places.

**Change 1 — replace the `walks_every_pending_proposal` bullet.** The current bullet — *"`walks_every_pending_proposal` — the prompt MUST walk every pending proposed-change file under `<spec-target>/proposed_changes/` (excluding the skill-owned `README.md`) before composing the revise-input JSON. Skipping a pending proposal is a silent-data-loss bug. **Assertion function**: the set of topic-stems extracted from `input_context.pending_proposals[]` is a subset of `replayed_response.decisions[].proposal_topic`'s set. Same assertion shape as the livespec-template `walks_every_pending_proposal` property; per-template `_assertions.py` registries hold independent function definitions (with identical behavior) per the v014 fixture-pattern."* — MUST be replaced with the following:

> - `decisions_reference_pending_proposals` — the prompt MAY emit decisions for any subset of pending proposed-change files under `<spec-target>/proposed_changes/` (excluding the skill-owned `README.md`); selective per-proposal coverage is supported per `SPECIFICATION/spec.md` §"Sub-command lifecycle" (v052) revise lifecycle clause (h). Every entry in `replayed_response.decisions[].proposal_topic` MUST, however, reference an actually-pending proposed-change canonical topic — extras (decisions whose topic does NOT match any pending proposal stem) indicate stale or typo'd topic references and are a bug. **Assertion function**: every entry in `replayed_response.decisions[].proposal_topic` is a member of the topic-stem set extracted from `input_context.pending_proposals[]`. Same assertion shape as the livespec-template `decisions_reference_pending_proposals` property; per-template `_assertions.py` registries hold independent function definitions (with identical behavior) per the v014 fixture-pattern.

**Change 2 — preserve the rest of the catalogue.** All other catalogue entries in this subsection (specifically `per_proposal_disposition_with_rationale`, the **Assertion-function contract** and **Catalogue widening rule** trailers) MUST remain unchanged. The relaxation is scoped to the single property being renamed.

**Downstream code follow-ups (NOT part of this proposal; required before the prompt-QA harness can run cleanly).** After this proposal lands as a revision in the minimal sub-spec tree, two code-tier changes follow:

1. The `_assertions.py` registry under `tests/prompts/minimal/` MUST rename the registry key from `"walks_every_pending_proposal"` to `"decisions_reference_pending_proposals"` and update the function body to assert the inverse-only direction.
2. The fixture under `tests/prompts/minimal/` that exercises the assertion MUST be updated to reflect the renamed property and inverse-only semantics.

The parallel livespec-template proposal (filed separately as a sibling) covers the symmetric change in `SPECIFICATION/templates/livespec/contracts.md`.
