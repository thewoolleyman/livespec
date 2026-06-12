---
topic: family-secrets-1password-environment
author: claude-fable-5
created_at: 2026-06-12T03:52:30Z
---

## Proposal: family-secrets-1password-environment

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add a new section §"Family secrets — 1Password Environment as canonical source" to SPECIFICATION/non-functional-requirements.md establishing the livespec 1Password Environment as the single canonical source for every family-scoped secret, prohibiting standing secret-bearing files at rest on the host (with one sealed bootstrap exception), permitting run-scoped transient projections only where a consumer interface physically cannot read environment variables, defining GitHub Actions secrets as derived projections pushed under the wrapper, recording the write-side constraint (canonical values are operator-managed in the 1Password UI), and forbidding secret values from ever being committed or echoed into transcripts or logs.

### Motivation

A 2026-06-12 audit found every family secret loose: raw `gh secret set` pushes with no canonical source behind them, and mode-600 secret-bearing files at rest on the host (`tenant-secrets.env.local`, the fabro run-config overlay) — while the 1Password wrapper machinery (`with-livespec-env.sh` from the 1password-env-wrapper project) sat installed but unused. The Environment already carried the live livespec-pr-bot GitHub App private key (verified by a successful JWT mint), making it the natural canonical store. Without a normative rule, secret handling drifts back to ad-hoc files and unmanaged copies; this section makes the canonical-source discipline an invariant of the family's non-functional requirements.

### Proposed Changes

A new section §"Family secrets — 1Password Environment as canonical source" MUST be added to SPECIFICATION/non-functional-requirements.md carrying the following normative rules (decided 2026-06-12):

1. **Canonical source.** The livespec 1Password Environment — consumed via the installed `with-livespec-env.sh` wrapper from the 1password-env-wrapper project — is the SINGLE canonical source for every family-scoped secret: the GitHub App bump-bot credentials (`APP_ID`, `APP_PRIVATE_KEY` — one canonical App private key shared by all family repos), the per-tenant beads/Dolt passwords, the Fabro-dispatch Claude Code OAuth token, and `ANTHROPIC_API_KEY`.

2. **Local consumption rule.** Processes MUST consume secrets via environment injection — invoked under the wrapper. Standing secret-bearing files at rest on the host are PROHIBITED. The single permitted at-rest secret is the wrapper's own 1Password service-account token, sealed via systemd-creds; that token is the bootstrap root of trust.

3. **Scoped transient-materialization rule.** Where a consumer's interface physically cannot read environment variables (config-file-only interfaces), a run-scoped projection — generated from the environment at invocation time and removed when the run ends — is permitted; standing copies remain prohibited.

4. **GitHub Actions exception.** Hosted runners can only read GitHub's own encrypted secret store, so Actions secrets are DERIVED projections of the Environment, pushed via `gh secret set` executed under the wrapper. Rotation is: update the Environment once, then re-run the projection.

5. **Write-side constraint (verified 2026-06-12).** The `op` CLI has no Environment write surface (`op environment read` only) and the family service account holds zero vault grants; adding or rotating canonical values is a manual operator step in the 1Password UI.

6. **No leakage.** Secret values are never committed and never echoed into transcripts or logs — they are referenced by variable name only.
