---
proposal: realign-contracts-distribution-examples-to-beads.md
decision: accept
revised_at: 2026-06-09T04:03:00Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Phase 7 of the dolt-server beads-migration epic: the livespec family flipped its default impl backend to livespec-impl-beads, and contracts.md's illustrative distribution/example bodies still named livespec-impl-plaintext (and a jsonl format value). Accept as-proposed — three prose/example-body edits that bring the spec's own examples into lockstep with the active beads backend. No `## ` H2 heading is added, removed, or renamed, so tests/heading-coverage.json is untouched.

## Resulting Changes

- contracts.md
