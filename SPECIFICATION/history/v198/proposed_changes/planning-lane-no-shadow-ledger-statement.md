---
topic: planning-lane-no-shadow-ledger-statement
author: gpt-5-codex
created_at: 2026-08-05T22:17:59Z
---

## Proposal: Restore the no-shadow-ledger canonical statement

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Append one sentence to the Planning Lane guidance's Ledger-held planning state paragraph so the no-shadow-ledger rule is stated explicitly where existing references point.

### Motivation

Doctor finding b1 observed that v197 left the rule only entailed by ledger-held state and non-derivable-only handoff entries, while the Conformance Pattern registry and Stop no-shadow-ledger hook contract still cite Planning Lane guidance as the rule's home.

### Proposed Changes

Append this sentence to SPECIFICATION/non-functional-requirements.md under #### Planning Lane guidance, in the **Ledger-held planning state.** paragraph:

Checklist items in any planning artifact are session-local steps or pointers to real ledger ids, never a parallel work queue that shadows the ledger.
