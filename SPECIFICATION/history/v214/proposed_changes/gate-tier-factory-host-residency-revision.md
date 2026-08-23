---
proposal: gate-tier-factory-host-residency.md
decision: accept
revised_at: 2026-08-23T10:55:23Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Accepted as amended. The Fleet CI execution posture clause forbade a resident CI supervisor on the shared factory host UNCONDITIONALLY while the deliberately-privileged operator-triggered gate supervisor ran there, provisioned from the repository -- a ratified MUST NOT the fleet violated by design. The amendment names that one tier as an explicit, narrow exception on the prohibition's own grounds (idle-listener co-residency load from a POOL, which a single on-demand supervisor is not), states the factory-host residency honestly as an elected trade-off with reading 1 (relocate) left available in the text, and turns the compensating control into enforceable obligations: repository-installed opt-in gate (landed, livespec-dev-tooling #1615 9c36ab7f) and a wall-clock expiry of at most 24h with no renewal except a fresh explicit operator act -- because the measured state was an opt-in open nine days on a 44-day-uptime host, watching a workflow disabled since 2026-07-14. Independent read-only Fable-model review: first round BLOCKERS (a lockstep miss in the edited paragraph's next sentence; a false necessity ground; an unbounded expiry), all three fixed in livespec PR #2472, none waived; second round NO-BLOCKERS on the amended bytes, full-paragraph target verified verbatim count 1, no H2 change so no heading-coverage co-edit, topic == stem. Work-item livespec-s43svm.43.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-23T10:54:14Z
verdict: NO BLOCKERS
proposal_stem: gate-tier-factory-host-residency
content_digest: c65edd9c9201b595b5b5278ea62cb614e38136a04b7faca0d99b1b8bd4aee54f
