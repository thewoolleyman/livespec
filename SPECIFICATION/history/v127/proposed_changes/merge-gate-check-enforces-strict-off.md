---
topic: merge-gate-check-enforces-strict-off
author: strict-off-enforce
created_at: 2026-06-22T18:32:16Z
---

## Proposal: branch_protection_alignment enforces strict-off

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

PR #521 changed the merge-gate (branch protection) NFR rule so the protection MUST NOT enable `strict`. The companion `branch_protection_alignment` shared check is now being updated to ENFORCE that constraint. Document the new failure condition in the contract: the check MUST fail when `strict` IS enabled (it MUST be off per the rule above).

### Motivation

The contract paragraph describing the branch_protection_alignment check's failure conditions lists protection-absent, enforce_admins-unset, and required-check-set-omission, but does not yet capture the strict-must-be-off enforcement that the check is gaining. Add the missing clause.

### Proposed Changes

In §"CI as a merge gate (branch protection)", amend the sentence enumerating the branch_protection_alignment check's failure conditions. Add the `strict IS enabled` clause (it MUST be off per the rule above) between the `enforce_admins` clause and the required-check-set clause; leave the rest of the paragraph intact. New sentence:

"The check MUST fail when branch protection is absent on `master`, when `enforce_admins` is not set, when `strict` IS enabled (it MUST be off per the rule above), or when the protection's required-check set does not cover the repo's CI matrix."
