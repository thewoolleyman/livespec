---
topic: orchestrator-roll-currency-exception
author: claude:gmktec-factory-placement
created_at: 2026-11-07T18:57:32Z
---

## Proposal: The plugin currency invariant carves out an orchestrator build a fleet clone holds under a recorded roll step

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The currency invariant in §"Plugin currency and the release train" requires every new session in every fleet repository to run the latest-released build of every livespec-ecosystem plugin. livespec-dev-tooling is ratifying a rule that a session start must not move an installed orchestrator plugin build, only a named operator step, because that install is what a repository's host dispatcher launches from. This proposal carves that plugin and that hold out of the invariant, and keeps staleness loud rather than hidden.

### Motivation

Plan gmktec-factory-placement (epic livespec-dev-tooling-me5aqz in the livespec-dev-tooling tenant). Session starts moved orchestrator builds, and so factory launch builds, with no roll step, including mid-canary (measured 2026-11-07). livespec-dev-tooling spec v154 (proposal orchestrator-build-explicit-adoption, ruled by legacy-coordinator-agent under R301) stops that. A read-only doctor run found the conflict with this invariant: nothing goes red, because per that run `assert_claude_plugin_currency` checks wiring only and `_currency/verify.py` judges core only (read, not run), so the two specifications would disagree silently. livespec-dev-tooling's earlier v150 had the same conflict. The revise here is this repository's own decision; this proposal does not presume it.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md` §"Plugin currency and the release train", after the paragraph **The currency invariant.**, add:

> **The orchestrator roll exception.** The orchestrator plugin is excepted from the currency invariant's latest-released requirement in one case: a fleet repository's or adopter's project-scope install held behind the latest release because livespec-dev-tooling's §"Orchestrator build adoption" moves that build only through a named operator step. A host dispatcher launches from that install, so a build moved by a session lifecycle event changes the factory's build outside any canary. The exception does not hide staleness: a session running a held build MUST still be able to tell that it is behind. It covers no other plugin, and no build a clone holds for any other reason.

Review the invariant's Mechanism and Installer slots for wording that assumes every session start updates every plugin, and align them to this exception. No new core skill, CLI or functional doctor invariant is implied.
