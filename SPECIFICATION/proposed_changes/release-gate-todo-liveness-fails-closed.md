---
topic: release-gate-todo-liveness-fails-closed
author: claude-opus-5-5 (spec-implementation-lockstep seat, plan bd-ib-ax3rds)
created_at: 2026-11-12T17:10:00Z
---

## Proposal: The release mode of check-no-todo-registry reads owner liveness from a published snapshot, and fails closed when that snapshot cannot answer

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The release mode of `check-no-todo-registry` rejects a closed or nonexistent `work_item` owner only "where the configured tracker makes liveness mechanically checkable". Where the tracker does not answer, the entry PASSES with a `liveness_unverified` diagnostic. No release runner in the fleet can reach its tracker, so the release gate is a green that checks nothing. Failing closed on the live tracker alone would fail every release on every TODO row instead. This proposal therefore names WHERE the answer comes from: a liveness snapshot that a host with tracker access publishes on a schedule, at a location the repository declares. The release mode fails closed, naming the rows, when that snapshot is missing, older than its declared bound, or silent about a row's owner.

### Motivation

Carried from livespec-orchestrator-beads-fabro work item bd-ib-fhbonx (plan bd-ib-ax3rds), routed here by legacy-coordinator-agent (session 959b2f8b) on 2026-11-12. That item is closed there as transferred to this proposal and to an implementation item in the livespec-dev-tooling tenant, because the clause is this repository's and the check is livespec-dev-tooling's.

Measured on 2026-11-11:
- `livespec_dev_tooling.checks.no_todo_registry` resolves liveness through `checks/_work_item_liveness`. When the store does not answer (no `bd`, no credential, or a hosted runner that cannot reach the loopback ledger), the entry passes with `liveness_unverified`.
- livespec-overseer arms the release mode (`release-readiness.yml:53`, `release-tag.yml:75`), yet released v5.54.1 at 19:19Z carrying 193 closed-owner TODO rows.
- livespec arms it too (`ci.yml:827`, `release-readiness.yml:37`, `release-tag.yml:48`).

Where the answer comes from (grade fix, legacy-coordinator-agent): measured on 2026-11-12, every job that runs the release mode in both arming repositories runs on GitHub-hosted `ubuntu-latest`. That is livespec `release-tag.yml:40` and `release-readiness.yml:35`, and livespec-overseer `release-tag.yml:72` and `release-readiness.yml:51`. Every family tenant serves only on the control node's loopback port, and the fleet's tailnet posture rules out a CI tailnet join. So NO arming repository's release job reaches its tracker today, and failing closed on the live tracker alone would fail every release on every row, debt or no debt. Of the routes the grade offered, this proposal takes the PUBLISHED SNAPSHOT: it needs no new credential and no network route. A host-side pre-tag step would tie every release to one host's availability.
- Recommended mechanism, not normative: a host-side timer that reads the tenant writes the snapshot to a dedicated ref of the repository itself. The host already pushes there, and the release job reads it with its default token.

FLEET SCOPE: the repositories that arm the release mode are livespec (`ci.yml:827`, `release-readiness.yml:37`, `release-tag.yml:48`) and livespec-overseer (`release-readiness.yml:53`, `release-tag.yml:75`). The change applies to each, and each must declare its snapshot location and bound and run the publishing step before its release mode is armed under this text. Other family repositories run only the per-commit tier, which this proposal does not change.

The current carve-out is ratified text, so failing closed is a ratification change, not a conformance fix. livespec-dev-tooling's own NFR already says "Every TODO MUST name a work_item that the configured tracker resolves as live"; this proposal aligns core with it.

Sequencing, not part of the normative text: implementation MUST land only after the fleet heading-coverage TODO-owner sweep has cleared each arming repository's closed-owner rows. Arming it earlier reddens livespec's and livespec-overseer's releases on debt they have not yet repaid. The alternative to this proposal is a recorded decision that release runners must reach their tenant. This proposal prefers failing closed, because a gate that cannot see must not report that it looked.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md`, the "Release-gate targets" bullet, change

> the release mode of `check-no-todo-registry` (rejecting an unowned TODO and, where the configured tracker makes liveness mechanically checkable, one whose named `work_item` is closed or nonexistent). An owned live TODO does not block an unrelated release.

to

> the release mode of `check-no-todo-registry` (rejecting an unowned TODO, and one whose named `work_item` is closed or nonexistent). The release mode MUST take each owner's liveness from a LIVENESS SNAPSHOT, a record that a host with access to the configured tracker publishes on a schedule, at a location the repository declares together with a maximum snapshot age. The snapshot MUST name the instant it was taken and, for each `work_item` named by a TODO row at the snapshot's source commit, whether the tracker reported it live, closed or nonexistent. The release mode MUST fail, naming every TODO row it could not verify, when the declared snapshot is missing or unreadable, when it is older than the declared maximum age, or when it does not report a row's owner. It MUST NOT pass such a row with a diagnostic. Where the snapshot reports an owner, an owned live TODO passes and does not block an unrelated release, and a closed or nonexistent owner fails. A repository whose release workflow arms the release mode MUST declare the snapshot location and bound, and run the publishing step, before it arms the mode.
