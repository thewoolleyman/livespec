---
topic: merge-gate-drop-strict
author: merge-gate-drop-strict
created_at: 2026-06-22T16:51:32Z
---

## Proposal: Drop the strict (require-branches-up-to-date) mandate from the merge-gate contract

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The §"CI as a merge gate (branch protection)" section currently MANDATES GitHub's `strict` (require-branches-up-to-date) branch-protection setting. The maintainer has decided `strict` must be OFF family-wide. This proposal flips the contract: branch protection MUST set `enforce_admins` and MUST NOT enable `strict`, and the `branch_protection_alignment` check's failure conditions and the per-repo enable step are updated to match.

### Motivation

Under `gh pr merge --auto`, `strict` makes GitHub keep a behind PR current by MERGING `master` into its branch, injecting a `Merge branch 'master'` commit that both violates `required_linear_history` and buries the per-commit Red-Green-Replay TDD trailers beneath a trailerless tip — forcing a corrective force-push. Since `master` accepts only rebase-merges, every PR is replayed onto the current `master` tip at merge time regardless of whether its branch was up to date, so `strict` adds no correctness guarantee; the one case it would have caught (a CI-green-against-older-master PR that SEMANTICALLY conflicts with the newer tip) is caught by CI on `master` after the merge. The family deliberately does NOT substitute a merge queue (org-only) or a hand-rolled serialized auto-rebase driver (fragile central loop that can orphan/mis-order/wedge PRs).

### Proposed Changes

Edit two paragraphs within §"CI as a merge gate (branch protection)" in SPECIFICATION/non-functional-requirements.md; no `## ` heading changes (so tests/heading-coverage.json needs no co-edit).

EDIT 1 — replace the `enforce_admins`/strict paragraph entirely so it sets `enforce_admins`, mandates `strict` MUST NOT be enabled, and carries the full rationale (auto-merge merge-commit injection vs required_linear_history and TDD trailers; rebase-merge replays every PR onto the current tip; semantic-conflict case caught by post-merge CI on master; no merge-queue substitution). The required-check-set-coverage sentence is preserved verbatim.

EDIT 2 — in the companion-mechanisms paragraph make two phrase-level changes: (a) the per-repo enable step now enables the protection with the required-check set and `enforce_admins`, explicitly leaving `strict` OFF per the rule above; (b) the `branch_protection_alignment` check's failure list drops the `when strict is not set` clause, so it fails when protection is absent, when `enforce_admins` is not set, or when the required-check set does not cover the CI matrix.
