---
proposal: selective-revise.md
decision: accept
revised_at: 2026-05-07T19:24:02Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

User-confirmed accept of the proposal as drafted. The three edits to SPECIFICATION/spec.md line 49 land coherently as a unit: (1) the new start-of-revise stale-pending-proposal narration responsibility is added to the skill-prose enumeration; (2) a new wrapper precondition forbidding empty decisions[] (UsageError exit 2) is inserted as clause (b) with downstream re-lettering; (3) the former clause (g) is relaxed at its new (h) position to permit selective subset processing. BCP14 keywords are preserved throughout. The two follow-up changes (sub-spec catalogue walks_every_pending_proposal relaxation; schema minItems:1) are intentionally left to separate proposed-change cycles per the proposal's motivation.

## Resulting Changes

- spec.md
