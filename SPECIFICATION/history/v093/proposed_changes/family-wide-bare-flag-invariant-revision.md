---
proposal: family-wide-bare-flag-invariant.md
decision: accept
revised_at: 2026-05-27T22:47:00Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Accept as authored. Phase 1 of the family-wide bare-flag migration shipped the shared check at `livespec_dev_tooling.checks.primary_checkout_bare_flag_set` in `livespec-dev-tooling` v0.3.0; this PC writes the spec side so the discipline is enforceable across every livespec-governed sibling on the same `just check`/CI cadence. The amendments make the family-wide scope explicit in three load-bearing locations (`non-functional-requirements.md` §"Bare-flag enforcement", `non-functional-requirements.md` §"Bare-flag bootstrap procedure", `contracts.md` §"`primary-checkout-bare-flag-set`") without altering the underlying contract clauses or introducing new invariants — the rule was already universal-by-intent; the wording now matches the intent.

## Resulting Changes

- non-functional-requirements.md
- contracts.md
