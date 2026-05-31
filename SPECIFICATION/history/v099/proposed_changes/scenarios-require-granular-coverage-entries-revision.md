---
proposal: scenarios-require-granular-coverage-entries.md
decision: accept
revised_at: 2026-05-31T20:51:05Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-8-1m
---

## Decision and Rationale

Pre-approved spec amendment: scenarios are tracked granularly — every `##` heading in scenarios.md (including `Scenario:`-prefixed ones) requires its own heading-coverage registry entry, with a permitted many-to-one mapping to integration-tier test node ids. This gives the existing integration-tier-or-above sub-rule entries to bite on. Edits only body text inside the existing `## Heading taxonomy` H2; no `##` heading is added/changed/removed, so no tests/heading-coverage.json co-edit is required.

## Resulting Changes

- constraints.md
