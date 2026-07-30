---
topic: remove-mise-bd-pin
author: codex-gpt-5
created_at: 2026-07-30T09:09:45Z
---

## Proposal: Remove Beads from project-local mise toolchain pins

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Correct the toolchain contract so the Beads CLI is a host-provisioned runtime dependency reached through the lifecycle guard, not a project-local mise pin that can shadow that guard.

### Motivation

The current toolchain section still says bd is pinned in .mise.toml even though the pin was removed. Obsolete mise-managed Beads installs regenerated a bd shim ahead of /usr/local/bin/bd, creating a brittle path where a repository declaration could activate an unguarded binary.

### Proposed Changes

The Toolchain pins section MUST remove bd from the list of project-local mise-managed tools. It MUST state that a beads-backed repository obtains bd from its host runtime rather than declaring bd in .mise.toml, and that a fleet host whose lifecycle policy is enforced by a bd guard MUST resolve the supported bd entry point to that guard. Repository mise configuration MUST NOT declare or install bd because an active mise tool or regenerated shim can shadow the guarded entry point. Normal ledger callers MUST NOT invoke the guard's private delegate executable directly. Add a scenario under the existing non-functional Scenarios section proving that a beads-backed fleet checkout cannot select a mise-managed bd ahead of the lifecycle guard.
