---
proposal: remove-mise-bd-pin.md
decision: accept
revised_at: 2026-07-30T09:11:32Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: codex-gpt-5
---

## Decision and Rationale

The current statement is contradicted by the repository's actual configuration and permits a mise shim to shadow the lifecycle guard. The replacement makes the host guard the supported entry point and prohibits project-local Beads declarations.

## Resulting Changes

- non-functional-requirements.md
