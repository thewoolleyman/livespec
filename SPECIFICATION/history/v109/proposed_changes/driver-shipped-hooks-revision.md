---
proposal: driver-shipped-hooks.md
decision: accept
revised_at: 2026-06-12T07:43:19Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Accepted as proposed (decision pre-made by the user on work-item livespec-7nmc). The section codifies, verbatim-verified against livespec-driver-claude origin/master (.claude-plugin/hooks/hooks.json, block-auto-memory.sh, warn-plan-persistence.sh; Driver PRs #4/#5 merged 2026-06-11), what the Driver actually ships: the PreToolUse auto-memory redirect with its implementation.plugin config gate, the Stop plan-persistence WARN hook with its warn-only posture, and the shared fail-open discipline. No existing normative text conflicts: contracts.md §"Plugin distribution" carries the Driver-binding packaging facts this subsection extends, and non-functional-requirements.md §"Hook chaining" governs GIT hooks, not agent-runtime plugin hooks. No H2 headings are added, changed, or removed, so tests/heading-coverage.json is unaffected.

## Resulting Changes

- contracts.md
