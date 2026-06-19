---
proposal: behavior-clause-scenario-link-contract.md
decision: accept
revised_at: 2026-06-19T19:27:56Z
author_human: E2E Test <e2e-test@example.com>
author_llm: guardrail-1a
---

## Decision and Rationale

Codifies the Guardrail #1a clause-to-scenario link mechanism already shipped on master (dev-tooling/spec_clauses.py + dev-tooling/checks/behavior_scenario_link.py). The clauses[] registry array (constraints.md), the always-wired always-running behavior_scenario_link check with its warn|fail severity lever (non-functional-requirements.md), and the §Self-application clause-link co-edit extension (spec.md) are accepted as written, with the acceptance scenario added to scenarios.md. The proposal complies with the rule it codifies: its four new behavior clauses each carry a clauses[] link to the new scenario in tests/heading-coverage.json.

## Resulting Changes

- spec.md
- constraints.md
- non-functional-requirements.md
- scenarios.md
- ../tests/heading-coverage.json
