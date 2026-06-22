---
topic: retire-auto-update-branches
author: retire-auto-update-branches
created_at: 2026-06-22T20:44:11Z
---

## Proposal: Retire the auto-update-branches.yml required workflow

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Remove auto-update-branches.yml from the EXHAUSTIVE required-workflow-file set enumerated in non-functional-requirements.md §"Shared content sync — copier template". The workflow auto-merged master into every BEHIND open PR on each master push (via the GitHub update-branch REST endpoint, which produces a merge commit), making it the source of merge-commit injection into behind PRs and a violation of the family's linear-history goal. The auto-enable-merge.yml workflow stays; its bullet absorbs a one-clause rationale explaining why no pre-merge branch-update step is needed.

### Motivation

The maintainer decided to remove auto-update-branches.yml family-wide. strict=false branch protection plus auto-enable-merge's rebase-merge-on-current-tip plus post-merge CI is the robust replacement: rebase-merge resolves each PR against the current master tip at merge time and re-runs CI on the rebased result, so the pre-merge branch-update step auto-update-branches performed is unnecessary and its merge-commit injection is eliminated.

### Proposed Changes

In non-functional-requirements.md §"Shared content sync — copier template", delete the bullet:

```
- `auto-update-branches.yml` — auto-updates open-PR branches against `master` when the base advances. Paired with `auto-enable-merge.yml`; together they make merging a hands-free operation for green PRs.
```

The pairing-note language ("Paired with `auto-enable-merge.yml`; together they make merging a hands-free operation for green PRs") lived entirely inside the deleted bullet, so deleting it resolves the dangle. Fold a one-clause standalone rationale into the surviving `auto-enable-merge.yml` bullet so the merge story stands on its own:

```
- `auto-enable-merge.yml` — auto-enables REBASE auto-merge on PR open. Required so that propose-change PRs in every impl-plugin repo merge with the same cadence as upstream `livespec` PRs (incident 2026-05-26: `livespec-impl-plaintext` PR #26 sat OPEN/CLEAN for 10+ minutes because this file was absent). Rebase-merge resolves each PR against the current `master` tip at merge time and re-runs CI on the rebased result, so no pre-merge branch-update step is required.
```

The list remains EXHAUSTIVE; the corresponding hard-coded REQUIRED_WORKFLOW_FILES list in the `copier-template-workflow-coverage` doctor check and the deleted template/livespec workflow files are co-removed in the same change so the spec enumeration and the doctor invariant stay in lockstep per the EXHAUSTIVE-list discipline in this section. No `## ` heading changes (the edit is a bullet inside the existing §"Shared content sync — copier template" H3 under `## Contracts`).
