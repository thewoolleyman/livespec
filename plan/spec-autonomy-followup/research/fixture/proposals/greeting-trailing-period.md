---
topic: greeting-trailing-period
author: claude-opus-5-5 (spec-autonomy-followup fixture, session ce19c72a)
created_at: 2026-10-30T20:00:00Z
---

## Proposal: State that every greeting ends with exactly one period

### Target specification files

- SPECIFICATION/spec.md

### Summary

Add one sentence to §"Greeting" making the punctuation explicit.

### Motivation

Both greetings already end in a period; the rule is implicit. Stating it removes ambiguity for a name that itself ends in a period.

### Proposed Changes

In SPECIFICATION/spec.md §"Greeting", after the paragraph that begins "The service MUST answer a greeting request", append the paragraph, verbatim:

> Every greeting MUST end with exactly one period, even when the requested name itself ends with one.
