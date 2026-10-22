---
topic: factory-routing-default-petri
author: claude-opus-5-5
created_at: 2026-10-22T22:13:25Z
---

## Proposal: Default factory names petri after the Petri cutover

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Amend the last sentence of §"Factory routing" so `dispatcher.default_factory` MUST name `petri` instead of `legacy`, and require the table to keep declaring `legacy` so in-flight items pinned to it still resolve.

### Motivation

The maintainer directed the Fabro upgrade onto the Petri-era factory on gmktec (coordinator ruling R668, relayed 2026-10-22: "priority is getting fabro upgrade done and running on gmktec"; work-item bd-ib-iud52v in the livespec-orchestrator-beads-fabro tenant). The fleet registry /etc/livespec/fabro-factories.json already resolves `petri`. The ratified v226 sentence pins the default to `legacy`, so this repository cannot move its dispatches to Petri without amending it. Keeping `legacy` declared preserves resolution for any item whose recorded factory pin names it, per the recorded-pin rules. The registry-backed rule itself (no `server`, no `docker_host`) is unchanged.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md` §"Factory routing", replace the final sentence

> `dispatcher.default_factory` MUST name `legacy`.

with

> `dispatcher.default_factory` MUST name `petri`, and the table MUST still declare `legacy`, so an item whose recorded factory pin names `legacy` keeps resolving.

No other text in the section changes; the heading is unchanged, so `tests/heading-coverage.json` needs no co-edit.
