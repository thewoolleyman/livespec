---
proposal: append-only-store-legibility-and-merge-safe-reduction.md
decision: reject
revised_at: 2026-06-09T22:34:05Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Formally rejected per decision-record item 6 of the contract-and-reference-implementations-phase-1 proposed change (user-decided 2026-06-09), accepted in this same revise pass. Under the re-steered contract the work-items and memos stores are the orchestrator's private Ledger: core's contract never reads them, so order-independent reduction, record self-identification, the read-path-only-via-query-surface doctrine, a canonical livespec_runtime reducer, and the no-divergent-heads / no-raw-store-read doctor invariants have no home in core's SPECIFICATION — every contracts.md section this proposal targets (Backend-variability asymmetry, Thin-transport skill doctrine, the 10-skill surface, the semantic doctor cross-boundary invariants) is deleted by the successor. The content migrates rather than disappears: the append-store disciplines land in the git-jsonl reference orchestrator's own SPECIFICATION as Phase-4 work, where the store they govern actually lives. The front-matter spec_commitments declarations do not activate on rejection; they become the git-jsonl orchestrator's Phase-4 backlog instead.

## Rejection Notes

Rejection rationale captured in §"Decision and Rationale" above. Future re-proposal would need to address that critique.
