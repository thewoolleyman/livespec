---
proposal: merge-queue-on-organization-owned-fleet-repositories.md
decision: accept
revised_at: 2026-11-14T07:51:40Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted as filed under delegated revise authority, in the livespec revise slot legacy-coordinator-agent granted to plan stale-base-merge-options (livespec-dev-tooling epic xowhol), cut as v246 directly after red-master-self-healing's v245 (livespec#3220), separate by agreement between the two plans. throughput-plans-coordinator graded the proposals PASS-WITH-FIXES and then PASS at 69d59c18 before livespec#3215 merged. DELIBERATE DEPARTURE, named per the intent-preservation gate: this revise replaces the v126 statement that the fleet does not substitute a merge queue because GitHub merge queues are organization-only. The maintainer chose the organization move and adoption of GitHub's merge queue (scope event on livespec-dev-tooling-xowhol, 2026-11-12T19:34:25Z: "OK, we are going to go with the org move"), created the organization github.com/livespec-ai on GitHub Team, approved the plan's Definition of Done verbatim (epic comment 27, 2026-11-13; it requires the queue on livespec-dev-tooling and livespec-orchestrator-beads-fabro), and ruled call 3 option A, guarded self-hosted runners for merge_group (epic comment 27). The premise of the replaced statement no longer holds once the fleet is organization-owned, and incident livespec-dev-tooling-3hilpy plus three further stale-base episodes measured in that plan's note 007 show the post-merge catch failing. `strict` stays forbidden, unchanged. Placement: the two replaced sentences sat mid-paragraph in the strict rationale, so the paragraph is kept whole with the new 'one case it would have caught' sentence, and the 'Merge queue on organization-owned repositories' block follows as its own paragraph with conditions (a)-(e) written inline; the independent review confirmed no condition or meaning is lost. The scenario 'A merge queue ejects the second of two pull requests that break CI only together' is added under '## Scenarios'. No '## ' heading is added, so tests/heading-coverage.json is unchanged. Review nits not acted on: the amended 'Outside the explicit incident-only policy' sentence names the section rather than saying 'above', and reads a little heavily. Follow-on work: livespec-dev-tooling-o6eytb (the queue requirement and the semantic-conflict drill).

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
proposal_stem: merge-queue-on-organization-owned-fleet-repositories
content_digest: 12ee9d21fb609351157bbaf216b19e458c52e05e0978cb27d23e171759ab03f6
