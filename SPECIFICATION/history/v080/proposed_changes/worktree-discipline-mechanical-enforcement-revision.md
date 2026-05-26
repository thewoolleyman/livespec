---
proposal: worktree-discipline-mechanical-enforcement.md
decision: accept
revised_at: 2026-05-26T07:25:50Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Accept all four sub-proposals as authored. The PC introduces a complete three-mechanism enforcement loop for the v079 worktree-only discipline: (1) NFR rule mandating core.bare=true on every primary checkout, (2) NFR rule documenting the idempotent bootstrap-step contract, (3) doctor invariant verifying the flag at check time, (4) doctor invariant catching the secondary-worktree-on-master bypass. Memo mm-ndqume's observation (git worktree add/remove occasionally flips core.bare=true on the main checkout) is consistent with — and reinforces — the bare-flag mandate; the desired end state matches the observed flip. The bootstrap-step idempotence (sub-proposal 2 clause 3) covers the safe re-application case. Impl follow-ups are filed separately as work-items per the PC's own §'Impl-side follow-ups (filed as work-items, not spec changes)' section.

## Resulting Changes

- non-functional-requirements.md
- contracts.md
