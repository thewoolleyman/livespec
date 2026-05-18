---
proposal: multi-repo-distribution-and-coordination.md
decision: accept
revised_at: 2026-05-18T20:03:27Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Accept the entire multi-repo-distribution-and-coordination proposed-change (three proposal sections) as a single atomic landing. This proposal is FIRST in the post-orchestration dependency order and forward-defines mechanisms (plugin rename to livespec-core, sibling-repo topology, pin-and-bump compat block, copier shared-content sync, Implementation plugin ecosystem section) that the three later proposals in the batch reference. Spec-target-relative resulting_files cover both target files: contracts.md (Plugin distribution rewrite, new Cross-repo coordination section, new Shared content sync section) and non-functional-requirements.md (Repo-local implementation workflow replaced with Implementation plugin ecosystem + Shared content provenance sub-section; five enumerated beads-cluster sections removed and replaced with one-paragraph Implementation-plugin contract delegation stub; Codex dogfooding compatibility updated for sibling-repo split; Codex dogfooding contracts table renamed /livespec:* -> /livespec-core:* with the deferred /livespec-impl-* mapping noted; bd toolchain-pin cross-reference updated to point at the impl plugin's own spec; scenario slash-command references renamed consistent with the contract-level rename). Sibling proposed-change files for implementation-plugin-contract-9-skill-surface, doctor-invariant-catalog-expansion, and orchestration-layer-and-memo-paradigm are intentionally NOT covered by a decision in this pass (selective revise per spec.md revise lifecycle clause h); they remain in proposed_changes/ for subsequent revise sessions per the dependency-ordered batch plan.

## Resulting Changes

- contracts.md
- non-functional-requirements.md
