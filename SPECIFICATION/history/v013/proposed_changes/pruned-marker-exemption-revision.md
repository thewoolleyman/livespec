---
proposal: pruned-marker-exemption.md
decision: accept
revised_at: 2026-05-05T03:03:26Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: Claude Opus 4.7 (1M context)
---

## Decision and Rationale

Codify the pruned-marker exemption per PROPOSAL.md lines 2777-2785. The exemption is the consumer-side counterpart to the producer-side prune-history mechanic already codified in spec.md §Sub-command lifecycle. Without this exemption surfaced into SPECIFICATION/, the prune-history round-trip pre-step doctor check would cascade on its own marker output, blocking cycle 6.c.7's Green amend. Architecture-vs-mechanism discipline leaves the static-check implementation algorithm to the doctor-check author.

## Resulting Changes

- spec.md
