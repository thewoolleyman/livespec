---
topic: subspec-livespec-self-containment-purge-proposal-citation
author: livespec-bootstrap-phase13
created_at: 2026-05-06T19:14:10Z
---

## Proposal: subspec-livespec-self-containment-purge-proposal-citation

### Target specification files

- SPECIFICATION/templates/livespec/contracts.md

### Summary

Drop the trailing `per the field-copy mapping at PROPOSAL.md lines 2232-2242.` citation from the livespec sub-spec's contracts.md §"Template-internal JSON contracts". The field-copy mapping is described in the preceding bullet enumeration; the external citation is vestigial and points at the now-archived PROPOSAL.md.

### Motivation

Phase 13 — codify live-spec authority. The livespec sub-spec must be self-contained on archive references like the main spec. This propose-change covers the single residual PROPOSAL.md citation in the sub-spec tree.

### Proposed Changes

In `SPECIFICATION/templates/livespec/contracts.md` line 10, drop the trailing ` per the field-copy mapping at PROPOSAL.md lines 2232-2242.` clause; the sentence ends with a period at `proposed_changes` fields.
