---
proposal: cross-tree-revise-narration.md
decision: accept
revised_at: 2026-05-18T09:51:03Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

User-directed accept of the single-bullet widening: the start-of-revise stale-pending-proposal narration is rewritten as a two-clause rule covering (a) the active <spec-target>/ and (b) every OTHER spec tree in the project, with per-tree lines omitted when a tree has zero in-flight proposals. The load-bearing non-gating / non-blocking guarantees on the narration are preserved verbatim. Motivated by the 2026-05-18 session where invoking /livespec:revise against the main spec silently missed pending sub-spec work, leading to a duplicate-critique error during the post-step LLM-driven phase. The companion SKILL.md Step 3 narration prose is updated in the same git commit to match the new contract.

## Resulting Changes

- spec.md
