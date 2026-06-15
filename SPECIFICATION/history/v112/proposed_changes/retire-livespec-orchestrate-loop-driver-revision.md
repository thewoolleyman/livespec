---
proposal: retire-livespec-orchestrate-loop-driver.md
decision: accept
revised_at: 2026-06-15T01:40:55Z
author_human: E2E Test <e2e-test@example.com>
author_llm: livespec-a8bb-cutover
---

## Decision and Rationale

The user declared the W6 dark-factory cutover (2026-06-15). Accept as authored: the two passages flip from 'slated for retirement / interim working tooling' to RETIRED, naming the reference Beads/Dolt + Fabro orchestrator's Dispatcher as the successor that carries routine cross-repo work unattended. Relocate-never-drop verified: the skill's normative architectural disciplines already live in non-functional-requirements.md Orchestrator-internal Dispatcher guidance; its exact mechanics are mechanism-level detail that retires with the driver. The 'No required cross-repo loop driver' principle is preserved verbatim.

## Resulting Changes

- spec.md
- non-functional-requirements.md
