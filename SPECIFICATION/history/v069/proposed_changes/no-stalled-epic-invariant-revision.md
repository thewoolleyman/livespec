---
proposal: no-stalled-epic-invariant.md
decision: accept
revised_at: 2026-05-20T08:59:48Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

The proposal is well-scoped: it adds one structural invariant (no-stalled-epic) to doctor's cross-boundary catalogue, matches the existing no-X naming + fail-classification conventions, and handles the vacuous-truth case (empty depends_on) and the unresolvable-blocker delegation (no-orphan-blocker) explicitly. The motivation is concrete (li-6t5 drift discovered in the live dogfood store) and the load-bearing distinction between structural invariants and productivity heuristics from spec.md §Terminology supports the fail-classification choice. Accepting verbatim — no modifications needed.

## Resulting Changes

- contracts.md
- constraints.md
- ../tests/heading-coverage.json
