---
topic: unknown-name-wording
author: claude-opus-5-5 (spec-autonomy-followup fixture, session ce19c72a)
created_at: 2026-10-30T20:00:00Z
decision_policy: manual
---

## Proposal: Clarify that an empty name counts as no name

### Target specification files

- SPECIFICATION/spec.md

### Summary

Treat an empty or whitespace-only `name` the same as an absent one.

### Motivation

The current rule only covers an absent name.

### Proposed Changes

In SPECIFICATION/spec.md §"Unknown name", replace "When no name is supplied" with "When no name, an empty name, or a whitespace-only name is supplied".
