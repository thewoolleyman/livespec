---
proposal: pi-dogfooding.md
decision: accept
revised_at: 2026-08-15T12:57:15Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5-bootstrap-pi-driver
---

## Decision and Rationale

Accepted as filed (with the review-driven repairs already amended into the proposal before this pass). The proposal promotes pi to current reference Driver work, adds the pi distribution channel (resource-less git package, project-scoped committed .pi/settings.json, release-branch currency anchored to pi v0.84.1 with a major-bump re-verify obligation, trust-gate caveat), generalizes the Driver-shipped-hooks clauses to every-Driver form with the pi footgun-guard requirement, and adds the three pi dogfooding sections plus two scenarios. Independent adversarial review of the proposal ran three rounds to NO-BLOCKERS (commit c23534f7); an independent Fable-model ratification review re-derived the assembled resulting_files bytes from fresh baselines and attested NO BLOCKERS with a matching canonical digest. Plan: bootstrap-pi-driver, epic livespec-g5h5ff, child livespec-dsnlkx.

## Resulting Changes

- spec.md
- contracts.md
- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-15T12:55:15Z
verdict: NO BLOCKERS
proposal_stem: pi-dogfooding
content_digest: b65a6aa65ba0d06e1beab795181bd954a7c3ed120d58e5192211e79e7cb840e8
