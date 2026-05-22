---
proposal: next-prune-history-config-and-ordering.md
decision: accept
revised_at: 2026-05-22T03:27:44Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Both findings (configurable .livespec.jsonc next.prune_history_threshold + strict-last ordering invariant for prune-history) land cleanly in contracts.md §"/livespec:next spec-side thin-transport skill" without affecting other contract surfaces. The threshold semantics (positive integer, default 20, exit-3 on bad value) and the ordering clause (prune-history MUST NOT be primary recommendation when ANY other action is ripe) are codified as sub-sections under the existing /livespec:next section.

## Resulting Changes

- contracts.md
