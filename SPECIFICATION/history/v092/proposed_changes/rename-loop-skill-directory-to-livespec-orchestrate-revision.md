---
proposal: rename-loop-skill-directory-to-livespec-orchestrate.md
decision: accept
revised_at: 2026-05-27T15:13:25Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Accept as authored. Pure path substitution to disambiguate from the harness's built-in `/loop` skill. The Layer 3 architectural role, contract, and skill body are unchanged — only the directory path moves to give the slash command a unique, autocomplete-friendly name (`/livespec-orchestrate`).

## Resulting Changes

- spec.md
- non-functional-requirements.md
- contracts.md
