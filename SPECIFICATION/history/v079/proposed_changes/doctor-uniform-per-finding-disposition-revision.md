---
proposal: doctor-uniform-per-finding-disposition.md
decision: accept
revised_at: 2026-05-26T05:59:02Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Lands the new ## Doctor per-finding disposition dialogue section in contracts.md between ## Per-sub-spec doctor parameterization and ## Doctor cross-boundary invariants as proposed. The five-option menu (fix-now, capture-as-work-item, propose-change, defer, dismiss) with capture-as-work-item as the always-available universal fallback satisfies the 'nothing dropped on the floor' guarantee that surfaced from a real /livespec:doctor session. Cross-plugin invocation to the active impl-plugin's capture-work-item skill is consistent with the existing process-memos → /livespec:propose-change cross-boundary handoff pattern. The dialogue running BEFORE static-phase fail abort preserves the existing rule that LLM-driven check generation MUST NOT run after a static fail. Downstream .claude-plugin/skills/doctor/SKILL.md regeneration tracks as a separate impl follow-up work-item (resulting_files[] is spec-target-relative and cannot reach skill files anyway). tests/heading-coverage.json gets a TODO entry for the new ## heading.

## Resulting Changes

- contracts.md
- ../tests/heading-coverage.json
