---
proposal: owned-heading-coverage-todos.md
decision: modify
revised_at: 2026-08-03T02:10:16Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: codex-gpt-5
---

## Decision and Rationale

Accept the ownership model because it turns deferred coverage into tracked work and prevents unowned debt from landing; modify it to add an explicit revise scenario and to distinguish the per-commit ownership check from release-time tracker-liveness validation.

## Modifications

Add a Happy-path revise scenario for work-item creation and make the two check cadences explicit.

## Resulting Changes

- spec.md
- non-functional-requirements.md
- scenarios.md
