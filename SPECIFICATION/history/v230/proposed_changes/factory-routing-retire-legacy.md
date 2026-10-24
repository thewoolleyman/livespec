---
topic: factory-routing-retire-legacy
author: claude-opus-5-5
created_at: 2026-10-24T06:08:19Z
---

## Proposal: Retire the legacy factory entry from the committed factory table

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Remove the requirement that the committed `dispatcher.factories` table keep declaring `legacy`, the registry name of the hp-xubuntu factory instance being retired. `dispatcher.default_factory` still MUST name `petri`.

### Motivation

Fleet capacity coordinator ruling (gitops-fleet-capacity-monitoring, 2026-10-24) carrying the fabro-currency plan's Definition-of-Done assertion that hp carries no factory role in the committed fabro-hosts inventory: hp's legacy Fabro unit is being stopped and its factory role removed, which first requires every repository to stop declaring `legacy`. The requirement existed so that an open work item whose recorded `dispatch_factory` pin names `legacy` keeps resolving. A fresh dispatch never reads that pin (the orchestrator reads it only for a resume of the same run lineage), and the petri-factory-on-gmktec seat triaged every open legacy-pinned item across the fleet on 2026-10-24: none needs a run read from hp, because each closes through forge-held records.

### Proposed Changes

Apply exactly this edit; no heading changes, so tests/heading-coverage.json is unchanged. The same pull request removes the `legacy` entry from `.livespec.jsonc` and updates every test that asserts the committed table declares it.

```diff
--- a/SPECIFICATION/non-functional-requirements.md
+++ b/SPECIFICATION/non-functional-requirements.md
@@ -1670,2 +1670,2 @@
 
-Every entry this repository commits in `.livespec.jsonc` under `dispatcher.factories` MUST be registry-backed: it declares `"registry": true` and carries no `server` and no `docker_host` value, so no committed factory entry names a machine. Which Fabro server answers to a factory name is bound only in the fleet gitops inventory's factory registry (livespec-dev-tooling `non-functional-requirements.md` §"Fabro factory registry"), which each dispatching host renders as `/etc/livespec/fabro-factories.json`; a dispatch resolves a registry-backed entry from that file by name. `dispatcher.default_factory` MUST name `petri`, and the table MUST still declare `legacy`, so an item whose recorded factory pin names `legacy` keeps resolving.
+Every entry this repository commits in `.livespec.jsonc` under `dispatcher.factories` MUST be registry-backed: it declares `"registry": true` and carries no `server` and no `docker_host` value, so no committed factory entry names a machine. Which Fabro server answers to a factory name is bound only in the fleet gitops inventory's factory registry (livespec-dev-tooling `non-functional-requirements.md` §"Fabro factory registry"), which each dispatching host renders as `/etc/livespec/fabro-factories.json`; a dispatch resolves a registry-backed entry from that file by name. `dispatcher.default_factory` MUST name `petri`.
```

