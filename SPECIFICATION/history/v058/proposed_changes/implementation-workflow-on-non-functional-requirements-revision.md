---
proposal: implementation-workflow-on-non-functional-requirements.md
decision: accept
revised_at: 2026-05-08T08:10:15Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Authors the verbatim spec content for all 17 ### sub-sections plus the 1 Toolchain pins amendment that the propose-change file specified. Content is grounded in the architectural invariants the proposal lists; mechanism-level details (setup-beads internals, lock-file semantics, etc.) deliberately stay OUT of the spec per the architecture-vs-mechanism discipline. Open Brain is referenced as the canonical pattern source without inlining commit-pinned URLs. Redundant restatements of existing constraints (no force-push, no --no-verify, no bulk staging, atomic commits) are omitted — those live elsewhere in non-functional-requirements.md. Section structure follows the 5-section mirror exactly: ## Spec gets 1 sub-section (process intent); ## Contracts gets 3 new sub-sections (command surface, justfile namespace, gap-report shape) plus a Toolchain pins amendment (bd added; lefthook-no-npm constraint added); ## Constraints gets 4 new sub-sections (plugin layout, beads invariants, gap-tied closure verification, hook chaining); ## Scenarios gets 8 new ### Scenario sub-sections.

## Resulting Changes

- non-functional-requirements.md
