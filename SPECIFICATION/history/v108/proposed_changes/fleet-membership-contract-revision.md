---
proposal: fleet-membership-contract.md
decision: accept
revised_at: 2026-06-12T06:41:26Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Accepted as proposed (user-authorized). Repo-local enforcement cannot see absence — a repo missing wiring never fails checks it does not run — so a core-owned fleet manifest, per-class obligations across the three obligation types, a central conformance check that blocks the release fan-out as preflight, an idempotent wire-fleet-member reconcile mode sharing the same contract definition, a discovery safety net, register-first repo birth, the retrofit-travels-with-the-rule discipline, and the no-circular-gating rule structurally close the bump-automation hole class. Cross-references resolve intra-tree (branch protection, commit-refuse hooks, toolchain pins) and to the sibling family-secrets section accepted in the same pass; the section is net-new under the Constraints bucket of non-functional-requirements.md.

## Resulting Changes

- non-functional-requirements.md
