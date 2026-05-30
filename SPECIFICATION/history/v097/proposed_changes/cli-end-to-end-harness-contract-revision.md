---
proposal: cli-end-to-end-harness-contract.md
decision: accept
revised_at: 2026-05-30T22:44:20Z
author_human: E2E Test <e2e-test@example.com>
author_llm: livespec-orchestrate
---

## Decision and Rationale

Accepted as-filed (epic li-e2ecli Phase 1). Adds the '## CLI end-to-end harness contract' section to contracts.md encoding the 7 normative requirements for a top-of-pyramid, user-surface e2e tier that drives the claude CLI binary itself; placed after the existing '## E2E harness contract' whose lead is amended to name it the wrapper-chain tier (sibling to, not superset of, the new tier). Registers the new H2 in tests/heading-coverage.json as a TODO pending the real test from Epic D Waves 11-12 (li-e2ecdt/li-e2eclv/li-e2ecpx).

## Resulting Changes

- contracts.md
- ../tests/heading-coverage.json
