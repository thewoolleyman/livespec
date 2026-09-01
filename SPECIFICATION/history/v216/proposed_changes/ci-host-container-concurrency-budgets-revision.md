---
proposal: ci-host-container-concurrency-budgets.md
decision: accept
revised_at: 2026-09-01T16:13:46Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Ratifies two host-observable property clauses into non-functional-requirements.md §"Self-hosted CI runner host requirements", both scoped to the OPTIONAL containerized-execution path: (1) the kernel's per-user watch budget MUST cover peak container concurrency × per-container watch instances, with headroom; (2) the node's schedulable-unit capacity MUST cover the full expansion of the scheduler's concurrency cap (units-per-job × cap + infra + system units), with headroom. Carrier for livespec-sknvkp (epic livespec-ifwnqj, plan ci-runner-pod-lifecycle-reliability); motivated by the 2026-09-01 fleet-CI stall (inotify instance ceiling exhausted at ~100 containers; C=64 → ≥128 job pods vs default max-pods 110). Independent opus ratification review returned NO BLOCKERS on the exact resulting bytes; an independent Fable review of the proposal also returned NO BLOCKERS.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-01T16:11:29Z
verdict: NO BLOCKERS
proposal_stem: ci-host-container-concurrency-budgets
content_digest: 3d7e730d3dcc3cb8939ee06a10c935e1d393bcab99f208ff1a33f0b69459d433
