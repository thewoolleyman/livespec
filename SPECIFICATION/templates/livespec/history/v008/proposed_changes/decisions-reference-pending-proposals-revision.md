---
proposal: decisions-reference-pending-proposals.md
decision: accept
revised_at: 2026-05-07T22:26:39Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Aligns the livespec sub-spec's prompt-QA harness with the v052 main-spec relaxation that permits selective per-proposal revise. The replacement keeps the meaningful invariant (every decision topic MUST reference an actually-pending proposal — catches typos and stale refs in LLM-emitted JSON) and drops the now-contradictory subset-coverage requirement. Narrow, single-bullet replacement; rest of catalogue preserved verbatim. Three downstream code follow-ups noted in the proposal land outside this revise pass.

## Resulting Changes

- contracts.md
