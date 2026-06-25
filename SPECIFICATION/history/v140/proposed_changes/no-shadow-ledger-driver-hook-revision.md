---
proposal: no-shadow-ledger-driver-hook.md
decision: accept
revised_at: 2026-06-25T13:53:10Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accepting increment 3b's core slice: adds the no-shadow-ledger WARN-only Stop hook as a required cross-Driver bundle surface (single-sourced, byte-identical body + thin per-runtime adapters), realizing non-functional-requirements.md §"Planning Lane guidance" → "No shadow ledger". Required because §"Driver-shipped hooks" mandates a propose-change to add a hook to a Driver bundle. No H2 heading change (heading-coverage unaffected); no scenario added, consistent with the existing hook surfaces.

## Resulting Changes

- contracts.md
