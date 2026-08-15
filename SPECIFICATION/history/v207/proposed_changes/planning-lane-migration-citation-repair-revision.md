---
proposal: planning-lane-migration-citation-repair.md
decision: accept
revised_at: 2026-08-15T06:21:49Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-code
---

## Decision and Rationale

Two independent Fable-model adversarial review rounds. Round 1 found two blockers: (1) spec.md bullet 375's flat prohibition on supervisor-handoff.md contradicted the same bullet's own mandate to preserve a migrated copy under research/; (2) bullet 381's citation-resolution rule was silently reversed (archive-stable-path -> live-path + update-at-archival) without stating the reversal or a rationale. Both fixed per maintainer decision (2026-08-14/15): keep archived copies under research/ with an explicit carve-out; proceed with live-path citations, stated explicitly as replacing the prior rule with rationale and design-record tail. Round 2 independently re-derived all counts and verbatim quotes from scratch and returned NO BLOCKERS. Accepting swept all 16 archive-form citations across the 9 Planning Lane bullets in spec.md to the live-path form, plus the matching either-filename wording fix in scenarios.md and non-functional-requirements.md.

## Resulting Changes

- spec.md
- scenarios.md
- non-functional-requirements.md

## Ratification Review

ratification_review: manual-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-15T06:05:00Z
verdict: NO BLOCKERS
proposal_stem: planning-lane-migration-citation-repair
content_digest: d25be024ad83c9d28bbb67d456858636122dc2618ab48d0b3450cd73b70a3d12
