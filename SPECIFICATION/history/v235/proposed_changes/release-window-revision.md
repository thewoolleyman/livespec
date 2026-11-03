---
proposal: release-window.md
decision: modify
revised_at: 2026-11-03T16:59:16Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5:ci-runtime-and-cost
---

## Decision and Rationale

Modified under the delegated decision mode. legacy-coordinator-agent decided MODIFY under R301 (2026-11-03), following the maintainer's direct order of livespec-dev-tooling-aplxhg (2026-11-03 15:00:49Z, 'get this done too'). As proposed, the rule was a fleet-wide MUST that release-please never run its pull-request pass on push. livespec, livespec-overseer, livespec-driver-claude, livespec-driver-codex and livespec-runtime all run release-please on push today, so that rule would have made five fleet repositories non-conformant the moment it landed, before they adopted: the arming-before-adoption order the fleet forbids. The window is therefore ADOPTABLE. A repository either runs release-please on every push, or adopts a release window. An adopting repository MUST open or update its release PR only from schedule plus workflow_dispatch (reference cadence 4 h), MUST carry every merged commit, and on push MUST only tag a just-merged release PR. A repository SHOULD adopt the window when its release cadence drives material sibling fan-out. livespec-dev-tooling and livespec-orchestrator-beads-fabro adopt it now under aplxhg. Measured: release mechanics were 34% of fleet k3s CI time over 7 days (livespec-dev-tooling plan ci-runtime-and-cost, research 002). Independent ratification review (sonnet, read-only): NO BLOCKERS.

## Modifications

The fleet-wide 'MUST NOT run release-please's pull-request pass on push' becomes an adoptable window: 'A repository either runs release-please on every push to master, or adopts a release WINDOW', with the MUST clauses binding only an adopting repository, plus a SHOULD-adopt rule when release cadence drives material sibling fan-out. The scenario's Given names 'a repository that adopts a release window'. The rest of the proposal is unchanged.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-03T16:58:00Z
verdict: NO BLOCKERS
proposal_stem: release-window
content_digest: c0c7183ba4052b9acf18fd9dd64ff424ee7406c01d3be38b744488fde7be6267
