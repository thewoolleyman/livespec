---
proposal: migrate-auto-memory-project-architecture-entries.md
decision: accept
revised_at: 2026-05-26T23:50:54Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Both remaining sub-proposals codify durable architectural commitments currently held only in agent auto-memory: (1) the research/workflow-processes/ tool-agnostic-vs-implementation-specific split (prevents the conceptual model from being recursively tangled with livespec naming), and (2) the vendored-lib pyright resolution discipline (extraPaths + stubPath + per-vendor stubs) that is required across every livespec-impl-* sibling repo. The first sub-proposal (tmp/ ownership) was removed from this PC because the user clarified 2026-05-27 that tmp/ is transient scaffolding during canonical-workflow evolution, not a permanent architectural commitment — codifying it would violate the 'spec is for contracts, not tracking' rule. The modified PC accepts the two remaining sub-proposals verbatim.

## Resulting Changes

- non-functional-requirements.md
