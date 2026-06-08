---
proposal: scope-copier-template-workflow-coverage-to-consumers.md
decision: accept
revised_at: 2026-06-08T00:38:58Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Approved architectural decision (work-item li-k4gio6): scope the copier-template-workflow-coverage doctor invariant to copier-template consumers only, detected by a `.copier-answers.yml` file at the project root. Non-consumer repos (livespec itself, livespec-dev-tooling, livespec-runtime, dolt-server) legitimately carry a different workflow set and were never generated from the impl-plugin copier template; the unconditional check fires false fails against them. Gating on `.copier-answers.yml` makes the invariant correct for them (emit a non-failing `skipped` finding without inspecting `.github/workflows/`) while preserving full enforcement against `livespec-impl-*` consumers. The required-file list is unchanged.

## Resulting Changes

- contracts.md
