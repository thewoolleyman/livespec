---
topic: fix-next-thin-transport-citation
author: unknown-llm
created_at: 2026-06-26T02:02:10Z
---

## Proposal: Fix stale cross-reference to the /livespec:next contracts heading

### Target specification files

- SPECIFICATION/spec.md

### Summary

spec.md cites contracts.md via the section form using the OLD heading text 'thin-transport skill'; the heading was renamed to 'thin-transport binding'. Update the citation so it resolves under the doctor-no-cross-spec-reference check.

### Motivation

The doctor-no-cross-spec-reference static check surfaced a stale same-tree section citation: spec.md Terminology cites a contracts.md heading by its former name. Heading renames MUST be mirrored in citing files.

### Proposed Changes

In SPECIFICATION/spec.md, the Terminology entry for 'Durable-pending' MUST cite the contracts.md heading by its current name 'spec-side thin-transport binding' (not the former 'spec-side thin-transport skill').
