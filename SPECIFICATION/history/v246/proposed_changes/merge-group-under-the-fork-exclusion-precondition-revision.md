---
proposal: merge-group-under-the-fork-exclusion-precondition.md
decision: accept
revised_at: 2026-11-14T07:38:16Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted as filed under delegated revise authority, in the livespec revise slot legacy-coordinator-agent granted to plan stale-base-merge-options (livespec-dev-tooling epic xowhol), cut as v246 directly after red-master-self-healing's v245 (livespec#3220), separate by agreement between the two plans. throughput-plans-coordinator graded the proposals PASS-WITH-FIXES and then PASS at 69d59c18 before livespec#3215 merged. DELIBERATE DEPARTURE, named per the intent-preservation gate: this revise replaces the v126 statement that the fleet does not substitute a merge queue because GitHub merge queues are organization-only. The maintainer chose the organization move and adoption of GitHub's merge queue (scope event on livespec-dev-tooling-xowhol, 2026-11-12T19:34:25Z: "OK, we are going to go with the org move"), created the organization github.com/livespec-ai on GitHub Team, approved the plan's Definition of Done verbatim (epic comment 27, 2026-11-13; it requires the queue on livespec-dev-tooling and livespec-orchestrator-beads-fabro), and ruled call 3 option A, guarded self-hosted runners for merge_group (epic comment 27). The premise of the replaced statement no longer holds once the fleet is organization-owned, and incident livespec-dev-tooling-3hilpy plus three further stale-base episodes measured in that plan's note 007 show the post-merge catch failing. `strict` stays forbidden, unchanged. This decision's resulting file is CUMULATIVE: the revise CLI writes decisions in order to the same path, so its non-functional-requirements.md carries the merge-queue decision's edits plus this proposal's (the Event routing replacement with the guarded merge_group class, the failed-guard rule, the Fork-exclusion append, and two scenarios under '## Scenarios'); its digest binds those exact final bytes, and the independent review diffed it against the merge-queue decision's file to confirm only this proposal's changes were added. Follow-on work: livespec-dev-tooling-mvqo6h, which owns the dev-tooling self_hosted_routing and branch_protection_alignment change ratified separately in livespec-dev-tooling.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-14T07:37:39Z
verdict: NO BLOCKERS
proposal_stem: merge-group-under-the-fork-exclusion-precondition
content_digest: f44738edf801bc57d649b3d3faeba6fab99b2a7bc6fc135cc10c1565bace965e
