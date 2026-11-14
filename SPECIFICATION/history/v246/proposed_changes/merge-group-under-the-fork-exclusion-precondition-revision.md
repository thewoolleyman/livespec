---
proposal: merge-group-under-the-fork-exclusion-precondition.md
decision: accept
revised_at: 2026-11-14T07:51:40Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted as filed under delegated revise authority, in the same v246 pass as merge-queue-on-organization-owned-fleet-repositories (see that record for the slot, the grade, and the named departure from v126). Conditions (a)-(c) of the guarded merge_group class carry the proposal's wording verbatim, including "the workflow's first job" and "that first job's output"; the allowed events and conditions are written inline rather than as bullets, a formatting choice only. This decision's resulting file is CUMULATIVE: the revise CLI writes decisions in order to the same path, so its non-functional-requirements.md carries the merge-queue decision's edits plus this proposal's (the Event routing replacement with the guarded merge_group class and the failed-guard rule, the Fork-exclusion append, and two scenarios under '## Scenarios'). Its digest binds those exact final bytes, and the independent review diffed it against the merge-queue decision's file to confirm only this proposal's changes were added. Re-cut after throughput-plans-coordinator's grade found the first cut had written "a guard job" where the proposal says "the workflow's first job"; the review was re-run on the corrected bytes. Follow-on work: livespec-dev-tooling-mvqo6h (the dev-tooling self_hosted_routing and branch_protection_alignment change, ratified separately in livespec-dev-tooling; a credential-bearing merge_group job such as e2e-test-claude-code-real must stay hosted under Credential separation).

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-14T07:51:02Z
verdict: NO BLOCKERS
proposal_stem: merge-group-under-the-fork-exclusion-precondition
content_digest: 8dcfeab091a80df583ca1c28b30fdeb1db0a38f03105078e2a401132dc4fd8f7
