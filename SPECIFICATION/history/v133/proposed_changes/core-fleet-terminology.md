---
topic: core-fleet-terminology
author: gpt-5-codex
created_at: 2026-06-24T01:16:59Z
---

## Proposal: Converge core terminology on fleet

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Migrate the active livespec core specification vocabulary from the legacy
domain term `family` to `fleet` where the text refers to the governed set of
repositories, shared infrastructure, shared secrets, shared operational
discipline, or member tenants.

### Motivation

The fleet terminology better describes livespec's operational model: manifest
membership, conformance, dispatching, release fan-out, shared automation, and
shared observability. The legacy term mixes product meaning with social or
generic grouping language and makes the spec less precise.

### Proposed Changes

In `spec.md`, update the reference-orchestrator dogfooding language to say the
livespec fleet dogfoods Beads/Dolt + Fabro.

In `contracts.md`, rename `## Family agent-instruction core` to `## Fleet
agent-instruction core`, update the universal agent-instruction wording, and
express beads-runtime tenant/password guidance in fleet terms.

In `non-functional-requirements.md`, update self-application, shared
coordination, observability, secret-management, branch-protection,
commit-refuse-hook, fleet-membership, and reference-orchestrator wording from
family terminology to fleet terminology. Because the contracts heading is
renamed, update `tests/heading-coverage.json` to keep the heading map in
lockstep.
