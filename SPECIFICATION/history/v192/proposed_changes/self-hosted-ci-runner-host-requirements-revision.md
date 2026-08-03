---
proposal: self-hosted-ci-runner-host-requirements.md
decision: accept
revised_at: 2026-08-03T09:35:46Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted. The proposal answers a question the superseded GitHub-hosted-only posture explicitly deferred to a later revision: what a host must provide before fleet CI may execute on it. Placement follows the Boundary litmus — a project merely governed by livespec does not inherit livespec's CI host provisioning, so this is contributor-facing infrastructure belonging in non-functional-requirements.md rather than in contracts.md or constraints.md. Requirements are stated as host-observable properties rather than package names so realization stays owned by the provisioning repository and a non-FHS distribution can conform by its own means. The containment floor is reduced per the maintainer's 2026-08-03 decision that the fleet accepts no fork pull requests; that premise is ratified as a binding fork-exclusion precondition rather than as rationale, so the reduction cannot silently outlive the condition that justifies it. Two clauses departed from the filed proposal text and the departures are recorded here: (1) the proposal's self-referential sentence declaring itself the reactivation revision was dropped, because it names a paragraph that ceases to exist at the moment of ratification and would read as a dangling reference thereafter; the rule is stated positively instead, and the supersession history remains in this revision record and history/v189. (2) The fork-approval clause was tightened to require approval for all outside contributors rather than only first-time ones, because the weaker setting lets a returning outside contributor's fork pull request run with no human approval, which would void the precondition the reduced floor rests on. The unrelated pending proposal railway-dependency-supply-for-a-source-copied-library remains in the queue for its own cycle; it has had no ratification review and is not part of this pass.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-03T09:34:39Z
verdict: NO BLOCKERS
proposal_stem: self-hosted-ci-runner-host-requirements
content_digest: d0216a808bed66de86796f4983cd47937488708f9f1a9dbfb53c594037e2d10f
