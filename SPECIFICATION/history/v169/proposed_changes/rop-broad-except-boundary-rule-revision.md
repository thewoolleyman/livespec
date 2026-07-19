---
proposal: rop-broad-except-boundary-rule.md
decision: accept
revised_at: 2026-07-19T11:32:43Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Fleet ROP design-authority ruling (2026-07-19). Settles the ambiguity that blocked accepting three merged railway conversions and briefing ten conversion slices: a broad `except Exception` at an I/O seam is NOT permitted even when it lifts onto the Result/IOResult failure track, because a hand-rolled `except Exception` returning Failure/IOFailure is the blanket @safe/@impure_safe form the spec already forbids, written longhand. Accepted after SIX independent adversarial review rounds (blockers found: 5, 4, 2, 2, 0). The final round verified 16/16 replacement targets byte-exact and unique, zero apply-order hazards, zero heading changes across all three target files, six catch-site coherence probes each yielding exactly one disposition, a clean drift sweep across all five spec files, and every cross-repo claim confirmed against shipped code. NO BLOCKERS.

## Resulting Changes

- constraints.md
- contracts.md
- non-functional-requirements.md
