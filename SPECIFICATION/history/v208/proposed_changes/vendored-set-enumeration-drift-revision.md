---
proposal: vendored-set-enumeration-drift.md
decision: accept
revised_at: 2026-08-15T13:03:10Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-sonnet-5-spec-side-autonomy
---

## Decision and Rationale

Maintainer-authorized accept (2026-08-15) supersedes v104's livespec_runtime removal plan on changed facts (v206 put the spec-governance manifest inside the vendored tree core cannot delete). Passed a fourth independent Fable adversarial review with NO BLOCKERS after three rounds of review-found, worktree-fixed blockers (2, then 2, then 1) converged to zero; each round's fix verified clean under the next round's full fresh review. Master verified undrifted on the three target files since the reviewed commit 827294ff immediately before this accept.

## Resulting Changes

- spec.md
- constraints.md
- non-functional-requirements.md

## Ratification Review

ratification_review: manual-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-15T13:00:00Z
verdict: NO BLOCKERS
proposal_stem: vendored-set-enumeration-drift
content_digest: 38db1a90a6a364919d29d0f76e525f05acfa95f23b7d9b376ef2069f7a536ab0
