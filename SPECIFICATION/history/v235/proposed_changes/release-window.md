---
topic: release-window
author: claude-opus-5-5:ci-runtime-and-cost
created_at: 2026-11-03T15:38:41Z
---

## Proposal: release-please opens its release PR on a release window, not on every push

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Replace contracts.md §"Plugin versioning"'s "release-please opens a release PR on every push to master" with a release WINDOW: release-please opens or updates its release PR only on a schedule and on manual dispatch, while a push to master runs it only to tag a release PR that has just merged. Add a scenario stating the observable behaviour.

### Motivation

Measured over the 7 days to 2026-11-03 (plan ci-runtime-and-cost, livespec-dev-tooling, research 002): release mechanics were 34% of all fleet k3s CI time (release-please PR CI 102.1 h, release master CI 68.2 h, pin-bump PR CI 80.3 h, pin-bump master CI 77.8 h, of 964.5 job-hours). livespec-orchestrator-beads-fabro cut 110 releases in that week and livespec-dev-tooling 49 (about 20 on 2026-11-02 alone), because a release PR opens and auto-merges after every feature merge, and each release fans a pin-bump PR and a master CI run out to every sibling. A four-hour window bounds a repository to at most six releases per UTC day, removing about 68 of the orchestrator's 110 weekly releases with the same ratio of the sibling fan-out. The maintainer ordered this work directly on 2026-11-03 at 15:00:49Z (recorded on livespec-dev-tooling-6tgd2z: "livespec-dev-tooling-aplxhg - get this done too"); this proposal ratifies the rule the workflow edit realizes. The pin-currency settle window (livespec-dev-tooling contracts.md §"Pin-currency severity policy") is measured from the release's own published_at, and the fan-out still fires on release: published, so a windowed release cannot read as a stale pin: the window changes how often a release is cut, not how fast a cut release fans out.

### Proposed Changes

In `SPECIFICATION/contracts.md` §"Plugin versioning", replace the sentence

> release-please opens a release PR on every push to `master` carrying the next-version bump per the Conventional Commits → semver mapping:

with

> release-please opens or updates a release PR carrying the next-version bump per the Conventional Commits → semver mapping below, and it MUST do so only from a release WINDOW: a `schedule` trigger (the reference cadence is every four hours) and `workflow_dispatch`. A release PR opened from the window MUST carry every Conventional Commit merged to `master` since the previous release. A `push` to `master` MUST NOT open or update a release PR; it MUST run release-please only when the pushed head commit is a merged release PR, and then only to tag that release and create its GitHub Release (release-please-action's `skip-github-pull-request: true`), so the release and the cross-repo fan-out it triggers on `release: published` fire as soon as the release PR merges. A repository therefore cuts at most one release per window, and at most six per UTC day at the reference cadence. The window is a property of each repository's own `release-please.yml`; a repository MAY run a longer window, and MUST NOT run release-please's pull-request pass on `push`.

The mapping list that follows (`feat:` → MINOR and so on) is unchanged.

In `SPECIFICATION/scenarios.md`, add a new H2 section after the last existing section:

```markdown
## Releases are cut from a release window

```gherkin
Feature: Coalesced releases

Scenario: Merges between windows ship in one release
  Given a repository whose release-please workflow runs on a four-hour schedule
  And three feat: commits merge to master between two scheduled runs
  When the next scheduled run fires
  Then release-please opens one release PR carrying all three commits
  And no release PR was opened or updated by the three pushes

Scenario: A merged release PR is tagged at once
  Given a release PR opened by the scheduled run
  When the release PR merges to master
  Then the push of its release commit tags the release and creates its GitHub Release
  And that push opens no new release PR
```
```
