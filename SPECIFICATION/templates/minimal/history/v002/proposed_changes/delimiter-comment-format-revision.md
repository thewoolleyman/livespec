---
proposal: delimiter-comment-format.md
decision: accept
revised_at: 2026-05-06T00:55:44Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: Claude Opus 4.7 (1M context)
---

## Decision and Rationale

Accept as proposed. Shared-dependency cycle per Plan §3531-3550. Pins the format with a concrete syntax + regex; satisfies all 4 original invariants + adds 'on own line' as 5th invariant for parser cleanliness. No other minimal-template files are touched in this revise; the per-prompt regeneration cycles ((d).2-(d).5) follow.

## Resulting Changes

- contracts.md
