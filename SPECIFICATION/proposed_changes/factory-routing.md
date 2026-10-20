---
topic: factory-routing
author: claude-opus-5-5
created_at: 2026-10-20T15:58:44Z
---

## Proposal: Factory routing

### Target specification files

- non-functional-requirements.md

### Summary

Add a `## Factory routing` section to non-functional-requirements.md requiring every dispatcher.factories entry this repository commits in its own .livespec.jsonc to be registry-backed ("registry": true, no server, no docker_host) so no committed factory entry names a machine, and requiring dispatcher.default_factory to name legacy. Placed in non-functional-requirements.md because it binds only this repository's own configuration (the §"Boundary" litmus test); the preamble and §"Boundary" are amended to admit it as a sixth top-level section.

### Motivation

Coordinator rulings R318 and R320 (2026-10-20, plan petri-factory-on-gmktec, epic bd-ib-fyozyd) require every fleet repository's committed factory table to be registry-backed and name no machine; a factory is bound to a machine only in the fleet gitops inventory's factory registry. This heading is the governing clause the registry-switch work-item references. It is a rule for this repository's own .livespec.jsonc, not a contract a governed project inherits.

### Proposed Changes

Three edits to `non-functional-requirements.md`, all verbatim.

1. In the opening paragraph, after the sentence ending "plus a `Boundary` preamble, so contributors and agents apply the same categorization rule when landing new content.", append: "One further top-level section, `## Factory routing`, follows them; it states a rule for this repository's own committed `.livespec.jsonc` only, and no project governed by `livespec` and no other fleet repository inherits it."

2. In `## Boundary`, after the `## Scenarios` decision-rule bullet, add the bullet: "- `## Factory routing` — *this repository's own dispatch routing*: the rule its committed `.livespec.jsonc` factory table MUST satisfy. It has no counterpart in the user-facing spec files."

3. Append this H2 and body at the end of the file, after `## Scenarios`:

## Factory routing

Every entry this repository commits in `.livespec.jsonc` under `dispatcher.factories` MUST be registry-backed: it declares `"registry": true` and carries no `server` and no `docker_host` value, so no committed factory entry names a machine. Which Fabro server answers to a factory name is bound only in the fleet gitops inventory's factory registry (livespec-dev-tooling `non-functional-requirements.md` §"Fabro factory registry"), which each dispatching host renders as `/etc/livespec/fabro-factories.json`; a dispatch resolves a registry-backed entry from that file by name. `dispatcher.default_factory` MUST name `legacy`.

