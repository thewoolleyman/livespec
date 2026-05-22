---
topic: next-prune-history-config-and-ordering
author: claude-opus-4-7
created_at: 2026-05-21T23:13:36Z
---

## Proposal: prune-history-threshold-configurable-via-livespec-jsonc

### Target specification files

- contracts.md

### Summary

The hardcoded `_PRUNE_HISTORY_THRESHOLD = 20` constant in the spec-side `next` ranker MUST become configurable via `.livespec.jsonc` so projects can tune the prune-history recommendation cadence to their history-accretion rate.

### Motivation

Today the ranker fires `prune-history` once history reaches 20 unpruned `vNNN/` directories, with no way to defer the recommendation for projects on a longer cadence. This repo currently shows 70 unpruned versions and the recommendation triggers on every `next` invocation, even though pruning is housekeeping rather than the most-ripe move. Different specs evolve at different rates; the threshold MUST be project-tunable so the recommendation surfaces at a cadence matched to the project's pruning rhythm.

### Proposed Changes

Add a project-level `.livespec.jsonc` configuration block scoped to the `next` ranker:

```jsonc
{
  "next": {
    "prune_history_threshold": 20
  }
}
```

The `next` wrapper MUST read `next.prune_history_threshold` from `.livespec.jsonc` on each invocation. When the key is absent, the wrapper MUST fall back to the current default value of `20`. When the key is present, its value MUST be a positive integer; any non-positive-integer value MUST cause the wrapper to exit `3` with a `PreconditionError` naming the offending key and value.

Update `contracts.md` §"`/livespec:next` spec-side thin-transport skill" with a new sub-paragraph describing the configuration key, its default, its validation rule, and its semantics (a project MAY raise the threshold to defer prune-history recommendations on long-lived specs; a project MAY lower it to surface pruning sooner).

## Proposal: prune-history-strictly-last-in-next-ranking

### Target specification files

- contracts.md

### Summary

The spec-side `next` skill's output contract MUST encode `prune-history` as strictly the lowest-priority action: it MUST NOT be emitted as the primary recommendation whenever ANY other action (`revise`, `propose-change`, `critique`) is ripe, regardless of whether the prune-history threshold is met.

### Motivation

Pruning is housekeeping, not actionable spec evolution. Today the ranker happens to enforce this implicitly because `prune-history` only fires when `proposal_count == 0`, but the contract does not codify the ordering invariant. As the ranker is extended to emit `critique` and `propose-change` actions (per the parallel pagination + multi-candidate-ranking proposal), the invariant MUST hold across the expanded action set so users are never directed at housekeeping when there is real work pending.

### Proposed Changes

Amend `contracts.md` §"`/livespec:next` spec-side thin-transport skill" to add a normative ordering clause:

> The `next` ranker MUST rank `prune-history` strictly below every other action in the `action` enumeration. When ANY ripe candidate exists with `action != prune-history` (i.e., `revise`, `propose-change`, or `critique`), the ranker MUST NOT emit `prune-history` as the primary recommendation. The `urgency: "low"` label on prune-history is a soft signal; this ordering invariant is a hard constraint independent of urgency.

The invariant SHOULD be exercised by a unit test that constructs a spec tree with BOTH a non-empty `proposed_changes/` queue AND a history accretion above `prune_history_threshold`, then asserts the wrapper's emitted `action` is the queue-driven action (e.g., `revise`), never `prune-history`.
