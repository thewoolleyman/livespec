---
topic: hold-label-disarm-inherited-policy
author: claude-opus-5-5
created_at: 2026-11-10T22:28:50Z
---

## Proposal: A hold label added after auto-merge was armed turns auto-merge off, as inherited fleet policy

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/scenarios.md

### Summary

Add `disarm-on-hold-label.yml` to the EXHAUSTIVE orchestrator-plugin template workflow list in §"Shared content sync — copier template", right after the `auto-enable-merge.yml` bullet, stating its behaviour as BCP14 clauses; add a paragraph making the auto-enable-merge / disarm pair INHERITED FLEET POLICY that every member carrying `auto-enable-merge.yml` MUST also carry; and add the error-path scenario that pins the behaviour.

### Motivation

`auto-enable-merge.yml` arms rebase auto-merge within seconds of `opened` and skips a pull request that already carries `do-not-merge`, but it has no `labeled` trigger, so a hold label added AFTER the arm leaves auto-merge on. `gh pr create --label` adds labels in a second API call after `opened` fires, so labelling at creation does not stop the arm either. Measured 2026-11-10 in livespec-dev-tooling: #4019 merged against a coordinator hold, #4031 merged at a head its seat had found failing, and #4033 was armed while its seat reported it unarmed. The fix shipped as a separate disarm-only workflow in livespec-dev-tooling (#4051, work item livespec-dev-tooling-t2ezzq) and in livespec itself (livespec#3159, work item livespec-jznfgw); both were host-captured and independently replayed host_verified. The gap is fleet-wide: every member runs the same arming workflow, so the remedy is one inherited policy owned by core rather than five member-local clauses. Core owns it because the template list in this section is the place the orchestrator scaffold's workflow set is declared, and `copier-template-workflow-coverage` reads that list.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md` §"Shared content sync — copier template", insert the following bullet immediately after the `auto-enable-merge.yml` bullet (and after its nested sub-bullet), before `bump-pin-from-dispatch.yml`:

- `disarm-on-hold-label.yml` — turns a pull request's auto-merge OFF when the `do-not-merge` label is ADDED to it, so a hold can be placed on a pull request that `auto-enable-merge.yml` already armed. It MUST trigger on `pull_request` with the `labeled` activity type only. It MUST act only when the added label is `do-not-merge` and the pull request's head repository is the base repository; any other added label, and any fork pull request, MUST leave the auto-merge state unchanged. It MUST only ever disarm: it calls the GraphQL `disablePullRequestAutoMerge` mutation under the same GitHub App installation token `auto-enable-merge.yml` mints, does nothing when auto-merge is already off, and MUST NOT arm auto-merge on any path. `auto-enable-merge.yml` MUST NOT gain a `labeled` trigger, because its arming job would then fire on every added label and re-arm a pull request a seat had disarmed by hand. Removing `do-not-merge` re-arms through `auto-enable-merge.yml`'s existing `unlabeled` path. Opening the pull request with `--draft` remains the only ATOMIC hold, because a label added at creation lands after `opened` has fired.

Then, immediately after the paragraph that begins "The list is EXHAUSTIVE for the orchestrator-plugin scaffold", insert this paragraph:

**Hold-label disarm is inherited fleet policy.** The `auto-enable-merge.yml` / `disarm-on-hold-label.yml` pair is fleet policy that every fleet member inherits, not an orchestrator-scaffold detail: every fleet member whose `.github/workflows/` carries `auto-enable-merge.yml` MUST also carry `disarm-on-hold-label.yml` with the behaviour stated in its bullet above. A template-born member receives the file through `copier update --vcs-ref=master`. A member that is not template-born — `livespec` itself, `livespec-dev-tooling`, `livespec-overseer`, `livespec-runtime`, and the Driver plugins — carries its own copy, and its specification MUST cite this section for the behaviour rather than restate it. This paragraph documents the obligation and adds no asserted fleet-conformance row, so under §"Fleet membership contract" **New-obligation discipline** it carries no retrofit debt when it lands; a later change that arms such a row carries the retrofit for every member it would newly fail.

The same revise MUST co-edit, in one change: the template file `templates/orchestrator-plugin/.github/workflows/disarm-on-hold-label.yml.jinja`, whose rendered body is byte-identical to livespec's root `.github/workflows/disarm-on-hold-label.yml` (any `${{ ... }}` expression escaped for Jinja exactly as `auto-enable-merge.yml.jinja` escapes its own); and the `copier-template-workflow-coverage` doctor invariant's hard-coded required list, which gains `disarm-on-hold-label.yml` (per `contracts.md` §"Doctor cross-boundary invariants", which reads this section's list and is otherwise unchanged). Sequencing for the one template-born consumer, `livespec-orchestrator-beads-fabro`: its `copier update --vcs-ref=master` carrying the new file lands in that repository's work item for this rollout, and if the livespec pin bump that carries the extended invariant reaches it first, the `copier update` result joins that pin-bump pull request so the bump does not merge red.

In `SPECIFICATION/scenarios.md`, append this scenario as a new H2 (and add its row to `tests/heading-coverage.json` in the same revise commit):

## Error path — a hold label added after auto-merge was armed disarms it

```gherkin
Feature: Holding a pull request the fleet bot already armed
  As a fleet seat placing a merge hold
  I want adding the hold label to turn auto-merge off
  So that a held pull request cannot merge on green

Scenario: Adding do-not-merge to an armed pull request disarms it
  Given a same-repository pull request whose rebase auto-merge is armed
  When the do-not-merge label is added to it
  Then its auto-merge is turned off
  And the pull request stays open and unmerged

Scenario: Removing do-not-merge re-arms auto-merge
  Given a same-repository pull request held by the do-not-merge label with auto-merge off
  When the do-not-merge label is removed
  Then its rebase auto-merge is armed again

Scenario: Adding any other label leaves the auto-merge state unchanged
  Given a same-repository pull request whose rebase auto-merge is armed
  When a label other than do-not-merge is added to it
  Then its auto-merge remains armed
```
