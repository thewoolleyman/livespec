---
topic: live-exercise-floor-probe
created_at: 2026-08-11T00:00:00Z
---

# Live-exercise floor probe — DO NOT MERGE

This file exists ONLY to drive the `livespec-jvdvx4.6` live exercise
(leg 1). It is shaped exactly like a ratified proposal so that the
`auto-enable-merge` workflow derives it as an introduced proposal stem:
a non-`-revision` file ADDED under
`SPECIFICATION/history/*/proposed_changes/<stem>.md`.

It deliberately carries NO `spec_pr_merge_policy` front-matter key, so
the single-proposal effective policy resolves to the safe `manual`
default, and the pull-request conservative fold therefore floors the
whole pull request to `manual`.

The expected and REQUIRED observation is that auto-merge is NOT
registered on the pull request carrying this file. The pull request is
closed and its branch deleted as soon as that observation is recorded.
It must never merge, and this file must never reach `master`.
