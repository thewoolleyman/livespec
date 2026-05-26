---
proposal: next-layer-3-discoverability-nudge.md
decision: accept
revised_at: 2026-05-26T08:23:34Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Single sub-proposal in the file accepted as authored. The change adds a Layer 3 discoverability nudge requirement to both /livespec:next (contracts.md §'/livespec:next spec-side thin-transport skill' as a new subsection between '.livespec.jsonc configuration' and 'Cross-side composition exclusion') and the impl-plugin contract bullet for 'next' (contracts.md §'Implementation-plugin contract — the 10-skill surface'), plus a closing sentence to spec.md §'Three-layer orchestration architecture' tying the discoverability nudge to the doctrinal Layer 3 cross-side composition exclusion. The nudge is SKILL.md-prose discipline only; wrappers stay pure thin-transport pass-throughs. UX/discoverability improvement, last in the Wave 1 safety-net sequence. No H2 heading changes (only H3 subsection added), so no tests/heading-coverage.json update required.

## Resulting Changes

- contracts.md
- spec.md
