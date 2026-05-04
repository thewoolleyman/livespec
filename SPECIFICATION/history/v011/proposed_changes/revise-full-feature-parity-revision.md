---
proposal: revise-full-feature-parity.md
decision: accept
---

## Decision and Rationale

All four proposals codify architecture-level revise-widening rules from PROPOSAL.md §"`revise`" lines 2405-2522, §"Versioning" lines 1734-1745 (post-v038), and §"Revision file format" lines 3107-3167 with no deviations. Proposal 1 widens the contracts.md table row that was deliberately left as a placeholder at v001 and rides the scenarios.md `--revise-input` → `--revise-json` typo fix along with it. Proposals 2 and 3 surface the wrapper's payload-validation contract and lifecycle/responsibility-separation contract in spec.md §"Sub-command lifecycle"; Proposal 3 explicitly cites v038 D1 (Statement B: every successful revise cuts a new version; byte-identical-to-prior spec files when no decision is `accept`/`modify`) since v038's PROPOSAL revision was authored to resolve a contradiction surfaced by this very widening cycle. Proposal 4 extends spec.md §"Proposed-change and revision file formats" with the per-decision-type required sections (`## Modifications` for modify; `## Resulting Changes` for accept/modify; `## Rejection Notes` for reject) — the rejection-flow audit-trail richness Plan Phase 7 line 3383 mandates. Mechanism details (specific file-system call sequencing, IOResult composition primitives, the `_write_and_move_per_decision` accumulator shape) remain implementation choices per the existing architecture-vs-mechanism discipline.
