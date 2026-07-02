---
proposal: github-app-token-standardization.md
decision: accept
revised_at: 2026-07-02T01:33:12Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Codifies the credential-model decision groomed from epic livespec-2ef0 (plan/github-app-auth/) at the correct altitude: it constrains the credential class and its invariants (App installation tokens for all automated GitHub operations; App private key PEM probe-only via the tenant's credential_wrapper; tokens ephemeral with transparent re-mint; tenant-scoped fail-closed resolution with no silent fleet fallback; fleet = adopter #0 with install scope restricted to fleet repos; PATs and human OAuth non-conforming on agent paths) while leaving every realization mechanism to the sibling repos' slices. Placement passes the Boundary litmus (fleet infrastructure, contributor-facing) and extends the exact Fleet-secrets section carrying the Credential wrapper contract the rule builds on. A bold-run block inside an existing H3 - no H2 changes, so no tests/heading-coverage.json co-edit is required.

## Resulting Changes

- non-functional-requirements.md
