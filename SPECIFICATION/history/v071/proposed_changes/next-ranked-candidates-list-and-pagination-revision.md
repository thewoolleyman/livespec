---
proposal: next-ranked-candidates-list-and-pagination.md
decision: accept
revised_at: 2026-05-22T03:27:44Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Both findings (spec-side and impl-side ranked-list + --limit/--offset pagination) land cleanly. Spec-side schema lands under §"/livespec:next spec-side thin-transport skill" → Output schema. Impl-side schema lands in the §"Implementation-plugin contract — the 9-skill surface" `next` skill row, requiring impl-side candidates to carry the additional work_item_ref field while keeping the cross-plugin contract agnostic to per-implementation field additions. The urgency enum stays [high, medium, low] in both shapes per the user's option-A decision on the cross-repo blocker disposition.

## Resulting Changes

- contracts.md
