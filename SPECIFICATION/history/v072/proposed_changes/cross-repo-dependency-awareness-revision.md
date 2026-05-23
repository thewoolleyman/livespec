---
proposal: cross-repo-dependency-awareness.md
decision: modify
revised_at: 2026-05-23T16:39:07Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Accept all three sub-proposals (`cross-repo-dependency-awareness-h2-and-runtime-library-contract`, `doctor-invariants-rename-and-extend-for-typed-depends-on`, `impl-plugin-contract-rename-blocked-by-and-add-cleanup-invariants`) with targeted modifications applied to each. Sub-proposal 1: replaced the proposed `#### livespec-runtime library contract` subsection (which ~90% duplicated the existing `## Shared runtime — livespec-runtime` H2 — governance, semver, dependency-consumption shape, Python floor) with a tight `### livespec_runtime.cross_repo contract surface` subsection that only names the cross-repo-specific public API (`DependsOnEntry` union, `CrossRepoManifest` dataclass, `RefStatus` enum, `resolve_ref` entry point) plus module structure, deferring library-level concerns to that existing H2; stripped 3 work-item-ID inline references (`per li-aclzfe`, `per li-f5wmjr` ×2) per the spec-is-for-contracts-not-tracking discipline; promoted the proposed `####` (H4) subsections to `###` (H3) so heading depth is uniform with the rest of contracts.md. Sub-proposal 2: tightened the `no-stalled-epic` extension wording to walk the epic's OWN `depends_on` array (matches the existing structural concern) rather than the sub-tasks' depends_on as the proposal's wording suggested; fixed the lingering `no-orphan-blocker` reference inside `no-stalled-epic`'s explanatory text that the proposal forgot to update. Sub-proposal 3: softened the speculative `livespec_runtime.cleanup` module reference to `a livespec_runtime helper module if a future version provides one` to avoid pre-committing to a module name that isn't yet specified.

## Modifications

Sub-proposal 1: (a) replaced verbose duplicating `#### livespec-runtime library contract` subsection with terser `### livespec_runtime.cross_repo contract surface` listing exports + module structure + cross-reference; (b) stripped 3 work-item-ID inline references (`per li-aclzfe`, `per li-f5wmjr` ×2); (c) converted proposed H4 subsections to H3 for uniformity. Sub-proposal 2: (a) `no-stalled-epic` extension walks the epic's own `depends_on` array (not the sub-tasks' depends_on); (b) updated the residual `no-orphan-blocker` cross-reference inside `no-stalled-epic` to `no-orphan-dependency`. Sub-proposal 3: softened `livespec_runtime.cleanup` forward reference to a non-committal `livespec_runtime helper module if a future version provides one`. Also added a paired tests/heading-coverage.json entry for the new H2 `## Cross-repo dependency awareness` per CLAUDE.md's revise co-edit discipline.

## Resulting Changes

- contracts.md
- ../tests/heading-coverage.json
