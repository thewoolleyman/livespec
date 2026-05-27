---
proposal: fix-constraints-bcp14-and-anchor-meta-references.md
decision: accept
revised_at: 2026-05-27T07:48:41Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Accept both findings as authored. Each rewrite preserves the rule's intent while eliminating the self-violating literal token that the rule's own check is supposed to detect. Pre-existing failures on master that the prior recast revise pass surfaced.

## Resulting Changes

- constraints.md
