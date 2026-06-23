---
topic: livespec-fleet-manifest-hidden-name
author: gpt-5-codex
created_at: 2026-06-23T21:08:00Z
---

## Proposal: Rename the fleet manifest to a livespec dotfile

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Rename the core fleet membership manifest from `fleet-manifest.jsonc` to
`.livespec-fleet-manifest.jsonc` in the fleet membership contract.

### Motivation

The hidden livespec-prefixed filename makes the file's ownership and purpose
self-explanatory and keeps it near the other livespec configuration dotfiles in
filesystem listings.

### Proposed Changes

In `non-functional-requirements.md`, update the fleet membership contract's
manifest filename from `fleet-manifest.jsonc` to
`.livespec-fleet-manifest.jsonc`. No H2/H3 heading is added, removed, or
renamed, so `tests/heading-coverage.json` is untouched.
