---
proposal: every-self-hosted-gating-job-carries-a-measured-timeout-minutes.md
decision: modify
revised_at: 2026-11-08T03:51:37Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5:ci-runtime-and-cost
---

## Decision and Rationale

Accepted under delegated mode. The clause gives the fleet's self-hosted gating jobs a measured time limit, so a hung test no longer holds a runner and a k3s churn slot for the forge's 360-minute default. It also gives the nine Rule G timeout items, which share livespec-dev-tooling-u6jztk's sweep, a ratified clause where their governing-heading verdicts read 'unstated'. Placement in non-functional-requirements.md §"Self-hosted CI runner host requirements" binds every fleet member through core, the same way the rest of that section does. The independent sonnet review found no blockers. Its non-blocking notes are left for a later revise: which runs count toward the 7-day maximum (cancelled or failed runs, or runs that fell back to hosted capacity); 'can resolve through a repository variable' read as in scope; the loose 'recorded beside the job' location; and the reading of 'below that value' for a job capped at 360.

## Modifications

Closes a gap found in the independent review (finding 4): the ladder had no top, so a job whose 1.25-times maximum exceeds 360 minutes could satisfy no rung. One sentence is added to the clause: 'and a job whose 1.25-times value exceeds 360 minutes MUST declare 360 minutes'. Nothing else changes from the proposal, and the scenario is as proposed.

## Resulting Changes

- non-functional-requirements.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-08T03:50:49Z
verdict: NO BLOCKERS
proposal_stem: every-self-hosted-gating-job-carries-a-measured-timeout-minutes
content_digest: 2de67f164e7f1adef8d9994a622fc9036bb52349292083599884c452b3a6ca5c
