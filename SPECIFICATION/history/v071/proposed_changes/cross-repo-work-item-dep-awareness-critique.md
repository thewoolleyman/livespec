---
topic: cross-repo-work-item-dep-awareness-critique
author: claude-opus-4-7
created_at: 2026-05-22T02:32:58Z
---

## Proposal: fix-blocked-urgency-band-contradiction

### Target specification files

- proposed_changes/cross-repo-work-item-dep-awareness.md

### Summary

Finding #1 (cross-repo-dep-work-item-metadata-fields) MUST drop the `blocked` urgency band alternative and specify ONLY `excluded from the ranked candidates list` as the deterministic disposition for unsatisfied external deps.

### Motivation

Doctor LLM-driven phase surfaced two coupled issues: (a) `blocked` is undefined in the current urgency enum [high, medium, low], and the parallel `next-ranked-candidates-list-and-pagination` proposal explicitly says urgency semantics MUST remain identical, so the two proposals contradict if `blocked` is allowed. (b) The clause `impl-plugin author's choice ... the contract MUST specify ONE of these dispositions per impl-plugin` is itself self-contradictory (either the cross-plugin contract picks once globally, or each impl-plugin picks per-impl, but not both). User architectural decision: drop the `blocked` band; specify exclude-only as the single deterministic cross-plugin disposition.

### Proposed Changes

The disjunctive disposition clause in finding #1's `proposed_changes` body MUST be replaced with a single deterministic clause. The current text:

> The impl-side `next` ranker MUST honor `external_dep_cache[ref].status == "open"` for any `ref` declared in `depends_on_external` as a hard blocker: work-items with at least one unsatisfied external dep MUST NOT appear in the ranked candidates list, OR MUST appear with an explicit `blocked` urgency band (impl-plugin author's choice; the contract MUST specify ONE of these dispositions per impl-plugin to keep behavior deterministic).

MUST become:

> The impl-side `next` ranker MUST honor `external_dep_cache[ref].status == "open"` for any `ref` declared in `depends_on_external` as a hard blocker: work-items with at least one unsatisfied external dep MUST be excluded from the ranked candidates list entirely. The urgency enum (`high`, `medium`, `low`) is unchanged; blocked work-items simply do not appear as candidates.

This preserves consistency with the parallel `next-ranked-candidates-list-and-pagination` proposal's clause that urgency field semantics MUST remain identical to the current single-output shape.

## Proposal: fix-cross-repo-targets-example-plugin-name

### Target specification files

- proposed_changes/cross-repo-work-item-dep-awareness.md

### Summary

Finding #4 (cross-repo-dep-livespec-jsonc-target-block) MUST correct the `cross_repo_targets` example: the `livespec-core` target's `plugin` field MUST be `"livespec-impl-plaintext"`, not `"livespec"`.

### Motivation

Doctor LLM-driven spec-impl-drift check flagged a factual error: the example shows `"livespec-core": {"plugin": "livespec"}`, but `livespec` is the spec-side plugin and does NOT expose `list-work-items` (only impl plugins do, per the 9-skill surface contract). The actual impl plugin used by livespec-core is `livespec-impl-plaintext`, verified against `/data/projects/livespec/.livespec.jsonc` field `implementation.plugin: "livespec-impl-plaintext"`.

### Proposed Changes

The JSON example in finding #4's `proposed_changes` body MUST be corrected. The livespec-core entry's `plugin` field MUST change from `"livespec"` to `"livespec-impl-plaintext"`. The corrected example:

```jsonc
"livespec-core": {
  "path": "../livespec",
  "plugin": "livespec-impl-plaintext"
}
```

A clarifying sentence SHOULD be added immediately after the example: `The plugin field MUST always name the impl-plugin (the one exposing list-work-items), never the spec-side plugin. Cross-repo work-item lookups always route through impl plugins per the 9-skill surface contract.`

## Proposal: remove-memory-file-reference-from-spec-content

### Target specification files

- proposed_changes/cross-repo-work-item-dep-awareness.md

### Summary

Finding #2 (cross-repo-dep-resolver-skill) MUST NOT reference the LLM-session memory file `feedback_user_extensions_minimal_requirements.md` in spec content; the principle MUST be restated in spec-native terms.

### Motivation

Doctor LLM-driven prose-quality check flagged that memory files are LLM-session artifacts and NOT part of the durable spec. Cross-references from spec content to memory files leak transient session context into permanent spec content. The cited principle (cross-plugin contracts MUST remain agnostic to per-implementation field additions) SHOULD be restated in spec-native language.

### Proposed Changes

The parenthetical reference `(per feedback_user_extensions_minimal_requirements.md)` MUST be removed from the relevant sentence in finding #2's `proposed_changes` body. The current sentence:

> The contract MUST NOT prescribe the candidate object's `additionalProperties` discipline at the cross-plugin contract level (per `feedback_user_extensions_minimal_requirements.md`); impl-plugin authors own their per-implementation schema.

MUST become:

> The contract MUST NOT prescribe the candidate object's `additionalProperties` discipline at the cross-plugin contract level: impl-plugin authors own their per-implementation schema, and the cross-plugin contract surface MUST remain agnostic to per-implementation field additions.
