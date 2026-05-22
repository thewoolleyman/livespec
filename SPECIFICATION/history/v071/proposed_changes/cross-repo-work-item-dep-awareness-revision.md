---
proposal: cross-repo-work-item-dep-awareness.md
decision: modify
revised_at: 2026-05-22T03:27:44Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

All four findings (work-item metadata fields, resolver skill, doctor structural invariant, .livespec.jsonc cross_repo_targets block) land with corrections from the sibling -critique proposal integrated in place. The corrections preserve the contract pin from §"/livespec:next spec-side thin-transport skill" line forbidding cross-side reads in `next`: the resolver is the SOLE place that crosses repos; doctor stays read-only and structural; impl-side `next` reads only local metadata.

## Modifications

Three corrections integrated relative to the original proposal text: (1) HIGH — dropped the `blocked` urgency band alternative from the work-item metadata finding; specified single deterministic disposition: blocked work-items MUST be excluded from candidates list entirely (urgency enum [high, medium, low] unchanged, consistent with the parallel ranked-candidates pagination proposal). (2) MEDIUM — corrected the cross_repo_targets example: livespec-core plugin is `livespec-impl-plaintext` (the impl-plugin exposing list-work-items), not `livespec` (the spec-side plugin). Added a clarifying sentence after the example: `plugin` field MUST always name the impl-plugin, never the spec-side plugin. (3) LOW — removed the parenthetical reference to memory file `feedback_user_extensions_minimal_requirements.md` from the resolver skill finding; restated the underlying principle (cross-plugin contract MUST remain agnostic to per-implementation field additions) in spec-native terms.

## Resulting Changes

- contracts.md
- ../tests/heading-coverage.json
