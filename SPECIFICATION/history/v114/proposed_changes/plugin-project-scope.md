---
topic: plugin-project-scope
author: E2E Test
created_at: 2026-06-16T05:47:12Z
---

## Proposal: Project-scoped plugin enablement

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Reframe §"Plugin distribution" from a machine-wide `/plugin install` to project-scoped enablement: consumers commit a `.claude/settings.json` declaring remote-GitHub `extraKnownMarketplaces` + `enabledPlugins` (core + Driver + their `.livespec.jsonc` impl), so skills and the Driver's bundled hooks load only in the governed project, never machine-wide. Also corrects the stale "Driver installs globally (per-user, not per-project)" fail-open rationale to project-scoped enablement (config gate still scopes behavior).

### Motivation

Epic livespec-gy21 (openbrain peer review 2026-06-15): the family was enabled at user/global scope, leaking skills + hooks into every project on the host. Project-scoping stops the leak; the contract must document the project-scoped install as the default.

### Proposed Changes

Replace the `/plugin marketplace add` + `/plugin install` block with a committed `.claude/settings.json` example (extraKnownMarketplaces + enabledPlugins, remote GitHub) and state that consumers enable core + Driver + the impl named by `.livespec.jsonc`. Keep the machine-wide install as a supported-but-non-default fallback. Update the fail-open paragraph in §"Driver-shipped hooks" so its rationale reflects project-scope enablement rather than global per-user install.
