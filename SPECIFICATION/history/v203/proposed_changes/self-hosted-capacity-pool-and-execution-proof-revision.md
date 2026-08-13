---
proposal: self-hosted-capacity-pool-and-execution-proof.md
decision: accept
revised_at: 2026-08-13T01:44:42Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5-fleet-ci-runner-pool
---

## Decision and Rationale

Records two properties the section was silent about, both derived from provisioning the fleet's first conforming host end-to-end rather than from reading the text: that self-hosted capacity is a label-keyed pool whose hosts are additive co-members rather than successors, with a host-unique label required alongside the shared pool label so a single member can still be addressed; and that a host is proven by EXECUTING a job rather than by registering one. The second is the load-bearing one: four containment tests reported FAIL on a host whose containment was intact, while registration had already succeeded and the runner reported online, so every cheap signal read green and only running a job settled it. Independent read-only adversarial review by a separately-spawned Fable-model agent returned NO BLOCKERS on the amended text, after an earlier round's finding about an unanchored arm64 claim was corrected.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-13T01:43:00Z
verdict: NO BLOCKERS
proposal_stem: self-hosted-capacity-pool-and-execution-proof
content_digest: 1ff2870568bb74addaa85a520502abc72a66e81e5cafd374758b9599f77320b3
