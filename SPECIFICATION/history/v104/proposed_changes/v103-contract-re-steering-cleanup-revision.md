---
proposal: v103-contract-re-steering-cleanup.md
decision: accept
revised_at: 2026-06-09T23:39:18Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Accepted as drafted. All six proposals are mechanical consequences of the v103 contract + reference implementations re-steering, drafted from the post-v103 doctor pass: the CLI end-to-end harness contract is re-scoped to core's spec-side surface (orchestrator e2e coverage is owned by each orchestrator's own repository; the cross-boundary seam is exercised only through the three config-named orchestrator CLIs); the two compat-block obligations are restated in pointer form against the family/dev-tooling coordination surface; core's vendoring mandate for the livespec_runtime cross-repo machinery is dropped (the surface is orchestrator-private with no core consumer remaining); next joins the config-named, individually-overridable spec-side CLI set covered by config-named-cli-callability; the legacy project-local livespec-implementation sections and the work-item-machinery scenarios are retired from non-functional-requirements.md (the core-surface Codex scenarios are retained); and four near-miss section references are corrected, with the one genuinely cross-repo citation restated in the allowlist form that constraints.md requires (the matching external_references entry lands in .livespec.jsonc alongside this revision). No heading-coverage co-edit is required: the H2 sets of all three touched files are unchanged.

## Resulting Changes

- contracts.md
- constraints.md
- non-functional-requirements.md
