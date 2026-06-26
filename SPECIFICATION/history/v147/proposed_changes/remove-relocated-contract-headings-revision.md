---
proposal: remove-relocated-contract-headings.md
decision: accept
revised_at: 2026-06-26T04:09:47Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accept the besm.6 core-side removal: both contract sections have been relocated entirely into their owning sibling repos (B2 orchestrator PR #175, B4 driver-claude PR #47, both merged). Removes the two sections + their heading-coverage TODO entries and rewords the two now-dangling same-file citations to prose. Takes core's release-gate check-no-todo-registry to zero TODOs.

## Resulting Changes

- contracts.md
- ../tests/heading-coverage.json
