---
topic: worktree-root-mise-trust
author: claude-opus-4-8
created_at: 2026-06-24T08:20:27Z
---

## Proposal: Worktree root and mise trust

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add a "Worktree root and mise trust" subsection codifying that every git worktree lives under a single per-user root (~/.worktrees/<repo>/<branch>), never as a peer of the workspace clones, and that just bootstrap idempotently registers that root in mise's trusted_config_paths so a freshly created worktree's .mise.toml auto-trusts and the first mise exec never stalls on a "config not trusted" prompt.

### Motivation

Worktrees were previously created as undefined peers under /data/projects, cluttering the workspace, and every fresh worktree failed its first mise exec on an untrusted-config prompt, wasting a tool round-trip. The functional changes already landed (bootstrap recipe + AGENTS.md in PR #549); this records the durable contract.

### Proposed Changes

In non-functional-requirements.md, add a new H3 subsection "### Worktree root and mise trust" immediately AFTER "### Commit-refuse hook bootstrap procedure" and BEFORE "### CI as a merge gate (branch protection)", stating the per-user worktree-root convention (~/.worktrees/<repo>/<branch>, never a workspace peer; fleet-wide-by-intent; orchestrator janitor worktrees out of scope) and the idempotent mise trusted_config_paths bootstrap registration that auto-trusts fresh worktrees. Only an H3 heading is added, so tests/heading-coverage.json (which tracks H2 headings) needs no co-edit.
