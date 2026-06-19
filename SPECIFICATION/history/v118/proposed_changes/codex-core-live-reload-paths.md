---
topic: codex-core-live-reload-paths
author: codex-gpt-5
created_at: 2026-06-19T07:57:32Z
---

## Proposal: Core live-reload dogfooding paths use prose and wrappers

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Repair the Daily dogfooding path contract so it no longer claims core live-reloads `.claude-plugin/skills/<name>/SKILL.md`, because core intentionally ships no skill bindings.

### Motivation

The Codex dogfooding spec repair makes explicit that core has no `.claude-plugin/skills/` tree and that runtime bindings live outside core. The contracts.md Daily dogfooding path still says live edits to `.claude-plugin/skills/<name>/SKILL.md` reload from this repo, creating a direct contradiction.

### Proposed Changes

Update `SPECIFICATION/contracts.md` §"Daily dogfooding path" so maintainer live-reload mode says edits to core-owned `.claude-plugin/prose/<name>.md` and `.claude-plugin/scripts/...` are picked up via `/reload-plugins`. The section MUST say Claude Driver binding edits happen in the `livespec-driver-claude` repository, not in core. The section MUST NOT refer to `.claude-plugin/skills/<name>/SKILL.md` as a core live-edit path.
