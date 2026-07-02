---
topic: github-app-token-standardization
author: claude-fable-5
created_at: 2026-07-02T01:01:33Z
---

## Proposal: Fleet GitHub automation credential — App installation tokens

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Extend §"Fleet secrets — 1Password Environment as canonical source" with a GitHub automation credential rule: GitHub App installation tokens become the fleet's standard credential for ALL automated GitHub operations (factory dispatch AND standalone agent worktree commits), with the App private key PEM held probe-only and supplied solely via each tenant's configured credential_wrapper, tokens ephemeral (minted on demand, never persisted at rest), and resolution fail-closed and tenant-scoped (fleet = adopter #0 — no privileged fleet path, no silent fleet fallback). Long-lived personal access tokens and human OAuth tokens stop being conforming automation credentials on agent paths.

### Motivation

The fleet's GitHub credential model was fragmented across three identities, none right for automation: factory dispatch projected the fleet fine-grained PAT LIVESPEC_FAMILY_GITHUB_TOKEN (missing per-repo grants blocked sandbox PR creation; adopters could not bring their own credential), standalone agent worktree commits borrowed the human maintainer's long-lived gho_ OAuth token (broad, human-tied, account-wide), and only CI's GITHUB_TOKEN was fit for purpose. GitHub's primary documentation names App installation tokens the recommended automation credential: short-lived (~1 hour), revocable, structurally least-privilege (a token cannot exceed the App's grants or reach un-granted repos). Origin: groom of epic livespec-2ef0 (plan/github-app-auth/, design record plan/github-app-auth/research/01-design.md); this is the spec-change slice routed to propose-change per the groom operation, codifying the credential-model decision as fleet contract while the realization slices land in livespec-runtime (token provider + git credential helper), livespec-orchestrator-beads-fabro (factory dispatch routing), and the host wiring children of the epic.

### Proposed Changes

In `non-functional-requirements.md` §"Fleet secrets — 1Password Environment as canonical source", insert a new bold-run block titled **GitHub automation credential.** immediately after the **Credential wrapper.** block (it builds on the wrapper contract), with the following content:

**GitHub automation credential.** GitHub App installation tokens are the fleet's automation credential for ALL automated GitHub operations — factory dispatch AND standalone agent worktree commits alike. The durable secret is the App private key PEM: it MUST be held probe-only in the owning tenant's secret store and supplied SOLELY via that tenant's configured `credential_wrapper` environment injection (per the **Local consumption rule** and **Credential wrapper** blocks above); it MUST NOT be committed or persisted at rest outside that store. Installation tokens are ephemeral: they MUST be minted on demand (and re-minted transparently for operations that outlive a token's ~1-hour validity) and MUST NOT be persisted at rest. Credential resolution MUST be tenant-scoped and fail-closed: an automated GitHub operation resolves its credential ONLY through the consuming target's own `credential_wrapper`; a missing wrapper or missing PEM MUST be a hard error with an actionable diagnostic, and there MUST NOT be a silent fallback to the fleet's credential. The fleet is adopter #0 — it holds no privileged path; each adopter brings its own GitHub App and PEM in its own secret store, and the fleet App's installation MUST be restricted to fleet repos only. Long-lived personal access tokens and human OAuth tokens are NOT conforming automation credentials on agent paths; a human's own GitHub authentication MAY remain for genuine human interactive work. Commit authorship on agent paths SHOULD be preserved via git config (human author name plus co-author trailers); the App identity is only the transport.
