---
proposal: doctor-spec-target-drift.md
decision: accept
revised_at: 2026-08-14T05:22:42Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5-spec-side-autonomy
---

## Decision and Rationale

Accepted, direction confirmed by the maintainer 2026-08-12: document the flag rather than delete it. contracts.md stated in two places that the doctor static wrapper takes only --project-root, while the shipped CLI has accepted and honoured --spec-target since 8486f955 (2026-07-01); two path-resolution crashes in that flag's own code were fixed in PRs #2222 and #2225, so real work had been invested in behaviour the contract denied existed. Every sibling spec-tree-scoped wrapper already declares the flag, and sibling repos' live specs already invoke it. Independent adversarial review by a separately-spawned Fable reviewer initially returned ONE BLOCKER: core's own .claude-plugin/prose/doctor.md -- the harness-neutral artifact both Drivers read at invocation time -- enumerated doctor's flags without --spec-target, so ratifying the contract alone would have left core contradicting itself. That prose co-edit is included in this same payload, making contract and prose atomic; the amended proposal plus the exact resulting bytes were re-reviewed to NO BLOCKERS.

## Resulting Changes

- contracts.md
- ../.claude-plugin/prose/doctor.md

## Ratification Review

ratification_review: manual-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-14T05:21:23Z
verdict: NO BLOCKERS
proposal_stem: doctor-spec-target-drift
content_digest: e8beec3ab30e8c5f87890b2e8a7f8dcc2119f2aee724613423062d4c5b9c6689
