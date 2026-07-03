---
topic: no-shadow-ledger-plan-thread-convention
author: claude-fable-5
created_at: 2026-07-03T08:01:19Z
---

## Proposal: Plan-thread successor for the No-shadow-ledger convention pointer

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

In §"Planning Lane guidance" → the **No shadow ledger (the load-bearing rule).** paragraph, replace the final convention-pointer clause "and a per-repo `prompts/AGENTS.md` (or equivalent) defines the convention locally" with the plan-thread successor convention: handoffs live at the reserved `plan/<topic>/handoff.md` path, and the per-repo convention is defined by the Planning Lane realization rather than by a standalone `prompts/` file. Every other rule in the sentence (checklist items are session-local steps or ledger-id pointers; handoff refreshed at context budget; closing summary names the exact next-session command) and the closing openbrain-provenance sentence stay intact. No heading changes, so no tests/heading-coverage.json co-edit.

### Motivation

cleanup-research-and-prompt-cruft epic (fleet anchor livespec-ztepy5; livespec child livespec-kg6paq), confirmed decision D2: retire the root prompts/ handoff convention fleet-wide. The paragraph's convention pointer still names a per-repo `prompts/AGENTS.md` file — a convention this epic retires (livespec's prompts/ directory empties in the same changeset); the successor convention is the Planning Lane's `plan/<topic>/handoff.md`, already defined one paragraph earlier in §"The planning thread" and realized by the reference orchestrator's plan front-end. Evidence: plan/cleanup-research-and-prompt-cruft/research/02-dispositions-livespec.md.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md §"Planning Lane guidance", the **No shadow ledger (the load-bearing rule).** paragraph MUST replace the clause "and a per-repo `prompts/AGENTS.md` (or equivalent) defines the convention locally" with "and handoffs live at the reserved `plan/<topic>/handoff.md` path — the per-repo convention is defined by the Planning Lane realization, not by a standalone `prompts/` file". The rest of the sentence's rules MUST be kept intact, and the trailing sentence ("This re-adopts the openbrain planning discipline `livespec` had copied the shape of but dropped.") MUST be preserved. No heading is added, changed, or removed.
