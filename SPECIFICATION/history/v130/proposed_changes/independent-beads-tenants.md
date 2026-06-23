---
topic: independent-beads-tenants
author: claude-opus-4-8
created_at: 2026-06-23T02:30:48Z
---

## Proposal: Permit independent (non-family) beads tenants

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Relax the hard-coded family-only beads-access model so a tenant MAY be INDEPENDENT (non-family): it injects the bare BEADS_DOLT_PASSWORD via its OWN with-<project>-env.sh wrapper + its own 1Password Environment + its own tenant password, while family tenants keep sharing the family password via with-livespec-env.sh by explicit choice. Backward-compatible: family tenants are unchanged. Real isolation still comes from the per-tenant SQL user + DB-scoped grant.

### Motivation

Today the beads-access model is hard-coded to the livespec FAMILY: every beads tenant must share ONE family Dolt password injected by the single wrapper with-livespec-env.sh. We want to permit independent (non-family) tenants without weakening isolation, which already comes from the per-tenant SQL user + DB-scoped grant, not from password distinctness or wrapper identity.

### Proposed Changes

In contracts.md §"Family agent-instruction core": (1) generalize the beads-runtime-prose sentence so that every beads tenant injects a single bare BEADS_DOLT_PASSWORD via its configured per-project credential-injection wrapper — family tenants share ONE family password via with-livespec-env.sh, while an independent tenant injects its own tenant password from its own 1Password Environment via its own with-<project>-env.sh wrapper; either way bd consumes the same bare variable; no per-tenant BEADS_DOLT_PASSWORD_<tenant> variable and no per-call mapping; isolation comes from the per-tenant SQL user plus DB-scoped grant rather than from password distinctness or wrapper identity. (2) Generalize the beads-access-guard sentence so the guard blocks unless the command runs under a recognized per-project credential-injection wrapper (any with-<id>-env.sh), and clarify the guard is footgun-prevention, not the isolation boundary (the isolation boundary is the per-tenant SQL user plus DB-scoped grant). In non-functional-requirements.md §"Family secrets — 1Password Environment as canonical source": scope the per-tenant beads/Dolt passwords entry to family tenants, noting an independent non-family tenant keeps its own tenant password in its OWN 1Password Environment consumed via its own with-<project>-env.sh wrapper, outside this family source. No H2/H3 heading is added, removed, or renamed, so tests/heading-coverage.json is untouched. No connection-block schema change, no new config key.
