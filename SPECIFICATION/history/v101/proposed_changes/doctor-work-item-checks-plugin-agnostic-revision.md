---
proposal: doctor-work-item-checks-plugin-agnostic.md
decision: accept
revised_at: 2026-06-09T01:38:29Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Adopt the plugin-agnostic list-work-items-wrapper data-acquisition mechanism for the six work-item integrity invariants, replacing the plaintext-only direct-JSONL-read v1 mechanism. The implementation (the _work_items_provider seam + the rewired checks) already landed in this same branch; this revise records the contract that the code now satisfies, restoring live enforcement under the beads backend while preserving the hermetic-CI skip.

## Resulting Changes

- contracts.md
