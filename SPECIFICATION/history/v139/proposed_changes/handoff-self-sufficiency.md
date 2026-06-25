---
topic: handoff-self-sufficiency
author: claude-opus-4-8
created_at: 2026-06-25T10:13:47Z
---

## Proposal: Handoff self-sufficiency in the Planning Lane guidance

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add the handoff self-sufficiency criterion (with its one-path and no-dangling-reference corollaries) to the NON-normative Planning Lane guidance block, completing the no-shadow-ledger handoff discipline. Core records the pattern; the enforcing mechanisms (a cold-open readiness test, a fail-closed dangling-reference check) are named as realization concerns belonging to the reference orchestrator's plan front-end, not core.

### Motivation

livespec-zs22.3: prevent recurrence of an incomplete handoff (a load-bearing artifact left only in chat). The pattern half of zs22.3 lands here in core NFR; the realization half lands in the orchestrator plan skill.

### Proposed Changes

Under the Planning Lane guidance section, insert a new '**Handoff self-sufficiency.**' paragraph after the '**No shadow ledger**' paragraph and before '**The two seams.**'. A handoff is not ready until a fresh session opening ONLY the handoff can execute its next action without re-deriving anything: every depended-on artifact is committed and reachable through the handoff's read-first chain, never left only in chat. Corollary (1) one path: the next-session command names exactly ONE path, the handoff; needing to also list other files is the smell to fix the handoff. Corollary (2) no dangling reference: every cited artifact (read-first chain and next action) exists and is committed. The enforcing mechanisms (cold-open readiness test; fail-closed dangling-reference check) are realization concerns, mirroring how the archive backstops are described as realized separately, not by core.
