---
proposal: recast-layer3-standalone-orchestrate-plugin.md
decision: reject
revised_at: 2026-06-09T22:34:05Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Formally rejected per decision-record item 5 of the contract-and-reference-implementations-phase-1 proposed change (user-decided 2026-06-09), which is processed and accepted in this same revise pass and is the named successor for this proposal's surviving content. The re-steering retires the three-layer architecture this proposal amends: the orchestration loop moves inside the orchestrator, so there is no Layer 3 left to be livespec-resident or standalone-plugin, and the distribution debate this proposal settles dissolves. The surviving content is folded forward, not lost: the orchestrator-consumes-only-the-published-surface invariant, the dispatchable-from-config property, and per-repo addressability land in the successor's contracts.md changes; the loop discipline relocates as orchestrator-internal Dispatcher guidance in non-functional-requirements.md; the dead-end Layer-3 discoverability nudge is resolved by removing the nudge entirely. For this proposal to have been acceptable instead, the three-layer architecture would have had to remain core contract surface — the 2026-06-09 re-steering decided otherwise.

## Rejection Notes

Rejection rationale captured in §"Decision and Rationale" above. Future re-proposal would need to address that critique.
