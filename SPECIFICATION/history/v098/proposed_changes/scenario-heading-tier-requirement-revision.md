---
proposal: scenario-heading-tier-requirement.md
decision: accept
revised_at: 2026-05-30T23:09:18Z
author_human: E2E Test <e2e-test@example.com>
author_llm: livespec-orchestrate
---

## Decision and Rationale

Accepted as-filed (epic li-scetier Phase 1). Adds a sub-rule to constraints.md §'Heading taxonomy' requiring that scenarios.md heading-coverage entries map to integration-tier-or-above tests (per-repo [tool.livespec_dev_tooling.scenario_tiers] allowlist or an explicit pytest.mark.integration marker). Verified the premise: livespec's 20 scenarios.md headings (## Happy-path…, ## Error path…) are NOT 'Scenario:'-prefixed, so the L233 skip does not apply — they are real registry entries the sub-rule binds. No new H2 (sub-rule within existing §), so no tests/heading-coverage.json co-edit. The heading_coverage check extension + any re-tiering of existing entries are the pre-authorized follow-on (li-scetlv check phase + Waves 14).

## Resulting Changes

- constraints.md
