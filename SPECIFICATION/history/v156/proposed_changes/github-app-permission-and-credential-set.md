---
topic: github-app-permission-and-credential-set
author: claude-fable-5
created_at: 2026-07-03T02:48:09Z
---

## Proposal: GitHub App permission set

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add a bold-lead **GitHub App permission set.** clause to non-functional-requirements.md §"Fleet secrets — 1Password Environment as canonical source", immediately after the existing **GitHub automation credential.** block (v153). The clause codifies the exact repository-permission set a conforming automation App MUST hold — Contents: Read and write, Pull requests: Read and write, and Workflows: Read and write — plus least-privilege (no permissions beyond the set) and tenant-scoped installation (fleet App on fleet repos only; an adopter's App on that adopter's repos only). This is a clause-only extension inside the existing H2 (no heading changes, so no tests/heading-coverage.json co-edit), per the v022 beads-fabro precedent of clause-only extensions.

### Motivation

Maintainer directive following the github-app-auth epic (livespec-2ef0, closed 2026-07-03): codify the GitHub App/token setup and permission learnings into the spec. The Workflows: Read and write grant proved load-bearing in practice — GitHub structurally rejects any App push that creates or updates a file under .github/workflows/ without it, silently capping the factory's reach (discovered as livespec-2ef0.1). Without a codified permission set, every adopter (and any fleet App re-creation) re-discovers this by hitting the same rejection.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md` §"Fleet secrets — 1Password Environment as canonical source", insert the following bold-lead clause paragraph immediately AFTER the **GitHub automation credential.** block and BEFORE the **Scoped transient-materialization rule.** block:

**GitHub App permission set.** A conforming automation App — the fleet's `livespec-pr-bot` and every adopter's own App alike — MUST hold the repository permissions the automated paths require: `Contents: Read and write`, `Pull requests: Read and write`, and `Workflows: Read and write`. The workflows grant is load-bearing: GitHub structurally rejects any App push that creates or updates a file under `.github/workflows/` without it, silently capping the factory's reach (discovered as livespec-2ef0.1). Permissions beyond this set SHOULD NOT be granted (least privilege); the App MUST be installed only on the repos its tenant owns (the fleet App on fleet repos only; an adopter's App on that adopter's repos only).

No heading is added, changed, or removed; no other clause in the section is modified.

## Proposal: Tenant credential set

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add a bold-lead **Tenant credential set.** clause to non-functional-requirements.md §"Fleet secrets — 1Password Environment as canonical source", immediately after the new **GitHub App permission set.** clause. The clause codifies the COMPLETE credential set a tenant's `credential_wrapper` MUST inject for its automated paths — the GitHub App pair (`GITHUB_APP_ID`, `GITHUB_PRIVATE_KEY`; plus `GITHUB_APP_INSTALLATION_ID` when the App holds more than one installation), the tenant's work-items store secret (e.g. `BEADS_DOLT_PASSWORD`), and the dispatch engine's LLM credential (today `CLAUDE_CODE_OAUTH_TOKEN` for the Claude Code engine) — plus fail-closed diagnostics naming any missing variable and the adopter-onboarding completion criterion (the full set resolves through the adopter's OWN wrapper; fleet = adopter #0, no shared fallback). Clause-only extension inside the existing H2 (no heading changes), per the v022 beads-fabro precedent.

### Motivation

Maintainer directive following the github-app-auth epic (livespec-2ef0, closed 2026-07-03): the epic established which environment variables the automated paths actually consume and that onboarding is only complete when the tenant's own wrapper resolves the full set. Codifying the set closes the gap where a tenant's wrapper injects the store secret but not the GitHub App pair (or vice versa), which today surfaces only as a late runtime failure inside a dispatched sandbox rather than as an actionable onboarding diagnostic.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md` §"Fleet secrets — 1Password Environment as canonical source", insert the following bold-lead clause paragraph immediately AFTER the new **GitHub App permission set.** clause (i.e. second of the two new clauses following the **GitHub automation credential.** block) and BEFORE the **Scoped transient-materialization rule.** block:

**Tenant credential set.** A tenant's `credential_wrapper` MUST inject the COMPLETE credential set its automated paths consume: the GitHub App pair (`GITHUB_APP_ID`, `GITHUB_PRIVATE_KEY`; plus `GITHUB_APP_INSTALLATION_ID` when the App holds more than one installation), the tenant's work-items store secret (e.g. `BEADS_DOLT_PASSWORD`), and the dispatch engine's LLM credential (today `CLAUDE_CODE_OAUTH_TOKEN` for the Claude Code engine). Each consuming seam MUST fail closed with an actionable diagnostic naming any missing variable; adopter onboarding is complete only when the full set resolves through the adopter's OWN wrapper (fleet = adopter #0, no shared fallback).

No heading is added, changed, or removed; no other clause in the section is modified.
