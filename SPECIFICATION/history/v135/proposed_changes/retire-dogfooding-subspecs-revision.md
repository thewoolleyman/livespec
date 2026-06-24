---
proposal: retire-dogfooding-subspecs.md
decision: accept
revised_at: 2026-06-24T12:39:44Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accept the retirement of the two dogfooding sub-spec trees while preserving the multi-tree sub_specs/--spec-target feature. The unique template-internal contracts that lived only in the sub-specs are relocated into a single new '## Built-in template contracts' section in contracts.md; the few illustrative references to livespec's own two trees in the structural-mechanism section, README, self-application rule, and the happy-path doctor scenario are genericized so the cross-tree feature survives without asserting livespec's own current state. tests/heading-coverage.json is co-edited in the same payload: one TODO entry added for the new contracts.md heading and the 46 sub-spec-rooted entries removed (their tree roots no longer exist).

## Resulting Changes

- contracts.md
- README.md
- spec.md
- scenarios.md
- ../tests/heading-coverage.json
