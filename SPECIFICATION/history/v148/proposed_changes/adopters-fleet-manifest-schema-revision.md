---
proposal: adopters-fleet-manifest-schema.md
decision: accept
revised_at: 2026-06-26T05:26:13Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Adopter-enablement machinery (zs22.7.5): define the manifest's fleet + adopters arrays in the contract, rename the legacy members array to fleet per the locked design and the family->fleet convergence, and add the Adopters paragraph (profile/posture). No adopter registered; the dev-tooling parser is migrated first to accept both fleet and members keys.

## Resulting Changes

- non-functional-requirements.md
