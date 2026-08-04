---
proposal: plan-thread-tombstone-ban.md
decision: accept
revised_at: 2026-08-04T16:12:55Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted after two rounds of independent adversarial review plus a third pass verifying the LANDED BYTES against the cleared clause. Round 1 found the draft stated an archival-EVENT rule while the shipped plan_thread_no_tombstone check enforces a STATE invariant, so an event-only rule permitted retired-slug reuse the check hard-fails with no sanctioned green path; the reviewer ruled the prose wrong, not the check. Round 2 found two defects in that fix: an unqualified move-back arm licensing an active thread with a closed epic, and a third sanctioned living home carried in from the orchestrator tree (which does sanction it) into core (which forbids the neighbourhood). Round 3 checked this file's rendering word-by-word and caught a four-word meta addition — a shortened resurrection of a framing sentence the reviewer had asked be dropped — which contradicted the proposal's own 'nothing else is to be landed' instruction; it is removed here and the revise pass redone from master so the recorded digest binds the reviewer's verdict to the bytes that actually land. DELIBERATELY SCOPED partial revise pass: the payload names only this topic, so the other in-flight proposals in this tree are neither read nor disposed of.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: manual-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-04T16:07:08Z
verdict: NO BLOCKERS
proposal_stem: plan-thread-tombstone-ban
content_digest: 9701ec9ded87160360280138503fd7ff0e977c7a4cae7d99df22e8855c58719f
