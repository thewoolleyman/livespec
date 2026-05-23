---
topic: next-ranked-candidates-list-and-pagination
author: claude-opus-4-7
created_at: 2026-05-21T23:15:15Z
---

## Proposal: next-ranked-candidates-list-with-pagination-spec-side

### Target specification files

- contracts.md

### Summary

The spec-side `next` skill's output contract MUST change from a single `{action, reason, urgency}` recommendation to a ranked list of candidates plus pagination metadata, exposed via new wrapper CLI flags `--limit M` (default `5`) and `--offset N` (default `0`).

### Motivation

A single recommendation collapses the real ranking surface. A spec tree can have multiple ripe candidates of the same `action` kind (multiple pending proposed_changes, multiple critique findings, multiple sub-spec targets each with their own queues), and the consumer (the project-local Layer 3 loop driver or the user reading the JSON) loses information when only the top-ranked item is surfaced. Returning the top N candidates plus stateless pagination lets the consumer page through the full ranked surface without server-side cursor state.

### Proposed Changes

The spec-side `next` wrapper MUST change its output shape and CLI surface as follows.

**New CLI flags** (both optional, added to `next.py`):

- `--limit M` — positive integer, default `5`. Maximum number of candidates returned in the `candidates` array.
- `--offset N` — non-negative integer, default `0`. Number of ranked candidates to skip from the front of the ranked list before returning.

Non-positive `--limit` or negative `--offset` MUST cause the wrapper to exit `2` with a `UsageError`.

**New output schema** (replaces the current `next_output.schema.json` shape; this is a clean break, not a backwards-compatible widening):

```jsonc
{
  "candidates": [
    {
      "action": "revise",                            // existing enum
      "reason": "...",                                // existing
      "urgency": "high",                              // existing enum
      "target": "proposed_changes/foo.md"             // optional; spec-target-relative path or identifier for the specific item this candidate refers to
    }
  ],
  "pagination": {
    "offset": 0,                                       // echoed from --offset
    "limit": 5,                                        // echoed from --limit
    "total": 12,                                       // total count of ripe candidates BEFORE offset/limit
    "has_more": true                                   // true iff offset + len(candidates) < total
  }
}
```

The `action`, `reason`, `urgency` field semantics MUST remain identical to the current single-output shape. The new `target` field is OPTIONAL and MAY be omitted when the candidate has no specific target (e.g., `action: "none"` or `action: "prune-history"`). When `offset >= total`, the wrapper MUST emit `candidates: []` and `has_more: false`. The wrapper MUST always emit a valid (possibly empty) `candidates` array; an empty array does NOT degrade to the legacy `{action: "none"}` shape — the empty-candidate-list IS the no-work signal.

**Ranker semantics**: the ranker MUST enumerate ALL ripe candidates (not just the top one), apply the ordering invariant from `next-prune-history-config-and-ordering` (prune-history strictly last), sort within each action tier by urgency descending then by deterministic secondary key (e.g., `target` lexicographic), then apply `offset` + `limit` to produce the returned slice.

**Contracts.md update**: Amend §"`/livespec:next` spec-side thin-transport skill" to describe the new wrapper CLI flags, the new schema shape, the ranker enumeration semantics, and the pagination invariant. Replace `next_output.schema.json` with the new shape; preserve the file path.

## Proposal: next-ranked-candidates-list-with-pagination-impl-side

### Target specification files

- contracts.md

### Summary

The impl-plugin `next` skill contract surface (the `<impl-plugin>:next` row in §"Implementation-plugin contract — the 9-skill surface") MUST mirror the same ranked-list + pagination shape as the spec-side change, so cross-side consumers see a uniform abstraction.

### Motivation

The impl-side ranking surface is even richer than the spec-side: a work-items store typically holds tens to hundreds of items, of which many are simultaneously ripe (untriaged, ready, blocked-cleared, etc.). Today the impl contract requires a single `{action, work_item_ref, urgency, reason}` recommendation. As the project-local Layer 3 loop driver composes cross-side recommendations, it MUST be able to see more than the single top impl-side item. Keeping the impl-side and spec-side `next` output shapes symmetric (both `{candidates[], pagination}` with the same pagination semantics) lets the loop driver treat both sides uniformly.

### Proposed Changes

The impl-plugin `next` skill contract MUST adopt the same ranked-list + pagination shape as the spec-side change.

**Contract amendment** (`contracts.md` §"Implementation-plugin contract — the 9-skill surface", the `next` row): the impl `next` skill MUST accept the same `--limit M` (default `5`) and `--offset N` (default `0`) flags with the same validation rules and exit-2-on-bad-flags behavior.

**Output shape**: identical pagination block; the candidate object MUST carry at minimum `action`, `reason`, `urgency`, AND the impl-side-specific `work_item_ref` field (which was already required by the current contract). The candidate object MAY include additional impl-side-specific fields (e.g., `blocked_by`, `epic`) provided they are documented by the impl plugin's own per-implementation contract.

```jsonc
{
  "candidates": [
    {
      "action": "implement",
      "reason": "...",
      "urgency": "high",
      "work_item_ref": "li-abc123"
    }
  ],
  "pagination": { "offset": 0, "limit": 5, "total": 27, "has_more": true }
}
```

The contract MUST NOT prescribe the candidate object's `additionalProperties` discipline at the cross-plugin contract level (per `feedback_user_extensions_minimal_requirements.md`); impl-plugin authors own their per-implementation schema.

**Conforming impl-plugin update**: the active `livespec-impl-plaintext` impl plugin MUST be updated in its own repo to conform to the new contract; this is tracked as a follow-on impl-side work-item rather than as a change to this spec. The cross-repo coordination invariant in doctor (per `contracts.md` §"Cross-repo coordination — pin-and-bump") will fire if the impl plugin's pinned version falls out of compat with the new contract.
