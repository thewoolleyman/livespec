---
topic: selective-revise
author: claude-opus-4-7
created_at: 2026-05-07T19:05:06Z
---

## Proposal: Relax revise's all-or-nothing rule to permit selective per-proposal processing

### Target specification files

- SPECIFICATION/spec.md

### Summary

Relax clause (g) of the `revise` lifecycle paragraph in `SPECIFICATION/spec.md` §"Sub-command lifecycle" so a single revise pass MAY process a chosen subset of in-flight proposals and leave the rest in `<spec-target>/proposed_changes/` for a later revise. Add a non-empty-decisions wrapper precondition to keep no-op revises forbidden. Add a skill-prose responsibility to narrate stale-pending-proposal counts at the start of every revise dialogue, so accumulation stays visible without involving any automated gate.

### Motivation

Independent topic streams routinely arrive out-of-sequence in real spec work — for example, this very repository currently has two in-flight proposals where `codex-dogfood-compatibility.md` explicitly references `livespec-implementation-workflow.md` as a prerequisite. Under the current all-or-nothing rule, a single revise pass MUST process both, which either collapses two independent decisions into one diff (loss of audit clarity) or forces a `reject` on a proposal the user wants to keep, requiring re-file from scratch (asymmetric authoring cost — research, references, BCP14-rendered prose, and front-matter all have to be reconstructed). Per-proposal decisions are already encoded in `decisions[]`; the all-or-nothing rule is an artificial coupling layered on top of an already-decomposed design. Selective per-proposal processing is the natural mental model — every change-management system in common use (PRs, RFCs, ADRs) handles each change independently. The strongest argument for the current rule is the risk of stale proposals languishing forever; that risk is addressed by skill-prose narration at revise start (informational only, no gating), not by any new doctor check (which would re-introduce the same forcing-function in a different gate).

### Proposed Changes

The `revise` lifecycle paragraph in `SPECIFICATION/spec.md` §"Sub-command lifecycle" (the paragraph beginning `**`revise` lifecycle and responsibility separation.**`) MUST be revised in three places.

**Change 1 — clause (g) relaxation.** The current clause (g) text — *"after successful completion `<spec-target>/proposed_changes/` MUST be empty of in-flight proposals (the skill-owned `proposed_changes/README.md` persists)"* — MUST be replaced with the following:

> (g) after successful completion `<spec-target>/proposed_changes/` MUST contain exactly the in-flight proposal files whose canonical topic is NOT named in `decisions[]`; every proposal whose canonical topic IS named in `decisions[]` MUST have been moved to `<spec-target>/history/vNNN/proposed_changes/` per clauses (e) and (f). The skill-owned `proposed_changes/README.md` persists across all cases. When `decisions[]` covers every in-flight proposal, this collapses to the empty-of-in-flight-proposals state (the historical behavior); when `decisions[]` covers a strict subset, the unprocessed proposals remain in place for a future revise pass.

**Change 2 — new non-empty-decisions precondition.** A new clause MUST be inserted immediately after clause (a) and before the existing clause (b) (the existing clauses re-letter accordingly so that the existing (b) becomes (c), the existing (c) becomes (d), and so on through to the relaxed (g) above which becomes (h)):

> (b) it MUST fail hard with `UsageError` (exit 2) when the inbound `--revise-json` payload's `decisions[]` array is empty. A revise pass with zero decisions would produce a no-op cut and is forbidden; the schema `revise_input.schema.json` MUST encode this precondition with `minItems: 1` on `decisions[]` (paired with the corresponding dataclass under `livespec/schemas/dataclasses/` per the schema-dataclass-pairing invariant). Together with clause (a), this ensures every successful revise cut represents at least one processed proposal.

**Change 3 — new skill-prose responsibility.** The opening sentence of the `revise` lifecycle paragraph currently enumerates skill-prose responsibilities ("the per-`## Proposal` accept/modify/reject decision-and-rationale capture, the `modify`-decision iteration to convergence, the apply-to-all-remaining-proposals delegation toggle, ..."). One additional skill-prose responsibility MUST be added to that enumeration:

> the start-of-revise stale-pending-proposal narration (the skill prose MUST surface, before the per-proposal accept/modify/reject loop begins, the count of in-flight proposals under `<spec-target>/proposed_changes/` and the canonical topic + `created_at` of the oldest pending proposal, formatted as a single informational line; this narration MUST NOT gate the wrapper, MUST NOT add any pre-step or post-step doctor check, and MUST NOT block downstream wrapper invocations — its sole purpose is pending-proposal-accumulation visibility so the user MAY choose to address older proposals during the current pass)

**Downstream follow-ups (NOT part of this proposal; to be filed separately once this proposal lands).** Two co-required changes will follow this one as their own propose-change → revise cycles, once the rules above are codified:

1. The `walks_every_pending_proposal` semantic property in both `SPECIFICATION/templates/livespec/contracts.md` and `SPECIFICATION/templates/minimal/contracts.md` MUST be relaxed (or replaced with a renamed property) so the prompt-QA harness no longer asserts the subset relationship requiring every pending proposal's topic-stem to appear in `replayed_response.decisions[].proposal_topic`. The replacement assertion SHOULD verify only the inverse direction: every entry in `decisions[].proposal_topic` MUST reference an actually-pending proposed-change canonical topic under `input_context.spec_target/proposed_changes/` (no extras); the requirement that every pending must be covered MUST be removed.
2. The schema `.claude-plugin/scripts/livespec/schemas/revise_input.schema.json` MUST add `"minItems": 1` to the `decisions` array property, paired with its dataclass under `livespec/schemas/dataclasses/` per the schema-dataclass-pairing invariant in `livespec/schemas/CLAUDE.md`.

These two follow-ups are intentionally NOT bundled into this proposal because each lands in a different spec target (this proposal targets the main spec; (1) targets two sub-specs; (2) is implementation/code work that follows the spec landing). Each follow-up can be filed and revised on its own once this main-spec relaxation is recorded.
