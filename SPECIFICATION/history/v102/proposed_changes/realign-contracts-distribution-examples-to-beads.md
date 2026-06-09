---
topic: realign-contracts-distribution-examples-to-beads
author: claude-opus-4-8
created_at: 2026-06-09T04:00:33Z
---

## Proposal: Realign contracts.md distribution examples to livespec-impl-beads

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The livespec family has flipped its default impl backend from livespec-impl-plaintext to livespec-impl-beads. The §"Cross-repo coordination — pin-and-bump" prose and the illustrative .livespec.jsonc example block in contracts.md still name livespec-impl-plaintext (and a jsonl format value) as the impl-plugin exemplar, and the §"Three-layer orchestration architecture" pluggable-implementation example names livespec-impl-plaintext as the present-day impl. These are illustrative example bodies only; this proposal updates them so the spec's own examples mirror the now-active beads backend.

### Motivation

Phase 7 of the dolt-server beads-migration epic: bring livespec's own distribution/example prose into lockstep with the family's flip to the beads impl backend, so the spec does not advertise plaintext as the current exemplar while the repo's .livespec.jsonc, justfile ensure-plugins, and family tenants all run beads.

### Proposed Changes

Three prose/example-body edits, none of which add, remove, or rename any `## ` H2 heading:

1. In §"Cross-repo coordination — pin-and-bump" compat-key prose: change the impl-plugin compat-key example from `on the \`livespec-impl-plaintext\` key for impl-plugins` to `on the \`livespec-impl-beads\` key for impl-plugins`. The dev-tooling/runtime key clauses are unchanged.

2. In the illustrative `.livespec.jsonc` example block in that same section: change `"implementation": { "plugin": "livespec-impl-plaintext" },` to `"implementation": { "plugin": "livespec-impl-beads" },`, the section key `"livespec-impl-plaintext": {` to `"livespec-impl-beads": {`, and the `"format": "jsonl",` value to `"format": "beads",`. The `compat` block in that example is unchanged.

3. In §"Three-layer orchestration architecture" item 2 (Pluggable implementation): change `today \`livespec-impl-plaintext\`; tomorrow alternate implementations` to `today \`livespec-impl-beads\`; tomorrow alternate implementations`.
