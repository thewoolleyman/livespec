---
proposal: merge-gate-drop-strict.md
decision: accept
revised_at: 2026-06-22T16:52:16Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: merge-gate-drop-strict
---

## Decision and Rationale

Maintainer has decided the GitHub strict (require-branches-up-to-date) branch-protection setting must be OFF family-wide. The contract is flipped to mandate enforce_admins + MUST NOT enable strict, with the auto-merge/rebase-merge rationale codified, and the branch_protection_alignment check failure conditions and per-repo enable step updated to match. No `## ` heading changes; spec prose only.

## Resulting Changes

- non-functional-requirements.md
