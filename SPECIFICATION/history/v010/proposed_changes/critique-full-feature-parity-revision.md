---
proposal: critique-full-feature-parity.md
decision: accept
---

## Decision and Rationale

All three proposals codify architecture-level critique-widening rules from PROPOSAL.md §"`critique`" lines 2350-2403 with no deviations. Proposal 1 widens the contracts.md table row that was deliberately left as a placeholder at v001. Proposals 2 and 3 surface the wrapper's payload-validation contract and internal-delegation contract in spec.md §"Sub-command lifecycle"; the actual algorithm details (canonicalization, reserve-suffix composition, slug transformation, collision disambiguation) are already covered by the v009 revision and are referenced rather than duplicated, per the architecture-vs-mechanism discipline.
