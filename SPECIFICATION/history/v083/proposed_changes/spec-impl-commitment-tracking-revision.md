---
proposal: spec-impl-commitment-tracking.md
decision: accept
revised_at: 2026-05-26T08:07:09Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Accepted as filed (PC #4 of the Wave 1 cross-cutting safety-net ratification — structured commitment surface for spec→impl follow-ups). The four sub-proposals land together as a single file-level all-or-nothing acceptance per the revise-decision rule: (1) `spec_commitments.impl_followups[]` front-matter field in spec.md §"Proposed-change and revision file formats" with optional `supersedes[]` sub-field; (2) `unresolved-spec-commitment` doctor cross-boundary invariant in contracts.md §"Doctor cross-boundary invariants" (inserted after `depends_on-ref-wellformedness`); (3) impl-plugin work-item `spec_commitment_hint` field requirement added to contracts.md §"Implementation-plugin contract — the 10-skill surface" (inserted after `Backend-variability asymmetry`); (4) end-to-end threading via three new/extended subsections in contracts.md §"Sub-command wire contracts" (`propose-change payload validation` new subsection, `revise payload validation` extension) and §"`/livespec:next` spec-side thin-transport skill" → `Ranker semantics` extension. Meta-irony note: this PC declares its own impl follow-ups in prose ("Post-revise impl follow-ups" prose in the proposal bodies). The reviser does NOT retroactively add a `spec_commitments` front-matter block to this PC because the field has not yet been validated at the time this PC is being accepted (circular validation). The post-revise impl follow-ups are filed normally as work-items via the impl-plaintext `capture-work-item` skill in this same wrapper invocation's follow-up admin commit. No new `## ` H2 headings introduced in any spec file (only new `###` subsections within existing H2s), so tests/heading-coverage.json is not affected.

## Resulting Changes

- spec.md
- contracts.md
