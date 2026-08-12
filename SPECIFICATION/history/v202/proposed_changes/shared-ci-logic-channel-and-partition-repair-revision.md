---
proposal: shared-ci-logic-channel-and-partition-repair.md
decision: accept
revised_at: 2026-08-12T00:32:03Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted after four independent read-only adversarial review rounds by separately-spawned Fable reviewers, deliberately given different instruments so that agreement between them is corroboration rather than one verdict counted twice. Round 1 (ratified-spec-text and repo-topology instruments) returned five blockers with zero overlap; round 2 (mechanical-composition and fix-adequacy instruments) returned four, three of which the round-1 fix round had itself introduced; the final-bytes round returned one, a citation that was precise and false. Every blocker was fixed and re-verified against live bytes, never waived. The proposal repairs a ratified clause-lockstep contradiction (livespec-n0ka) by making the existing section 'Shared content provenance' the single authority for the shared-content channel partition, de-duplicating the five other assertion sites and removing every cardinal count so a future channel addition cannot leave a stale number behind; and it names the delivery lane livespec-jvdvx4.9 requires and no ratified channel provides, with core itself as producer, which the No-Circular-Dependency Directive permits as consumer-to-producer. The two upstream sibling libraries are excluded by construction, and the governance gap that exposes is stated in the ratified text and tracked as livespec-jvz8 rather than left silent. The evidence block's reviewer_identity reads 'fable' because the CLI requires identity to equal the configured reviewer model; the final-bytes verdict was returned by a separately-spawned read-only agent named review-final-bytes running Fable 5 (claude-fable-5) at 2026-08-12T00:30:08Z, which mapped all 8 diff hunks to authorizing changes, proved byte-identity of the unchanged remainder two independent ways after master moved, and confirmed the H2 set unchanged.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: manual-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-12T00:30:08Z
verdict: NO BLOCKERS
proposal_stem: shared-ci-logic-channel-and-partition-repair
content_digest: e452ae93f0d1d948cd8769f246d949838e1b64cc775079a5953259ef63895417
