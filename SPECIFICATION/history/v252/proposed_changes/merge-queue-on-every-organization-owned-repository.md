---
topic: merge-queue-on-every-organization-owned-repository
author: claude-sonnet-5-5
created_at: 2026-11-16T19:00:02Z
---

## Proposal: merge-queue-on-every-organization-owned-repository

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Require GitHub's merge queue on master for every organization-owned repository (every livespec-ai repository), replacing the MAY plus two-named-repositories rule, with no opt-in or opt-out.

### Motivation

Maintainer ruling on stale-base-merge-options epic livespec-dev-tooling-xowhol, 2026-11-16: "No I think we should turn on the merge queue for every repo in the org. Why wouldn't we?" The NFR currently makes the queue mandatory only for livespec-dev-tooling and livespec-orchestrator-beads-fabro and optional (MAY) elsewhere, so the other organization repositories merge without the composed-tree run and a stale-base merge is possible there. livespec-dev-tooling cannot change this core NFR in its own revise, hence this companion; its sibling proposal is livespec-ai/livespec-dev-tooling#4857. In-flight survey: pending proposals merge-queue-exception-names-the-recovery-principal and incident-merge-principal edit the recovery-bypass exception of the same paragraph but not its first sentence (relationship: align; the edits are disjoint sentences). Open spec PRs livespec#3206 (tests-that-run-a-real) and livespec#3189 (release-gate-todo-liveness-fails-closed) are unrelated (align). Remote branch spec/old-owner-refs-livespec-ai is unrelated (align).

### Proposed Changes

1. In SPECIFICATION/non-functional-requirements.md, paragraph **Merge queue on organization-owned repositories** (under section "CI as a merge gate (branch protection)"), replace the first sentence ("A fleet repository owned by a GitHub organization MAY require GitHub's merge queue on `master`, and livespec-dev-tooling and livespec-orchestrator-beads-fabro MUST require it while they are organization-owned.") with: "Every repository whose owner is a GitHub organization (owner `type` `Organization`) MUST require GitHub's merge queue on `master`; this covers every repository of the livespec-ai organization, with no per-repository name list, no opt-in and no opt-out, and a repository cannot configure itself out of the queue. The requirement changes only with a livespec specification revision." Leave clauses (a) through (e), the recovery-bypass exception, the personal-account sentence ("A repository owned by a personal account cannot use the merge queue and keeps the post-merge catch.") and the closing sentence about the hand-rolled auto-rebase driver unchanged. Where the same section's strict-rationale sentence says "where the repository requires a merge queue", no edit is needed: it stays true, and now holds for every organization-owned repository.

2. In SPECIFICATION/non-functional-requirements.md, add this scenario immediately after "### Scenario: A merge queue ejects the second of two pull requests that break CI only together" (a `###` scenario, so tests/heading-coverage.json needs no new row):

### Scenario: Every organization-owned fleet repository requires the merge queue

Given a repository owned by the organization livespec-ai, such as livespec-website, that is not livespec-dev-tooling or livespec-orchestrator-beads-fabro

And no active ruleset on its default branch carries a merge_queue rule

When its branch protection is audited against this specification

Then the repository is non-conforming, exactly as livespec-dev-tooling would be

And the repository cannot restore conformance by configuration that opts it out of the queue

And a repository owned by a personal account is not subject to this requirement and keeps the post-merge catch.

Cross-repo placement: the requirement text is livespec core's. The enforcement realization (the branch_protection_alignment check and its QUEUE_REQUIRED_REPOSITORIES constant) belongs to livespec-dev-tooling, whose sibling proposal is livespec-ai/livespec-dev-tooling#4857 (queue-required-every-org-repo), which replaces that constant with an owner test. The two agree: every livespec-ai repository is queue-required.
