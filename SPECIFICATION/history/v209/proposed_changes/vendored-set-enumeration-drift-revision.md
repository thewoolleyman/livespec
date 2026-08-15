---
proposal: vendored-set-enumeration-drift.md
decision: accept
revised_at: 2026-08-15T14:57:24Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-sonnet-5-spec-side-autonomy
---

## Decision and Rationale

Maintainer-authorized accept (2026-08-15) supersedes v104's livespec_runtime removal plan on changed facts (v206 put the spec-governance manifest inside the vendored tree core cannot delete). Cuts as v209 (v208 was taken by an unrelated concurrent ratification, pi-dogfooding, commit 50b6ca02). Passed a sixth independent Fable adversarial review with NO BLOCKERS after: three rounds fixing the five spec-text edits (2, then 2, then 1 blockers, converging to a clean round-4 verdict bound to master 827294ff); a version collision when pi-dogfooding ratified v208 first and a livespec-runtime pin bump (e25174b1) landed, staling the proposal body's own measured-state claims (not the spec-text edits); a round-5 fix anchoring those claims to a commit SHA instead of a bare version number; and round 6 confirming the anchored wording is accurate, all five replace-targets still match verbatim exactly once, and nothing else drifted on master since e25174b1's single intervening commit. Master re-verified undrifted since the reviewed commit 1fcb3a38 immediately before this accept.

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
reviewed_at: 2026-08-15T14:56:00Z
verdict: NO BLOCKERS
proposal_stem: vendored-set-enumeration-drift
content_digest: a8dc92a29cc6a613a64c2e9abb66eaccb805790970dbc2e71527e98ef07899f7
