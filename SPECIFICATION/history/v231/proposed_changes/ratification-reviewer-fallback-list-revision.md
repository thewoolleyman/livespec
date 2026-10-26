---
proposal: ratification-reviewer-fallback-list.md
decision: modify
revised_at: 2026-10-26T21:02:11Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Modified under coordinator ruling R60, on the maintainer's 2026-10-26 direction that the Fable reviewer requirement has outlived its usefulness and should follow the standard for interchangeable models: opus first, with clear allowance for fallbacks, not over-engineered. The configured ratification reviewer (opus, read-only) returned NO BLOCKERS on its second pass after one blocker was folded in.

## Modifications

Simplified from the filed proposal: ratification_reviewer_model accepts a string or an ordered list (primary first), and evidence satisfies the designation when its reviewer model equals ANY entry, with the independent-review floor unchanged for every entry. Dropped the filed text's try-in-order duty and its fallback-recording evidence fields. Escalation is for a missing or malformed designation or the unavailability of every listed model, both in the effective_ratification_review paragraph and in 'No ratification with zero independent review'. The stale 'MUST designate fable' sentence is replaced by 'MUST designate opus as the primary entry' (this repo already says opus), and the fleet-wide Fable designation is recorded as retired 2026-10-26. Adds one scenario: a reviewer from the designated list ratifies, and a model not in the list is rejected.

## Resulting Changes

- spec.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-26T21:01:58Z
verdict: NO BLOCKERS
proposal_stem: ratification-reviewer-fallback-list
content_digest: cbbef04dfd0957064506589805d0df6a9062fc5af2779360d1d70dd4d37a432a
