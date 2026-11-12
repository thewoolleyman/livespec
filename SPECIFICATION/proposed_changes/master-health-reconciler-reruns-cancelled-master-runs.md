---
topic: master-health-reconciler-reruns-cancelled-master-runs
author: claude-opus-5-5:stale-base-merge-options
created_at: 2026-11-12T18:39:49Z
---

## Proposal: The reconciler resolves an unverdicted master commit before naming a culprit

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/scenarios.md

### Summary

Amend §"CI as a merge gate (branch protection)" step (b) of §"Red master heals itself: revert by default": when a `master` commit in the suspect range has no completed gate verdict because its run was cancelled (for example by a master-push concurrency group that keeps only the newest pending run), the master-health reconciler MUST re-run that commit's gating run and wait for its verdict before naming a culprit, and MUST NOT name a culprit from an unverdicted commit. Add one scenario to the existing `## A red master heals by revert by default, or through a progressing fix-forward` block.

### Motivation

On 2026-11-09 the maintainer ruled (livespec-dev-tooling `.ai/coordinator-duties.md` §10 "Superseded master runs", answer "OK B'") that livespec-dev-tooling and livespec-orchestrator-beads-fabro keep only the in-progress and newest pending master push run, and that neither repository adopts the master-health reconciler until "option A" lands: the reconciler re-runs a cancelled master run in the suspect range before naming a culprit. Step (b) today names "the earliest red `master` commit whose parent was green", which is undefined when the culprit's own run was cancelled. That happened on 2026-11-12: livespec-dev-tooling#4339 (b9838b28c) merged on a stale base at 16:09Z, its master run and the next one were cancelled by the B' group, and the first red verdict landed on a later commit (6201dcdb2) at 16:52Z. Without this rule a reconciler would revert the wrong merge or none, so the two busiest repositories (65% of fleet merges over 2026-10-15..11-12) stay without self-healing. The 2026-11-09 ruling requires this as a core propose-change plus a livespec-dev-tooling realization.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md §"CI as a merge gate (branch protection)", paragraph **Red master heals itself: revert by default.**, second paragraph ("On a red `master` the reconciler MUST: ..."), replace clause (b):

> (b) identify the culprit as the earliest red `master` commit whose parent was green;

with:

> (b) identify the culprit as the earliest red `master` commit whose parent was green, where every `master` commit between the last green commit and the first red one carries a completed gate verdict: a commit in that range whose gating run was cancelled or never completed — for example one dropped by a master-push concurrency group that keeps only the newest pending run — MUST first have its gating run re-run, and the reconciler MUST wait for that verdict before naming any culprit; the reconciler MUST NOT name a culprit from, or past, an unverdicted commit, and each such re-run is one step of the stateless reconcile;

In SPECIFICATION/scenarios.md, inside the existing ```gherkin block under `## A red master heals by revert by default, or through a progressing fix-forward` (no new `## ` heading, so tests/heading-coverage.json needs no co-edit), append after the scenario "A revert that would clobber later work is refused":

```gherkin
Scenario: A cancelled master run is re-run before a culprit is named
  Given a red `master` whose last green commit is followed by commits whose gating runs were cancelled before a verdict
  When the master-health reconciler runs
  Then it re-runs the gating run of the earliest unverdicted commit in that range
  And it names no culprit and opens no revert until every commit up to the first red one has a completed verdict
  And the culprit it then names is the earliest red commit whose parent is green
```
