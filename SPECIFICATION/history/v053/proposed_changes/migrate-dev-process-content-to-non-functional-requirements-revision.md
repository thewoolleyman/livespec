---
proposal: migrate-dev-process-content-to-non-functional-requirements.md
decision: accept
revised_at: 2026-05-08T03:17:18Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Atomic migration moving 18 H2 sections (4 from spec.md, 14 from constraints.md) into the new SPECIFICATION/non-functional-requirements.md file, organized under a 5-section mirror structure (Boundary / Spec / Contracts / Constraints / Scenarios) matching the user-facing spec files. Sections demote from H2 to H3 when moved. Three sections rename to clarify their place under the new structure: 'Typechecker constraints (Phase 1 pin)' → 'Typechecker rule set'; 'Linter and formatter' → 'Linter rule set'; 'Code coverage' → 'Code coverage thresholds'; 'Enforcement suite' → 'Enforcement-suite invocation'. A new 'Toolchain pins' sub-section under Contracts consolidates the dev-toolchain tool-pin contract that was previously implicit across multiple Constraints sections. The 'Constraint scope' intro in constraints.md is rewritten to reference the NFR boundary explicitly. No content is added or removed beyond the boundary preamble, the Toolchain pins consolidation, and the small Constraint-scope rewrite — every moved section's body is preserved verbatim.

## Resulting Changes

- spec.md
- constraints.md
- non-functional-requirements.md
