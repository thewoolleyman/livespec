---
proposal: merge-gate-check-enforces-strict-off.md
decision: accept
revised_at: 2026-06-22T18:32:37Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: strict-off-enforce
---

## Decision and Rationale

Ratify the contract addition: the branch_protection_alignment check now ENFORCES that `strict` is off (per the merge-gate rule changed in PR #521). The new clause is added to the check's enumerated failure conditions; the rest of the paragraph is unchanged. No `## ` heading set changes, so no tests/heading-coverage.json co-edit is required.

## Resulting Changes

- non-functional-requirements.md
