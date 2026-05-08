---
topic: migrate-dev-process-content-to-non-functional-requirements
author: claude-opus-4-7
created_at: 2026-05-08T03:17:06Z
---

## Proposal: Migrate dev-process content from spec.md and constraints.md to non-functional-requirements.md

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/constraints.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Atomic migration of 18 dev-process H2 sections (4 from spec.md, 14 from constraints.md) into the new SPECIFICATION/non-functional-requirements.md file. The new file MUST adopt a 5-section mirror structure (Boundary / Spec / Contracts / Constraints / Scenarios) matching the user-facing spec files, so contributors and agents apply the same categorization rule when landing new content. No content is added or removed beyond a boundary preamble, a new Toolchain pins sub-section consolidating dev-toolchain pin contracts, and a small NFR-pointer paragraph appended to the Constraint scope section in constraints.md. Every moved section's body MUST be preserved verbatim (with H2 headings demoted to H3 and existing H3+ headings demoted one level accordingly).

### Motivation

Today the user-facing spec files are mixed with dev-process content. spec.md interleaves user-facing intent (project intent, sub-command lifecycle, versioning, lifecycle, prior art) with contributor-facing process material (testing approach, TDD discipline, developer-tooling layout, definition of done). constraints.md mixes constraints whose violation an end user could observe (runtime versions, exit-code contract, structured-logging schema, vendored-library discipline, NLSpec discipline) with contributor-only rules (package layout, pure/IO boundary, ROP composition, supervisor discipline, typechecker rule set, linter rule set, comment discipline, complexity thresholds, code coverage, keyword-only arguments, structural pattern matching, enforcement suite, CLAUDE.md coverage, self-application bootstrap exception). The v009 sub-spec change introduced non-functional-requirements.md as the canonical home for contributor-facing invariants, but the main SPECIFICATION/ tree's content has not yet been migrated. The mirror structure (Spec / Contracts / Constraints / Scenarios) was chosen because it gives agents the same decision rule they already use for the user-facing files: 'is this intent/behavior, an external interface, an architectural invariant, or a workflow scenario?' Three sections rename to clarify their place under the new structure: 'Typechecker constraints (Phase 1 pin)' becomes 'Typechecker rule set' under Constraints; 'Linter and formatter' becomes 'Linter rule set' under Constraints; 'Code coverage' becomes 'Code coverage thresholds' under Constraints; 'Enforcement suite' becomes 'Enforcement-suite invocation' under Contracts. A new Toolchain pins sub-section under Contracts consolidates the dev-toolchain pin contract that was previously implicit across multiple Constraints sections.

### Proposed Changes

The migration MUST be atomic: every moved section MUST appear in non-functional-requirements.md AND MUST be removed from its original location in the same revise. The new file's structure MUST be:

```
# Non-functional requirements — `livespec`

## Boundary
[preamble defining the 5-section mirror + the boundary against spec.md/contracts.md/constraints.md/scenarios.md]

## Spec
### Test-Driven Development discipline (from spec.md, demoted)
### Testing approach (from spec.md, demoted)
### Definition of Done (from spec.md, demoted)
### Self-application bootstrap exception (from constraints.md, demoted)

## Contracts
### Toolchain pins (NEW abstraction; consolidates dev-toolchain pins)
### Enforcement-suite invocation (from constraints.md 'Enforcement suite', renamed and demoted)

## Constraints
### Developer-tooling layout (from spec.md, demoted)
### Package layout (from constraints.md, demoted)
### Pure / IO boundary (from constraints.md, demoted)
### ROP composition (from constraints.md, demoted)
### Supervisor discipline (from constraints.md, demoted)
### Typechecker rule set (from constraints.md 'Typechecker constraints (Phase 1 pin)', renamed and demoted)
### Linter rule set (from constraints.md 'Linter and formatter', renamed and demoted)
### Comment discipline (from constraints.md, demoted)
### Complexity thresholds (from constraints.md, demoted)
### Code coverage thresholds (from constraints.md 'Code coverage', renamed and demoted)
### Keyword-only arguments (from constraints.md, demoted)
### Structural pattern matching (from constraints.md, demoted)
### CLAUDE.md coverage (from constraints.md, demoted)

## Scenarios
[empty initially; section header lands so the mirror is complete]
```

All moved section bodies MUST be preserved verbatim. Heading levels MUST demote uniformly (H2→H3, H3→H4, etc.) within each moved block. The four renames listed above MUST apply only to the section's H2/H3 heading line, not to references in body prose.

The Constraint scope section in constraints.md MUST receive a new closing paragraph pointing readers at non-functional-requirements.md for contributor-facing invariants. Specifically: after the existing 'Tests under <repo-root>/tests/...' paragraph, the spec MUST add: 'Constraints in this file MUST be those whose violation an end user could observe — runtime versions, exit-code contracts, dependency envelopes, structured-logging schemas, vendored-library discipline, and NLSpec discipline (BCP14 + heading taxonomy). Contributor-facing invariants — code patterns, layout rules, coverage thresholds, linter/typechecker rule sets, and dev-toolchain pins — MUST live in non-functional-requirements.md instead.'

After migration, spec.md MUST contain exactly 13 H2 sections (the original 17 minus the 4 moved), constraints.md MUST contain exactly 10 H2 sections (the original 24 minus the 14 moved), and non-functional-requirements.md MUST contain exactly 5 H2 sections (Boundary, Spec, Contracts, Constraints, Scenarios).

Companion changes that MUST land in the same PR (outside this propose-change scope):
- tests/heading-coverage.json MUST drop the ~17 orphan entries for moved H2 sections and gain 5 new entries for the new H2 headings in non-functional-requirements.md.
- No code surface needs updating (heading_coverage.py and the seed prompt were already widened in the v009 PR; the dev-tooling/checks/template_files_present.py check is a Phase-3 stub that does not enforce file-set presence).

The Toolchain pins sub-section's prose MUST enumerate the contributor-facing tools (mise, uv, just, lefthook, pytest + plugins, hypothesis + jsonschema, ruff, pyright, mutmut), state their pinning mechanism (.mise.toml for non-Python binaries; pyproject.toml [dependency-groups.dev] + uv.lock for Python deps), describe each tool's role, cross-reference the rule sets in Constraints (### Typechecker rule set, ### Linter rule set), and reference the dev-tooling/checks/no_direct_tool_invocation.py AST check that enforces task-runner indirection in lefthook.yml and CI workflows.

The Boundary preamble MUST include both a description of the 5-section mirror (so future contributors know which sub-section to land new material in) AND the explicit boundary against the user-facing spec files (so contributors do not land user-facing material in non-functional-requirements.md by mistake).
