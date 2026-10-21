---
topic: adopter-registration-posture-for-toolchain-less-repos
author: claude-opus-5-5 (petri-factory-on-gmktec 4320c559)
created_at: 2026-10-21T06:42:43Z
---

## Proposal: A released adopter is registered only after its committed configuration satisfies plugin currency

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/scenarios.md

### Summary

Amend non-functional-requirements.md §"Fleet membership contract" → "Adopters" so that an adopter entry with posture released MUST NOT land in .livespec-fleet-manifest.jsonc until the adopter repository's committed configuration already satisfies the adopter currency row, while an adopter that is not yet wired MAY be registered with posture none. This reconciles the register-before-wiring practice in livespec's .ai/adding-an-adopter.md with the world-gate behaviour the fleet actually runs, and adds one scenario.

### Motivation

Measured 2026-10-21. livespec PR #2913 registered seven host/deploy repositories (vps-info, poweredge-xubuntu-info, gmktec-xubuntu-info, hp-xubuntu-info, fabro-hosts, otel-collector, local-llm) as released adopters before any carried .claude/settings.json, following .ai/adding-an-adopter.md, which says registering before wiring is deliberate so that the gap 'surfaces as a conformance finding'. But the adopter leg's adopter-claude-plugin-currency row is error-severity with no warning demotion (maintainer decision 2026-07-20), and check-fleet-conformance-admin runs inside livespec-dev-tooling's post-merge janitor. Running it locally against livespec master reported exactly one finding per repository (adopter-claude-plugin-currency: '.claude/settings.json missing', seven findings, exit 4), and every livespec-dev-tooling reconcile-merged went red until #2915 reverted the registration. The guide's 'surface as a finding' and the gate's 'fail loud' cannot both hold for a released adopter: a declared-but-unwired released adopter is not a visible finding, it is a blocked world gate. Posture none already gives the visibility the guide wants without the block, because the sweep reports a posture-excluded adopter by name at info severity rather than leaving it invisible.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md §"Fleet membership contract", append the following paragraph immediately AFTER the paragraph beginning `**Adopters.** Beyond the fleet members it enumerates in the \`fleet\` array`:

> **Registration follows wiring for a released adopter.** An adopter entry whose `posture` is `released` MUST NOT be merged into the manifest until the adopter repository's committed configuration already satisfies every obligation the fleet-conformance sweep holds a `released` adopter to — today the adopter plugin-currency row — because the sweep's adopter findings fail loud and a released-but-unwired adopter therefore reddens every world-gate consumer rather than surfacing as a finding. An adopter that is not yet wired MAY be registered with `posture: none`, which the sweep reports by name as posture-excluded and never evaluates, so the declaration is visible before the wiring lands; the entry's `posture` MUST then change to `released` in a later manifest change, once the wiring is committed. The fleet-maintainer registration guide (`.ai/adding-an-adopter.md`) MUST state this ordering and MUST NOT describe registering a released adopter ahead of its wiring as deliberate.

In SPECIFICATION/scenarios.md, append:

```
## A released adopter is registered only after its wiring satisfies the sweep

Given an adopter repository whose committed configuration does not yet satisfy the adopter plugin-currency row
When the fleet maintainer registers it in the manifest
Then the entry carries posture none and the fleet-conformance sweep reports it as posture-excluded without failing
And only after the repository commits configuration that the adopter plugin-currency row passes does the entry change to posture released
```

This adds one `## ` heading to scenarios.md; the revise that accepts this finding MUST co-edit tests/heading-coverage.json in the same change, adding an entry for that heading (its `test` MAY be the literal "TODO" with a non-empty `reason`).

## Proposal: A toolchain-less host or deploy adopter takes the instruction-only profile, which binds plugin currency and no other baseline concern

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/scenarios.md

### Summary

Define an adopter-only profile, instruction-only, for a repository whose only livespec surface is committed agent configuration (a .claude/settings.json enabling livespec core and the Driver, and its agent instructions) and which carries no livespec toolchain (no justfile, no mise configuration, no .livespec.jsonc, no work-items tenant). An instruction-only adopter with posture released is held to the Plugin-currency concern only; Shell-and-Justfile-discipline, Request-budget-discipline and every other baseline concern do not bind it until it declares the baseline profile. One scenario is added.

### Motivation

Measured 2026-10-21 on the seven host/deploy repositories named in the previous finding: none carries a justfile, mise configuration, .livespec.jsonc or .beads directory. Every existing posture misstates or overloads them. Posture released binds the baseline concerns Plugin-currency, Shell-and-Justfile-discipline and Request-budget-discipline (each 'bound where an adopter's posture is released'), and the last two presuppose a livespec toolchain these repositories do not have, so a released registration states obligations they cannot meet. Posture pinned misstates them, because their sessions track the latest-released plugin builds through a SessionStart hook rather than a pinned marketplace registration. Posture none is truthful only until they are wired, and leaves the Driver's hooks (including the fleet-host mutation guard these repositories exist to receive) outside the sweep's currency check. The fleet needs a named class whose obligations are exactly the ones such a repository can and should meet: running the current livespec plugins so the Driver's guards reach sessions opened in it.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md §"Conformance Pattern", in the paragraph beginning `**Profiles and the declarative manifest.**`, after the sentence that lists `baseline` (every governed repo) plus additive layers, insert:

> An adopter MAY instead declare the adopter-only profile `instruction-only`, which REPLACES the `baseline` floor rather than layering on it: it is for a repository whose only livespec surface is committed agent configuration — a `.claude/settings.json` enabling livespec core and the livespec Driver, plus its agent instructions — and which carries no livespec toolchain (no `justfile`, no mise configuration, no `.livespec.jsonc`, no work-items tenant). Of the `baseline` concerns, an `instruction-only` adopter whose `posture` is `released` MUST be held to Plugin-currency and MUST NOT be held to Shell-and-Justfile-discipline, Request-budget-discipline, or any other `baseline` concern; its Plugin-currency obligation is satisfied by the documented successor mechanism (`livespecPluginCurrencySuccessor` with a non-empty `mechanism` and `documentedIn`) as well as by the SessionStart `ensure-plugins` wiring, since it carries no justfile to wire. A fleet member MUST NOT declare `instruction-only`. An `instruction-only` adopter that later adopts the livespec toolchain MUST change its profile to `baseline` (plus any layers), at which point every `baseline` concern binds it under its `posture`.

In the same file, in §"Shell and Justfile discipline" and §"Request-budget discipline", where each states that it binds opted-in adopters whose `posture` is `released`, append to that sentence: "except an adopter whose profile is `instruction-only` (§\"Conformance Pattern\" → \"Profiles and the declarative manifest\")".

In SPECIFICATION/scenarios.md, append:

```
## An instruction-only adopter is held to plugin currency and to no other baseline concern

Given an adopter registered with profile instruction-only and posture released
And its repository carries no justfile, mise configuration or .livespec.jsonc
And its committed .claude/settings.json declares livespecPluginCurrencySuccessor with a non-empty mechanism and documentedIn
When the fleet-conformance sweep evaluates the adopter
Then the adopter plugin-currency row passes
And no Shell-and-Justfile-discipline or Request-budget-discipline obligation is evaluated for it
```

This adds one `## ` heading to scenarios.md; the revise that accepts this finding MUST co-edit tests/heading-coverage.json in the same change, adding an entry for that heading (its `test` MAY be the literal "TODO" with a non-empty `reason`). Implementation of the profile value in livespec-dev-tooling's manifest parser and sweep is a follow-up work-item in that repository and is NOT part of this specification change.
