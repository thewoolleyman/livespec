---
topic: e2e-harness-contract
author: unknown-llm
created_at: 2026-05-06T13:00:22Z
---

## Proposal: E2E harness contract

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Codify the end-to-end integration test harness contract covering fake_claude.py location, the LIVESPEC_E2E_HARNESS env var, the mock-tier interface, the seed-payload path convention, and the test structure.

### Motivation

Phase 9 E2E integration test implementation. The harness contract MUST be in SPECIFICATION/contracts.md before the implementation lands so the propose-change/revise discipline is maintained.

### Proposed Changes

Add a new ## E2E harness contract section to SPECIFICATION/contracts.md. The section MUST describe: (1) the mock at tests/e2e/fake_claude.py and the env var LIVESPEC_E2E_HARNESS=mock|real; (2) the mock-tier interface (one function per sub-command, keyword-only args, returns subprocess.CompletedProcess); (3) the seed-payload path convention (SPECIFICATION/spec.md, two path parts, compatible with doctor and prune-history); (4) the test structure (happy path, retry-on-exit-4, doctor-fail-then-fix, prune-history-noop); (5) Python-rule compliance notes (coverage exclusion for tests/e2e/).
