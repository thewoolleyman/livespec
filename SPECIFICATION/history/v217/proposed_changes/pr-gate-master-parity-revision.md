---
proposal: pr-gate-master-parity.md
decision: accept
revised_at: 2026-09-04T18:51:13Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: pr-gate-master-parity plan session (Claude Code)
---

## Decision and Rationale

Accept: retire the v050 zero-.py gate skip so a pull request's gating-check set is identical to what master enforces (PR gate == master gate), the only structural guarantee of the maintainer directive 'NOTHING SHOULD BE ABLE TO BREAK MASTER'. Independent adversarial review by the configured opus ratification reviewer returned NO BLOCKERS (after an earlier Fable pass surfaced and fixed two blockers, and the opus pass surfaced and fixed a third drift-sweep miss now covered by Change 5); all replace-targets verified verbatim; no ## heading change so no heading-coverage co-edit.

## Resulting Changes

- contracts.md
- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-04T18:49:12Z
verdict: NO BLOCKERS
proposal_stem: pr-gate-master-parity
content_digest: 8142adbde0bcd3526868a1e49e9b1f5d1bd9d1e877ae98fb69f8503126559c7f
