---
topic: vps-info-hook-trust-stopgap
author: claude-opus-5-5
created_at: 2026-11-11T19:24:51Z
---

## Proposal: Non-Driver Codex hook-trust writers leave release-verifiable plugins to the Driver

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

State, in `contracts.md` §"Plugin distribution" → "### Driver-shipped hooks", the contract that binds any host-level writer of Codex hook trust OTHER than the Codex Driver: it MUST NOT write trust for any hook of a plugin whose marketplace the installed Codex Driver can release-verify; it MAY automatically trust the operator's user-level hooks and the hooks of plugins whose marketplace the Driver cannot release-verify; and when it cannot tell, it MUST leave that plugin's hooks to the Driver. Add one scenario stating the observable behaviour.

### Motivation

The Codex Driver's own specification (livespec-driver-codex `SPECIFICATION/contracts.md`) requires that Codex trust in a covered plugin's hooks be re-established from release-verified bytes, or that the host fail closed or report loudly. Nothing in core says what a SECOND trust writer on the same host may do, yet the fleet's dev host runs one: the operator's automatic hook-trust fallback in thewoolleyman/vps-info `services/codex-config/` (systemd units `codex-hook-trust.timer` and `codex-hook-trust-review.timer`). Before thewoolleyman/vps-info#77 it trusted every enabled hook, including the Driver's own, so it could approve bytes the Driver's release verification rejects and mask the Driver's failures. #77 scoped it away from every plugin the Driver can release-verify, under a coordinator ruling (legacy-coordinator-agent, 2026-11-11, R301/R493, reported to the maintainer for objection), and kept automatic trust for third-party plugins such as `honeycomb@honeycomb-plugins`, which the Driver reports `unverified (release tag cannot be identified for this marketplace)` and can never re-trust. That split is a host-observable invariant about who may establish trust in which hooks, so it is a contract and belongs here, beside the Codex Driver guards; the realization (systemd units, the reconciler's code) stays in vps-info. Carries livespec work-item `livespec-75ttpw` (plan epic `livespec-3rfjga`, plan `codex-plugin-hook-path-regression`), whose filing-time tier classification held it for exactly this topic.

### Proposed Changes

1. `SPECIFICATION/contracts.md`, §"Plugin distribution" → "### Driver-shipped hooks": insert the following paragraph IMMEDIATELY AFTER the paragraph that begins `**Codex fleet-host mutation guard (required).**` and BEFORE the paragraph that begins `**pi fleet-host mutation guard (required).**`:

> **Non-Driver Codex hook-trust writers.** A host-level writer of Codex hook trust other than the Codex Driver (`livespec-driver-codex`) — for example an operator's automatic-trust fallback provisioned on a fleet host — MUST NOT write a Codex trust record for any hook of a plugin whose marketplace the installed Codex Driver can release-verify, so that trust in such a plugin's hooks is established only by the Driver, from release-verified bytes. Such a writer MAY automatically trust the operator's own user-level hooks and the hooks of a plugin whose marketplace the installed Driver cannot release-verify. When such a writer cannot determine whether the installed Driver can release-verify a plugin's marketplace — because the Driver's own release-verification resolver cannot be loaded or raises, or because the hook's plugin identity names no marketplace — it MUST leave that plugin's hooks untouched. Which marketplaces the Driver can release-verify is the Driver's determination and MUST be read from the installed Driver, never from a list fixed in the writer. On a host with no Codex Driver installed, this paragraph imposes nothing.

2. `SPECIFICATION/scenarios.md`: append the following new H2 section at the end of the file (no existing heading is changed or removed):

## A non-Driver Codex hook-trust writer leaves release-verifiable plugins to the Driver

```gherkin
Feature: Codex hook trust written by something other than the Driver
  As a fleet operator
  I want a host-level trust fallback to stay out of the plugins the Codex Driver release-verifies
  So that no hook of a release-verifiable plugin runs on trust the Driver did not establish

Scenario: A trust fallback skips release-verifiable plugins and trusts the rest
  Given a host with the Codex Driver installed
  And a plugin whose marketplace the installed Driver can release-verify
  And a third-party plugin whose marketplace the installed Driver cannot release-verify
  And an operator user-level hook
  And Codex reports every one of those hooks as needing trust
  When a host-level hook-trust writer other than the Driver reconciles Codex hook trust
  Then it writes no trust record for any hook of the release-verifiable plugin
  And it writes trust records for the third-party plugin's hooks and the user-level hook

Scenario: A trust fallback that cannot consult the Driver trusts only user-level hooks
  Given a host with the Codex Driver installed
  And the installed Driver's release-verification resolver cannot be loaded
  When a host-level hook-trust writer other than the Driver reconciles Codex hook trust
  Then it writes no trust record for any plugin's hook
  And it writes trust records for the operator's user-level hooks
```

3. Co-edit at revise time (per `spec.md` §"Self-application"): the new `scenarios.md` H2 heading requires a `tests/heading-coverage.json` entry, spelled `../tests/heading-coverage.json` in `resulting_files[]`, with `test` `TODO` and a `reason` naming the integration tier — e.g. "Integration-tier: exercised end-to-end on the dev host against the live Codex app-server by thewoolleyman/vps-info `services/codex-config/` (vps-info#77); no livespec-core integration test drives a third-party Codex trust writer yet." The `contracts.md` change adds no `## ` heading.
