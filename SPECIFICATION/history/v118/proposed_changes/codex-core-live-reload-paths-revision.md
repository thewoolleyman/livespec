---
proposal: codex-core-live-reload-paths.md
decision: accept
revised_at: 2026-06-19T07:58:00Z
author_human: E2E Test <e2e-test@example.com>
author_llm: codex-gpt-5
---

## Decision and Rationale

Accept the proposal because it removes the remaining core-spec claim that live reload edits a `.claude-plugin/skills` tree, aligning the contract with the split between core prose/wrappers and the external Claude Driver bindings.

## Resulting Changes

- contracts.md
