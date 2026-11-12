---
topic: release-gate-todo-liveness-fails-closed
author: claude-opus-5-5 (spec-implementation-lockstep seat, plan bd-ib-ax3rds)
created_at: 2026-11-12T17:10:00Z
---

## Proposal: The release mode of check-no-todo-registry fails, rather than passes, a TODO whose owner's liveness it cannot verify

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The release mode of `check-no-todo-registry` rejects a closed or nonexistent `work_item` owner only "where the configured tracker makes liveness mechanically checkable". Where the tracker does not answer, the entry PASSES with a `liveness_unverified` diagnostic. A release runner that cannot reach its tenant therefore turns the release gate into a green that checks nothing. This proposal makes the release mode fail on an unverifiable owner, naming every such row, in a repository whose release workflow arms the mode. Where the tracker answers, the verdict is unchanged.

### Motivation

Carried from livespec-orchestrator-beads-fabro work item bd-ib-fhbonx (plan bd-ib-ax3rds), routed here by legacy-coordinator-agent (session 959b2f8b) on 2026-11-12. That item is closed there as transferred to this proposal and to an implementation item in the livespec-dev-tooling tenant, because the clause is this repository's and the check is livespec-dev-tooling's.

Measured on 2026-11-11:
- `livespec_dev_tooling.checks.no_todo_registry` resolves liveness through `checks/_work_item_liveness`. When the store does not answer (no `bd`, no credential, or a hosted runner that cannot reach the loopback ledger), the entry passes with `liveness_unverified`.
- livespec-overseer arms the release mode (`release-readiness.yml:53`, `release-tag.yml:75`), yet released v5.54.1 at 19:19Z carrying 193 closed-owner TODO rows.
- livespec arms it too (`ci.yml:827`, `release-readiness.yml:37`, `release-tag.yml:48`).

The current carve-out is ratified text, so failing closed is a ratification change, not a conformance fix. livespec-dev-tooling's own NFR already says "Every TODO MUST name a work_item that the configured tracker resolves as live"; this proposal aligns core with it.

Sequencing, not part of the normative text: implementation MUST land only after the fleet heading-coverage TODO-owner sweep has cleared each arming repository's closed-owner rows. Arming it earlier reddens livespec's and livespec-overseer's releases on debt they have not yet repaid. The alternative to this proposal is a recorded decision that release runners must reach their tenant. This proposal prefers failing closed, because a gate that cannot see must not report that it looked.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md`, the "Release-gate targets" bullet, change

> the release mode of `check-no-todo-registry` (rejecting an unowned TODO and, where the configured tracker makes liveness mechanically checkable, one whose named `work_item` is closed or nonexistent). An owned live TODO does not block an unrelated release.

to

> the release mode of `check-no-todo-registry` (rejecting an unowned TODO, and one whose named `work_item` is closed or nonexistent). Where the release mode runs but the configured tracker does not answer for an owner, so the owner's liveness cannot be verified, the release mode MUST fail and MUST name every TODO row whose owner it could not verify; it MUST NOT pass such a row with a diagnostic. Where the tracker answers, an owned live TODO passes and does not block an unrelated release, and a closed or nonexistent owner fails.
