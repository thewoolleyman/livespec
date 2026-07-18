---
proposal: rop-enforcement-fleet-policy.md
decision: accept
revised_at: 2026-07-18T05:25:13Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accepted per maintainer decisions 2026-07-18 (full ROP everywhere; add ruff BLE + backfill fleet) after an independent Fable-model NO-BLOCKERS review: all four replace-target anchors byte-identical, design-record fidelity to plan/rop-sweep-fleet-policy/handoff.md Parts B/C + Decision 1, drift-sweep clean (no conflict with §"Supervisor discipline" — core ships no hooks; contracts.md fail-open discipline grounds the hook-boundary clause), no H2 heading change so no tests/heading-coverage.json co-edit. Codifies the observability pass-through-tap rule, adds BLE to the enumerated linter set (27->28), and states the full-ROP fleet+adopter-wide bar.

## Resulting Changes

- non-functional-requirements.md
