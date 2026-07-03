---
proposal: retire-workflow-processes-split-mandate.md
decision: accept
revised_at: 2026-07-03T08:02:18Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Accepted as proposed: the H3 §"research/workflow-processes/ tool-agnostic vs implementation-specific split" is removed in full. The mandate is obsolete — the memo paradigm it froze into the mandated artifact was retired at v123, the v151 accepted tool-agnostic-workflow-diagram proposal re-authored the stale SVG into spec.md §"Tool-agnostic workflow — spec / implementation lifecycle" (the living tool-agnostic home), and tool-agnostic-workflow.md carries 76 stale `memo` mentions. No still-true residue needs inlining; the research/workflow-processes/ tree archives under archive/research/ in the same changeset per the cleanup-research-and-prompt-cruft epic (livespec-ztepy5, Phase 2 CONFIRMED verdict; livespec child livespec-kg6paq). H3-only removal — the H2 set is unchanged, so tests/heading-coverage.json is not co-edited.

## Resulting Changes

- non-functional-requirements.md
