---
topic: one-app-consolidation-installation-scope
author: claude-fabro-on-hp
created_at: 2026-08-19T01:58:07Z
---

## Proposal: One-App consolidation: rename the fleet App and retire the fleet-repos-only installation restriction

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The fleet GitHub App (App id 3668528) was renamed from livespec-pr-bot to thewoolleyman-factory-bot and its installation deliberately widened to All repositories of the owning account (maintainer-directed 2026-08-18: one automation App for all of the maintainer's projects, decoupled from the livespec project name). Two ratified clauses now contradict that decided posture: the GitHub automation credential block's 'the fleet App's installation MUST be restricted to fleet repos only', and the GitHub App permission set block's stale App name plus 'the App MUST be installed only on the repos its tenant owns'. Amend both so installation scope is the resource owner's decision, while keeping tenant-scoped credential resolution (which is what actually isolates tenants) and least-privilege permissions intact.

### Motivation

Maintainer ruling 2026-08-18 during the fabro-on-hp track's App consolidation (livespec-orchestrator-beads-fabro ledger bd-ib-l3nptz, children .10-.13): one GitHub App for everything owned by the maintainer, no per-project Apps, no livespec coupling in its name; the fleet App's installation was widened to All repositories to give the shared fabro factory servers clone coverage over every governed repo (a fabro server clones with its vault App, so a repo outside the installation cannot be dispatched at all - proven live by openbrain sandbox-init failures). The prior fleet-repos-only wording made that widening a spec violation; isolation is in fact carried by per-tenant credential_wrapper resolution and per-tenant secret stores, not by installation narrowness.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md:

1. In the **GitHub automation credential** block, replace the sentence "The fleet is adopter #0 — it holds no privileged path; each adopter brings its own GitHub App and PEM in its own secret store, and the fleet App's installation MUST be restricted to fleet repos only." with: "The fleet is adopter #0 — it holds no privileged path; each EXTERNAL adopter brings its own GitHub App and PEM in its own secret store. An App's installation scope is the resource owner's decision: a single owner MAY install one automation App across all repositories they own (the fleet's owner does exactly this — App id 3668528, currently named `thewoolleyman-factory-bot`, installed account-wide so the shared factory servers can clone any governed repo), and tenant isolation is carried by tenant-scoped credential resolution through each tenant's own `credential_wrapper`, not by installation narrowness."

2. In the **GitHub App permission set** block, replace "A conforming automation App — the fleet's `livespec-pr-bot` and every adopter's own App alike —" with "A conforming automation App — the fleet owner's `thewoolleyman-factory-bot` (App id 3668528) and every adopter's own App alike —", and replace the final sentence "Permissions beyond this set SHOULD NOT be granted (least privilege); the App MUST be installed only on the repos its tenant owns (the fleet App on fleet repos only; an adopter's App on that adopter's repos only)." with: "Permissions beyond this set SHOULD NOT be granted (least privilege). The App MUST NOT be installed on repositories outside the owning account or organization; within the owning account, installation breadth (selected repositories vs all repositories) is the owner's call per the GitHub automation credential block above."

3. In the **GitHub App request budget** block, replace "The fleet's own installation is therefore shared across all members listed in `.livespec-fleet-manifest.jsonc`" with "The fleet's own installation is therefore shared across every repository it is installed on — for an account-wide installation, all repositories of the owning account, not only the members listed in `.livespec-fleet-manifest.jsonc`". The rest of the block is unchanged.
