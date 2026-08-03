---
topic: github-hosted-ci-posture
author: codex-gpt-5
created_at: 2026-08-03T01:14:40Z
---

## Proposal: GitHub-hosted fleet CI posture

### Target specification files

- non-functional-requirements.md

### Summary

Make GitHub-hosted runners the current fleet-wide CI execution posture so the shared factory host is reserved for Fabro, Dolt, and other production machinery instead of carrying an always-resident CI pool.

### Motivation

The maintainer explicitly reversed the earlier local-runner mandate after the shared host became overloaded. The live host had 48 idle GitHub Actions listeners across eight repositories even while normal CI was already routed to ubuntu-latest. This proposal explicitly supersedes the local-hot-runner rollout recorded by livespec-3lev and its Phase 0/2/3 children for the current operating period.

### Proposed Changes

In non-functional-requirements.md under the existing CI invocation and merge-gate guidance, the fleet's merge-gating CI MUST execute on GitHub-hosted runners. Fleet repositories MUST NOT depend on a self-hosted runner label for their ordinary CI gate while this posture is active, and self-hosted-only auxiliary CI workflows MUST remain disabled rather than queue indefinitely. The shared factory host MUST NOT run a resident CI supervisor, listener pool, runner-liveness timer, or runner-cache timer during this posture; Fabro, Dolt, and Dispatcher machinery remain in scope and are not disabled by this CI rule. Reactivating fleet self-hosted CI MUST require a later spec revision plus separately provisioned capacity, rather than an implicit repository-variable deletion or service restart. Add a contributor-facing Gherkin scenario under the existing non-functional Scenarios section proving that a fleet PR executes its gate on GitHub-hosted capacity and leaves no CI listener or worker on the shared factory host.
