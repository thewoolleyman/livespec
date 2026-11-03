---
proposal: expedited-incident-policy-core.md
decision: modify
revised_at: 2026-11-03T21:10:15Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: codex:expedited-incident-response-flag/core-revise
---

## Decision and Rationale

Ratify with minimal formatting corrections from the configured independent review, preserving the maintainer-directed incident-only policy, preserving complete normal master and factory validation, exact incident receipts, scoped recovery authority, and owning-repository lifecycle boundaries. Apply proposal hunks by exact context against current v235 so its unrelated release-window clauses and scenarios remain intact; co-edit new heading coverage with the existing livespec-3lwk4n owner.

## Modifications

Preserve the required blank line separating the inserted incident scenario block from the existing v235 release-window scenario and the trailing newline of contracts.md when applying the proposal end-of-file hunks to the current tree; preserve the registry UTF-8 style. No normative incident behavior changes.

## Resulting Changes

- contracts.md
- non-functional-requirements.md
- scenarios.md
- ../tests/heading-coverage.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-03T21:08:06Z
verdict: NO BLOCKERS
proposal_stem: expedited-incident-policy-core
content_digest: fa7021419cd6805c865a67abe72d3d42d2e1d679613ed5320ddcef83e4c6dfc3
