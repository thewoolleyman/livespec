---
proposal: catalogue-heading-level-fix.md
decision: accept
revised_at: 2026-05-06T00:15:41Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: Claude Opus 4.7 (1M context)
---

## Decision and Rationale

Accept the proposal as drafted. Single-character typo correction (`##` → `#`) bringing the seed-prompt catalogue rule into alignment with SPECIFICATION/constraints.md line 47. No downstream impact on the seeded spec.md; the rule's intent (top-level intent-derivation) is preserved with corrected level pinning. User confirmed via /bootstrap --ff turn 2026-05-06 after pushing back on the executor's initial halt-and-ask.

## Resulting Changes

- contracts.md
