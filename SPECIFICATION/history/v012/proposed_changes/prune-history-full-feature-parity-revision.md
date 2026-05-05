---
proposal: prune-history-full-feature-parity.md
decision: accept
revised_at: 2026-05-05T00:26:16Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: unknown-llm
---

## Decision and Rationale

All three proposals codify architecture-level prune-history rules from PROPOSAL.md §"Pruning history" lines 1827-1872, §"`prune-history`" lines 2532-2544, §"Pre-step skip control" lines 811-822, and §"Spec-target selection contract" lines 363-366 with no contract extensions. Proposal 1 widens the contracts.md table row deliberately left as a placeholder at v001; the new row enumerates the PROPOSAL-authorized flag set (no `--spec-target` per the v018 Q1 spec-target enumeration). Proposal 2 codifies the prune-history wrapper's lifecycle and responsibility separation in spec.md §"Sub-command lifecycle" (skill-prose vs wrapper split; deterministic file-shaping; 5-step prune mechanic; carry-forward first; no-metadata invariant; no-op short-circuits). Proposal 3 codifies the pre-step skip control mechanism shared by every pre-step-having wrapper. The architecture-vs-mechanism discipline at constraints.md §"Code style" leaves implementation choices (the specific IOResult composition shape; the file-system call sequencing; the no-op-detection helper layout) to sub-step 6.c.

## Resulting Changes

- contracts.md
- spec.md
