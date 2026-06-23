---
proposal: independent-beads-tenants.md
decision: accept
revised_at: 2026-06-23T02:31:11Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Maintainer ratifies permitting INDEPENDENT (non-family) beads tenants. The beads-runtime prose and the beads-access guard are generalized from family-only to any per-project credential-injection wrapper (with-<id>-env.sh): every tenant injects a single bare BEADS_DOLT_PASSWORD via its configured wrapper; family tenants share ONE family password via with-livespec-env.sh by explicit choice, while an independent tenant injects its own tenant password from its own 1Password Environment via its own with-<project>-env.sh wrapper. Isolation still comes from the per-tenant SQL user + DB-scoped grant, not from password distinctness or wrapper identity; the guard is footgun-prevention, not the isolation boundary. Backward-compatible: family tenants are unchanged. The family-secrets canonical-source entry is scoped to family tenants. No H2/H3 heading is added, removed, or renamed, so tests/heading-coverage.json is untouched.

## Resulting Changes

- contracts.md
- non-functional-requirements.md
