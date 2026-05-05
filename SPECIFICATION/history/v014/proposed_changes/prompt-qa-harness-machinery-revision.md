---
proposal: prompt-qa-harness-machinery.md
decision: accept
revised_at: 2026-05-05T21:58:19Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: Claude Opus 4.7 (1M context)
---

## Decision and Rationale

Accept both proposals as drafted. P1 codifies the prompt-QA tier in spec.md §"Testing approach" (test-pyramid widening per PROPOSAL.md §"Test pyramid" lines 3549-3567 and §"Prompt-QA tier" lines 3987-4047). P2 codifies the harness contract in contracts.md (file location, fixture format, per-template assertion-registry mechanism, harness behavior, Python-rule compliance). Both proposals stay within the PROPOSAL-authorized prompt-QA scope; cascading-impact scan against PROPOSAL.md and the bootstrap plan was clean (`_harness.py` matches plan line 3672 verbatim; the new `_fixture.schema.json` and `_assertions.py` names have no prior conflicting text). Implementation lands across subsequent Red→Green cycles per the v035 D5a / v033 D5b spec-then-implementation precedent.

## Resulting Changes

- spec.md
- contracts.md
