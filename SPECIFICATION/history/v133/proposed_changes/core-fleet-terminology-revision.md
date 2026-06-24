---
proposal: core-fleet-terminology.md
decision: accept
revised_at: 2026-06-24T01:16:59Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: gpt-5-codex
---

## Decision and Rationale

The accepted change establishes `fleet` as the active core specification term
for livespec's governed repo set, shared infrastructure, shared secrets,
shared operating discipline, and member tenants. It keeps the functional
meaning unchanged while aligning core's upstream vocabulary with the fleet
manifest and fleet-conformance model.

The pass is terminology-only. It also renames one H2 heading from `Family
agent-instruction core` to `Fleet agent-instruction core`;
`tests/heading-coverage.json` is updated with the same heading rename.

## Resulting Changes

- spec.md
- contracts.md
- non-functional-requirements.md
