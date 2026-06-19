---
proposal: orchestrator-grooming-guidance.md
decision: accept
revised_at: 2026-06-19T07:55:43Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accepted as-written per maintainer authorization. Graduates the repo-agnostic, human-led grooming PATTERN from research/dark-factory-operability/work-breakdown.md into non-functional-requirements.md as a NON-normative #### subsection beside the existing Orchestrator-internal Dispatcher guidance, under ### Implementation plugin ecosystem. It explicitly adds NO new core skill, CLI, or doctor invariant; the concrete realization belongs to the reference orchestrator's own spec. Structurally an H4 only (no ## heading added/renamed/removed), so tests/heading-coverage.json is unaffected. The documented Open questions paragraph is preserved verbatim and left open, not resolved.

## Resulting Changes

- non-functional-requirements.md
