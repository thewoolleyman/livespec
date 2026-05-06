---
proposal: python-style-scope.md
decision: accept
revised_at: 2026-05-06T04:41:47Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: Claude Opus 4.7 (1M context)
---

## Decision and Rationale

Accept as proposed. First cycle of Plan Phase 8 item 2 per-section migration. Migrates source-doc §"Scope" into `SPECIFICATION/constraints.md` as a new `## Constraint scope` section. Restructured for BCP 14 normative language. Intro paragraph updated from the Phase-6 deferral note to a Phase-8-in-progress note. Deviation from `deferred-items.md` §`python-style-doc-into-constraints`'s "at seed time" guidance is intentional per Phase 6's documented audit-granularity rationale: per-section split keeps each section's revision human-reviewable in isolation; later need to revisit a particular style rule does not have to contend with a single 92KB historical revision. Subsequent cycles will cross-reference this first cycle's revise body for the deviation rationale.

## Resulting Changes

- constraints.md
