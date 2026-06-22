---
proposal: retire-auto-update-branches.md
decision: accept
revised_at: 2026-06-22T20:44:32Z
author_human: E2E Test <e2e-test@example.com>
author_llm: retire-auto-update-branches
---

## Decision and Rationale

Maintainer-directed family-wide removal of auto-update-branches.yml. The workflow injected merge commits into behind PRs via the update-branch endpoint, violating linear history; strict=false + auto-enable-merge rebase-merge-on-current-tip + post-merge CI is the robust replacement, so the pre-merge branch-update step is unnecessary.

## Resulting Changes

- non-functional-requirements.md
