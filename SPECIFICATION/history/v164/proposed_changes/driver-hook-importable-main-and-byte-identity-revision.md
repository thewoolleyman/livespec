---
proposal: driver-hook-importable-main-and-byte-identity.md
decision: accept
revised_at: 2026-07-13T08:55:12Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accepted per maintainer approval 2026-07-13 after an independent Fable NO-BLOCKERS review (replacement-target fidelity byte-exact on all 7 quotes + unique insert anchor; design-record fidelity; drift-sweep complete; no H2 change so no heading-coverage co-edit). Slice S1 (livespec-pxj9) of epic livespec-9z8h. The importable-main() discipline is stated at SHOULD (the design record's strength; keeps hook internals Driver-tunable per the section's closing paragraph) per the maintainer's conscious choice. Edit (d) also corrects a pre-existing misattribution: the live text named 'the Plugin-resolution concern' (registry concern #2 is Cross-harness plugin-resolution, unrelated to hook-body byte-identity); the amendment points at the consumer-side byte-identity Verifier in livespec-dev-tooling without naming the collision-prone 'No-shadow-ledger' registry member (that name is the planning-artifact discipline).

## Resulting Changes

- contracts.md
