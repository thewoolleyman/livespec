---
proposal: next-ranked-candidates-list-and-pagination.md
decision: accept
revised_at: 2026-05-23T08:33:43Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Both findings (spec-side ranked-candidates list + pagination output shape with --limit/--offset, plus the impl-side symmetric mirror in the impl-plugin :next row) cleanly extend the existing /livespec:next contract and the impl-plugin contract :next row. New CLI flags (--limit positive int default 5, --offset non-negative int default 0, exit-2 on bad values), new output schema with top-level candidates[] + pagination, ranker semantics requiring exhaustive enumeration, and impl-side symmetric shape are all codified. The breaking nature of the output schema change is acknowledged; this is a clean break (not backwards-compat widening) per the propose-change explicit framing. resulting_files carries the cumulative contracts.md content for both next-UX accepts in this revise pass.

## Resulting Changes

- contracts.md
