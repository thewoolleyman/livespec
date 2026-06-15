---
proposal: graduate-architecture-diagram-into-spec-dry.md
decision: accept
revised_at: 2026-06-15T03:53:44Z
author_human: E2E Test <e2e-test@example.com>
author_llm: livespec-zkmn-diagram-dry
---

## Decision and Rationale

Accept as authored. W7/zkmn diagram codification, done DRY per the user's 2026-06-15 directive: the canonical architecture diagram becomes a single-source fenced Mermaid block in spec.md (matching the existing lifecycle diagram), and the repo README references it instead of embedding a duplicate. No '## ' heading changed, so heading-coverage is unaffected. Verified DRY: the architecture 'flowchart TB' block now appears exactly once (spec.md), zero times in README.

## Resulting Changes

- spec.md
