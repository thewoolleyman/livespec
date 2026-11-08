---
topic: every-self-hosted-gating-job-carries-a-measured-timeout-minutes
author: claude-opus-5-5:ci-runtime-and-cost
created_at: 2026-11-08T03:32:20Z
---

## Proposal: A self-hosted gating job carries a measured time limit

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/scenarios.md

### Summary

Require every merge-gating CI job of a fleet repository that resolves to self-hosted capacity to declare a job-level time limit, derived from that job's own 7-day maximum run time as the smallest of 30/45/60/90/120/180/240/360 minutes that is at least 1.25 times that maximum. A job with no measured run records the absence instead of a guessed limit. A scenario states the observable outcomes: a hung job is cancelled at its limit and releases its runner, and a slowed but healthy run still finishes.

### Motivation

Measured 2026-11-08 across the ten fleet repositories: no self-hosted gating job in any of them declared timeout-minutes, so a hung test held a self-hosted runner and a k3s churn slot for GitHub Actions' 360-minute default. livespec-dev-tooling-u6jztk (livespec-dev-tooling#3757) added measured limits to livespec-dev-tooling, and a same-day Rule G sweep filed one item per other member: bd-ib-px5nxf, livespec-d7lb5v, overseer-ye2nhq, livespec-runtime-frdkkk, livespec-console-beads-fabro-zwdtp3, bd-gj-sycugx, livespec-driver-claude-plkqti, livespec-driver-codex-uyc2tf and livespec-driver-pi-47vt3p. Every one received the governing-heading verdict 'unstated', because no ratified clause anywhere states CI job time limits, and livespec-d7lb5v was refused at admission for that reason (legacy-coordinator-agent, 2026-11-08). FLEET SCOPE: the clause binds every fleet member through core's non-functional requirements, the same way §"Self-hosted CI runner host requirements" already binds them, so no member needs its own copy. The derivation rule is the one applied in all ten repositories, measured over 7 days of runs: e.g. livespec-dev-tooling check-per-file-coverage max 141.1 min -> 180, and the orchestrator ci-root-uid check-per-file-coverage max 107.1 min -> 180.

### Proposed Changes

Add one clause to `non-functional-requirements.md` §"Self-hosted CI runner host requirements", placed directly after the paragraph that begins "**Availability MUST NOT become a merge dependency.**":

> **A self-hosted gating job MUST carry a measured time limit.** Every job of a fleet repository's merge-gating CI whose runner resolves, directly or through a repository variable, to self-hosted capacity MUST declare a job-level time limit (`timeout-minutes` on GitHub Actions). Without one, a hung job holds its runner, and any scheduler slot that runner holds, for the forge's default limit, while every merge in that repository waits behind it. The limit MUST be derived from that job's own measured run time: the smallest of 30, 45, 60, 90, 120, 180, 240 and 360 minutes that is at least 1.25 times the longest started-to-completed duration the job recorded over the most recent 7 days of runs. A limit MUST NOT be set below that value, because a limit that a slowed but healthy run can reach turns host contention into red CI. A job that recorded no run in the 7-day window MUST NOT be given a guessed limit: it declares no derived limit, and the absence and its reason MUST be recorded beside the job until a measured run exists. A job whose runner can only resolve to hosted capacity is outside this clause.

Add one scenario to `scenarios.md`, as a new `## ` heading with a Gherkin block in the file's existing form:

```gherkin
Feature: Bounding a self-hosted gating job's run time

Scenario: A hung job releases its runner at its declared limit
  Given a fleet repository whose merge-gating job resolves to self-hosted capacity and declares a time limit derived from its own 7-day maximum
  When a run of that job stops making progress
  Then the forge cancels the job once it has run for its declared limit
  And the runner and any scheduler slot it held are released for the next job

Scenario: A slowed but healthy run finishes inside its limit
  Given a self-hosted gating job whose declared limit is at least 1.25 times its longest run in the most recent 7 days
  When host contention slows a run of it to that longest recorded duration
  Then the run completes with the conclusion it would have reached without the limit

Scenario: A job with no measured run records an absence, not a guessed limit
  Given a self-hosted gating job that recorded no run in the most recent 7 days
  When the repository's job time limits are derived
  Then that job declares no derived limit
  And the absence and its reason are recorded beside the job
```

The scenario heading MUST read: `## A hung self-hosted gating job is cancelled at its measured time limit`. The revise that accepts this proposal MUST add a matching `tests/heading-coverage.json` entry for that heading in the same commit.
