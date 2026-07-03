---
proposal: github-app-permission-and-credential-set.md
decision: accept
revised_at: 2026-07-03T02:49:03Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Maintainer directive: codify the GitHub App permission set and the tenant credential set learned in the github-app-auth epic (livespec-2ef0, closed 2026-07-03) into non-functional-requirements.md §'Fleet secrets — 1Password Environment as canonical source'. Both proposals are clause-only extensions inside the existing H2 immediately after the **GitHub automation credential.** block (v153) — no heading changes, so no tests/heading-coverage.json co-edit, per the v022 beads-fabro precedent of clause-only extensions. The workflows-grant clause captures the structurally-enforced GitHub rejection discovered as livespec-2ef0.1; the credential-set clause captures the complete env-var set a tenant wrapper must inject and the fail-closed onboarding criterion. Accepted verbatim as proposed.

## Resulting Changes

- non-functional-requirements.md
