---
topic: wiring-completeness-sibling-advisory
author: claude-opus-5-5
created_at: 2026-10-27T03:18:10Z
---

## Proposal: wiring-completeness-cross-repo fails only on the consumer's own drift, reports sibling drift as advisory, and refuses rather than skips when it cannot evaluate

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md

### Summary

The cross-repo wiring-completeness check reports its result in one finding. It fails only when a canonical slug is missing from the consuming repo's own just-check inventory, which it reads from the project root even when that root is not in the registry. A slug missing from a sibling's inventory makes the finding warn, naming the sibling and the slugs. That drift fails instead in the dev-tooling fleet-conformance check, which the drifting sibling cannot remove in the same change. The check applies only to projects that declare the cross-repo conformance registry. It reads the canonical set from a source inside the plugin runtime envelope, and it fails rather than skips when it cannot read that set, so a run that could not evaluate the check never reads as green.

### Motivation

Spec-first for work-item livespec-wggfps (P1, held for dispatch; coordinator gitops-fleet-capacity-monitoring ruling R96; requested by petri-factory-on-gmktec). On livespec-orchestrator-beads-fabro master 89eaa1d07 with core c485d0ba4841, the system-python wrapper reports the check 'skipped' and green, because livespec_dev_tooling is not importable there. Under the repo venv the same check FAILS on 136 sibling drift pairs: dolt-server 64, console 60, driver-claude 3, driver-codex 3, runtime 3. That reds every gate where dev-tooling imports, including the factory sandbox, and it blocked bd-ib-6zy3zd for drift that the consuming repo neither owns nor can fix. So the check today has two wrong outcomes: a red gate in one repo for another repo's drift, and a green result when the check never ran. The fix keeps the adversarial-drift backstop. A consumer that drops a canonical slug together with check-aggregate-completeness still fails its OWN doctor run, which reads its own inventory, while sibling drift stays visible without blocking unrelated repos. Prior art: livespec-i6pyy6 (the CI sibling-clone list; it makes unevaluable siblings fail CI loudly) and livespec-dbbgoc (read siblings' canonical branch). The sibling drift itself is owned by the delegated-gate-fleet-rollout thread. A first read-only Opus review raised four blockers, and all four are folded in. (1) Making sibling drift advisory everywhere would have removed the adversarial-drift backstop, so sibling drift now fails in the fleet-conformance check, which already excludes a non-conformant sibling from the release fan-out loudly. (2) A hard refusal on an unimportable livespec_dev_tooling would fail every installed plugin's doctor pre-step, because that module is not vendored, so the canonical set must be readable inside the runtime envelope. (3) The consumer's own inventory and the check's applicability are now defined. (4) A registered check returns one finding, so the status is computed over the consumer and its siblings together. A second Opus round raised one blocker, which is folded in: the fleet-conformance obligation is scoped to `fleet`-array members of the fleet manifest, and a registered sibling outside that array stays advisory.

### Proposed Changes

Three edits in two files; all MUST land together in a single revision. No `## ` or `### ` heading is added, changed or removed.

**1. `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants" → "`wiring-completeness-cross-repo`".** Replace

```
compute the canonical-set difference, and fire `fail` on any inventory lacking any canonical slug.
```

with

```
compute the canonical-set difference, and report it in the check's single finding. The check applies only to a project whose `.livespec.jsonc` declares the cross-repo conformance registry; any other project MUST receive a single non-failing `skipped` finding. For an applicable project, the check MUST also resolve the tracked inventory of the project root it was run against (the consuming repo), read directly from that root whether or not the root appears in the registry. The finding's message MUST name each inventory lacking a canonical slug and each slug it lacks, attributing a sibling's drift to that sibling. Its status MUST be `fail` when the consuming repo's own inventory lacks a canonical slug, otherwise `warn` when any sibling's inventory does, otherwise `pass`; a sibling's drift MUST NOT fail the consuming repo's run, and, for a `fleet`-array member, it fails instead in the fleet-conformance check of `non-functional-requirements.md` §"Fleet membership contract" → "Fleet-conformance enforcement", which a drifting sibling cannot remove in the same change. The check MUST read the canonical set from a source satisfiable inside the plugin runtime envelope (`constraints.md` §"Vendored-library discipline"), such as a committed projection of `livespec_dev_tooling.canonical_checks` shipped in the bundle and verified for equality by a livespec-private check. When it cannot read the canonical set, the check MUST report `fail` naming the source it failed to read, and MUST NOT report `skipped`, so a run that could not evaluate the check never reads as green.
```

**2. The same paragraph.** Replace

```
the in-repo gate cannot catch that combination (the gate is gone before it next runs), but the cross-repo backstop can.
```

with

```
the in-repo gate cannot catch that combination (the gate is gone before it next runs), but the cross-repo backstop surfaces it in every other consuming repo's run, and the fleet-conformance check fails it.
```

**3. `SPECIFICATION/non-functional-requirements.md` §"Shared code sync — livespec-dev-tooling", item 3 "Cross-repo backstop.".** Replace

```
resolves the tracked static target inventory reached by that repo's `just check` recipe, and fires `fail` on any inventory lacking a canonical slug.
```

with

```
resolves the tracked static target inventory reached by that repo's `just check` recipe, and reports a missing canonical slug per that section: `fail` for the consuming repo's own inventory and `warn` for a sibling's. A sibling's missing canonical slug MUST fire `fail` in the fleet-conformance check of §"Fleet membership contract" → "Fleet-conformance enforcement", which asserts, for every `fleet`-array member of the fleet manifest that carries a tracked `just check` target inventory, that the inventory contains every canonical slug. A registered sibling outside the `fleet` array has no such obligation, and its drift stays advisory.
```

The fleet-conformance assertion in edit 3 is a committed follow-up owned by the `livespec-dev-tooling` sibling (§"Sibling spec ownership"). So are shipping a canonical-set projection inside the plugin bundle and its livespec-private equality check, which are owned by core's implementation.
