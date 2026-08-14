---
proposal: spec-governance-flag-drift.md
decision: accept
revised_at: 2026-08-14T05:21:26Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5-spec-side-autonomy
---

## Decision and Rationale

Accepted. contracts.md enumerated the spec-governance control CLI's modes as a closed list of three while the shipped CLI has a fourth, --check-default-block, absent from the entire spec tree since 2026-08-04. Direction is forced: the mode is the shipped consumer-side distribution surface a governed downstream repo uses to run the default-block comparison against itself, so deleting it would retract a designed guard surface rather than tidy an unused one. Independent adversarial review by a separately-spawned Fable reviewer initially returned TWO BLOCKERS against the proposal's own record -- a test-file miscount, and a direction rationale that falsely claimed core's just check consumes the mode. Both were fixed (magnitude deleted per the delete-the-magnitude discipline; rationale rewritten to the true No-Circular-Dependency ground) and the amended proposal plus the exact resulting bytes were re-reviewed to NO BLOCKERS. The replacement contract text was verified accurate clause-by-clause in both passes, including the mutual-exclusivity assertion against a real argparse required mutually-exclusive group.

## Resulting Changes

- contracts.md

## Ratification Review

ratification_review: manual-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-14T05:19:53Z
verdict: NO BLOCKERS
proposal_stem: spec-governance-flag-drift
content_digest: e5710b145f94cd4a2104c3dbaf88ff8c24437aec53f3adebf311ed9ac3f33b77
