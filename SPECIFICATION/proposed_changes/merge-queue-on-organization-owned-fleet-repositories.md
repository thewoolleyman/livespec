---
topic: merge-queue-on-organization-owned-fleet-repositories
author: claude-opus-5-5
created_at: 2026-11-13T23:54:43Z
---

## Proposal: Organization-owned fleet repositories gate master through GitHub's merge queue

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Replace the clause in §"CI as a merge gate (branch protection)" that rules the merge queue out for the fleet. Once a fleet repository is owned by a GitHub organization, it MAY require GitHub's merge queue on master. livespec-dev-tooling and livespec-orchestrator-beads-fabro MUST require it. Three conditions apply wherever the queue is required: the merge_group run executes the full gating aggregate, every path to master enters through the queue except the expedited incident policy's recovery bypass, and the build concurrency is at least 2. `strict` stays forbidden.

### Motivation

The maintainer moved the fleet to the organization github.com/livespec-ai (GitHub Team), so that GitHub's merge queue becomes available. The ruling is in plan stale-base-merge-options, epic livespec-dev-tooling-xowhol, scope event 2026-11-12T19:34:25Z ("OK, we are going to go with the org move"). The maintainer approved the plan's Definition of Done as written in epic comment 27 on 2026-11-13. That Definition of Done requires the queue on dev-tooling and the orchestrator, and requires that two PRs which break CI only together cannot both land. The clause being replaced rests on "GitHub merge queues are organization-only". That premise no longer holds once the fleet is organization-owned. The post-merge catch it accepts has measurably failed: on 2026-11-13, livespec-dev-tooling#4442 and livespec-dev-tooling#4449 merged 87 s apart, each green on its own base, and turned master red (incident livespec-dev-tooling-3hilpy). Only the full aggregate caught it. Note 005 §5 call 3 records why the queue stops this only under the full-suite and every-path conditions.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md §"CI as a merge gate (branch protection)", make three edits.

1. In the `strict` rationale paragraph, replace the sentence that begins "The one case it would have caught" and the sentence that begins "The fleet deliberately does NOT substitute a merge queue" with:

> The one case it would have caught is a PR that was CI-green against an older `master` and conflicts SEMANTICALLY (not textually) with the newer tip. Where the repository requires a merge queue, that case is caught by the queue's composed-tree run, as described below. Otherwise it is caught by CI on `master` after the merge.
>
> **Merge queue on organization-owned repositories.** A fleet repository owned by a GitHub organization MAY require GitHub's merge queue on `master`. livespec-dev-tooling and livespec-orchestrator-beads-fabro MUST require it while they are organization-owned. Where the queue is required, all of the following hold:
> - (a) The `merge_group` run of `ci.yml` MUST execute the same gating job set as a `push` to `master`, including the full per-file coverage aggregate, so that each queued batch tests the composed tree.
> - (b) Every path to `master` MUST enter through the queue, including auto-merge, factory merges and human merges. The one exception is the recovery bypass actor of `contracts.md` §"Expedited incident response policy", whose push still runs the full aggregate on `master`.
> - (c) The queue's build concurrency MUST be at least 2.
> - (d) The required-check set is still exactly the all-green gate job, and `strict` stays off, because the queue is what tests the composed tree.
>
> A repository owned by a personal account cannot use the merge queue, and keeps the post-merge catch. The fleet still does NOT adopt a hand-rolled serialized auto-rebase driver: it would trade robust per-PR `gh pr merge --auto` for a fragile central loop that can orphan, mis-order or wedge PRs.

2. In the paragraph that begins "Outside the explicit incident-only policy above", replace "This rule introduces no merge queue, no `strict`, no serialized merge train, and no additional CI on the happy path." with:

> This rule introduces no `strict`, no serialized merge train, and no additional CI on the happy path. The merge queue permitted above for organization-owned repositories is the only queue, and it adds one full run per queued batch.

3. Add a scenario at the end of the section:

```gherkin
### Scenario: A merge queue ejects the second of two pull requests that break CI only together

Given an organization-owned fleet repository requires the merge queue on master

And its merge_group run executes the same gating job set as a push to master

And pull request A and pull request B each pass the gate on their own bases

And the tree composed of A and B fails a gating check

When both are armed for auto-merge

Then the queued batch containing A and B fails its merge_group run

And the queue removes B from the queue without merging it

And A lands, and master's head commit passes the full gating aggregate
```

The revise commit adds a `tests/heading-coverage.json` row for the new scenario, as a spec-first TODO at the integration tier or above. Its `work_item` is the plan's merge-queue cutover child, livespec-dev-tooling-o6eytb, whose semantic-conflict drill exercises the scenario.
