---
proposal: recast-layer-3-livespec-only-orchestration.md
decision: accept
revised_at: 2026-05-27T07:40:55Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Accept all 5 findings as authored. The per-repo Layer 3 slot has been demonstrably unused across multiple cross-repo epics; recasting Layer 3 as livespec-resident matches what the architecture is in practice. Coordinated edits across spec.md, non-functional-requirements.md, and contracts.md keep cross-references consistent. The driver contract (mode, budget, janitor as hard gate, structured iteration journal) stays intact; what changes is WHERE the driver lives.

## Resulting Changes

- spec.md
- non-functional-requirements.md
- contracts.md
