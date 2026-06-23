---
topic: codex-skills-picker-discoverability
author: gpt-5-codex
created_at: 2026-06-23T09:59:00Z
---

## Proposal: Require Codex skills picker discoverability proof

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Codex compatibility proof already requires an installed plugin entry plus a
`codex exec` operation path through the Driver and core prose. Add the missing
human-discoverability requirement: claims about `/skills` discovery must verify
the supported Codex TUI picker path, search by the short skill name, and confirm
the owning plugin is rendered as context.

### Motivation

The previous acceptance only proved model-visible and `codex exec` name
selection. It did not exercise the human `/skills` picker path where operators
search for `orchestrate` and see a row such as
`orchestrate (livespec-orchestrator-beads-fabro)`.

### Proposed Changes

In non-functional-requirements.md, extend Codex compatibility verification so a
separate human-discoverability claim MUST drive `/skills` -> `List skills` (or
an official noninteractive equivalent if Codex exposes one), search by short
skill name, and verify plugin context rendering. Also clarify that core or an
orchestrator may claim human `/skills` discoverability only after the real
picker or official equivalent proves that display contract. No H2/H3 heading is
added, removed, or renamed, so tests/heading-coverage.json is untouched.
