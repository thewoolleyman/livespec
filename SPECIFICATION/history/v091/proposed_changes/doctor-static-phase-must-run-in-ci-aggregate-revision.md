---
proposal: doctor-static-phase-must-run-in-ci-aggregate.md
decision: accept
revised_at: 2026-05-27T13:59:36Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Accept as authored. Closes a real gap surfaced 2026-05-27 where 4 pre-existing doctor-static fail findings sat undetected on master (constraints.md typos, v081 historical write-loss, copier-update-drift self-coverage gap). The `check-doctor-static` target makes the deterministic phase mechanically gated alongside ruff/pyright/pytest. LLM-driven phases stay interactive-only per their nondeterministic nature.

## Resulting Changes

- non-functional-requirements.md
