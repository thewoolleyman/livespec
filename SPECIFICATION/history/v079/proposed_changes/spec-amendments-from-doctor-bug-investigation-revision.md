---
proposal: spec-amendments-from-doctor-bug-investigation.md
decision: accept
revised_at: 2026-05-26T05:59:02Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Both sub-proposals codify spec to match impl that already shipped. Sub-proposal 1a adds livespec_runtime as the 6th locked vendored lib so bare bin/doctor_static.py invocation no longer fails with ModuleNotFoundError, closing the silent contract gap against constraints.md's existing 'python3 >= 3.10 is the sole runtime dependency' promise (tracked under work-item li-tvi7lm). Sub-proposal 1b narrows the BCP14 static-phase rule to Shall only (the unambiguous case) and defers Must/Should/May to the LLM-driven phase where sentence-level context can disambiguate normative from descriptive English; this matches the narrowing already landed in commit 0c90289 under work-item li-mrtoei. No new ## headings are introduced; tests/heading-coverage.json does not require an update for this decision.

## Resulting Changes

- constraints.md
