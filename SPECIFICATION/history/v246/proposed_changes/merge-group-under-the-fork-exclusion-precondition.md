---
topic: merge-group-under-the-fork-exclusion-precondition
author: claude-opus-5-5
created_at: 2026-11-13T23:54:18Z
---

## Proposal: merge_group runs may reach guarded self-hosted capacity under the Fork-exclusion precondition

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Amend §"Self-hosted CI runner host requirements" so that a merge_group run may reach self-hosted capacity that carries merge-gating CI. Two conditions apply: the repository meets the Fork-exclusion precondition, and a guard job first proves through the API that every pull request in the merge group is a same-repository branch by an allowlisted author. Any other merge_group run, and any guard failure, runs on hosted capacity.

### Motivation

The maintainer ruled call 3 of plan stale-base-merge-options (note 005 §5; epic livespec-dev-tooling-xowhol, comment 27, 2026-11-13) as option A: queue CI runs on guarded self-hosted runners. The maintainer accepts the fork-PR secrets exposure while the fleet takes no outside contributions. Today the **Event routing** clause admits only same-repository pull-request events and protected-branch pushes. A merge_group run differs from both: it executes the queued PRs' code in the base repository's trusted context, with secrets, and the fork-PR approval gate does not cover it. So a fork PR that a write-access user enqueues would run fork code on fleet hosts (note 004, check 2). The guard closes that path without reading author vigilance as enforcement. The ruling also requires this to be ratified before the dev-tooling self_hosted_routing change is coded.

### Proposed Changes

Make three edits to SPECIFICATION/non-functional-requirements.md: edits 1 and 2 in §"Self-hosted CI runner host requirements", and edit 3 under `## Scenarios`.

1. Replace the **Event routing** paragraph with:

> **Event routing.** Self-hosted capacity carrying merge-gating CI MUST be reachable only from the following events:
> - same-repository pull-request events;
> - pushes to a protected branch;
> - guarded `merge_group` events, as defined below.
>
> Trigger classes a non-collaborator can reach, and privileged trigger classes that check out or interpret externally-supplied content, MUST remain on hosted capacity. The two tiers carved out under **Scope** above are not bound by this clause.
>
> A `merge_group` event is GUARDED when all of the following hold:
> - (a) the repository meets the **Fork-exclusion precondition**;
> - (b) the workflow's first job runs on hosted capacity with a read-only token, and resolves every pull request in the merge group through the forge API;
> - (c) every gating job's self-hosted route depends on that first job's output, and the output is true only when every one of those pull requests has a head repository equal to the base repository and an author on the repository's committed merge-queue author allowlist.
>
> Every other `merge_group` run MUST route its gating jobs to hosted capacity: a fork head, an author off the allowlist, or a guard that fails or cannot resolve a pull request. That fallback MUST NOT skip or shrink any gating job. In particular, a guard job that fails or is cancelled MUST NOT cause a gating job that depends on it to be skipped: either each such gating job still runs, routed to hosted capacity, or the all-green gate job of §"CI as a merge gate (branch protection)" fails when a gating job of a `merge_group` run was skipped. A batch whose gating jobs did not run is never reported green.

2. Append to the **Fork-exclusion precondition** paragraph:

> The fork-pull-request approval setting does not cover a `merge_group` run, because the queue executes enqueued code in the base repository's context. Under this precondition, self-hosted `merge_group` capacity is therefore admitted only through the guard in **Event routing**.

3. Under `## Scenarios`, after the scenario "A conforming self-hosted host carries a fleet gate without host-wide privilege", add these two scenarios in the section's plain-prose convention, one step per paragraph:

### Scenario: A merge group holding a fork pull request runs its gate on hosted capacity

Given a fleet repository meets the Fork-exclusion precondition and routes merge-gating jobs to self-hosted capacity

And its merge queue holds a batch whose pull requests include one whose head repository is a fork

When the merge_group run starts

Then the guard job resolves that pull request's head repository and reports the batch as unguarded

And every gating job of that run executes on GitHub-hosted capacity

And no gating job of that run is skipped

### Scenario: A failed merge-group guard never yields a green batch

Given a fleet repository routes guarded merge_group runs to self-hosted capacity

And the guard job of a merge_group run fails before reporting its output

When the run's gating jobs are scheduled

Then each gating job either runs on GitHub-hosted capacity or the all-green gate job fails

And the merge queue does not merge that batch on a green verdict from gating jobs that did not run
