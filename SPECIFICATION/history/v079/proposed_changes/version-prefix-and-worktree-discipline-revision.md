---
proposal: version-prefix-and-worktree-discipline.md
decision: modify
revised_at: 2026-05-26T05:59:02Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Land both rule bodies as proposed, but as ### subsections under the existing ## Constraints top-level heading rather than as two new ## sections. non-functional-requirements.md's own §Boundary explicitly mandates exactly five top-level ## sections (Boundary / Spec / Contracts / Constraints / Scenarios) mirroring the user-facing spec; adding new ## peers would violate that invariant. The proposal text itself flagged this as an acceptable alternative ('or fold into an existing contributor-conventions section if one fits better'). Both rules are architectural authoring invariants on contributor-facing concerns, which matches the §Boundary decision rule for ## Constraints. The future doctor LLM-subjective check for bare v\d+\.\d+\.\d+ literals and the future static check for master-direct uncommitted spec-tree edits both remain as future-tense aspirations in the landed prose.

## Modifications

Lifted both proposed ## sections to ### subsections under ## Constraints. ### Prose conventions inserted after ### Comment discipline (both are authoring discipline). ### Workflow discipline — spec-side changes inserted after ### Commit and merge discipline (both are workflow). Body content of both rules is preserved verbatim from the proposal.

## Resulting Changes

- non-functional-requirements.md
