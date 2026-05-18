---
proposal: claude-opus-4-7-critique.md
decision: accept
revised_at: 2026-05-18T15:44:28Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

User-directed accept of the proposed change as drafted. Drops the literal-message line from templates/minimal/scenarios.md §"End-to-end prune-history no-op" Then-block. The check_id 'prune-history-no-op' + status 'skipped' assertions remain — those are the load-bearing wire contract; the canonical message text lives only in main SPECIFICATION/constraints.md §"`prune-history` file-shaping mechanics" as the single source of truth, resolving the cross-tree disagreement (the trailing 'or is the only version' clause that the sub-spec scenario had but main constraint did not).

## Resulting Changes

- scenarios.md
