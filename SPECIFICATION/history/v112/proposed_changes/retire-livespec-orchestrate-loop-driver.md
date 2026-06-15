---
topic: retire-livespec-orchestrate-loop-driver
author: livespec-a8bb-cutover
created_at: 2026-06-15T01:40:07Z
---

## Proposal: Retire the livespec-resident cross-repo loop driver (W6 cutover)

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/non-functional-requirements.md

### Summary

The user declared the W6 dark-factory cutover (2026-06-15): the reference Beads/Dolt + Fabro orchestrator now realizes the Dispatcher and carries routine cross-repo work unattended. The interim `.claude/skills/livespec-orchestrate/SKILL.md` loop driver (which carried no contract status) is retired and removed. This proposed change flips the two spec passages that described that skill as 'slated for retirement … until then working tooling' to record it as RETIRED, with the orchestrator-internal Dispatcher named as the successor.

### Motivation

Realize work-item livespec-a8bb under epic livespec-4moata (v103/v105 contract + reference-implementations re-steering). The user reserved the cutover declaration and declared it; a8bb retires the Layer-3 human-driven loop driver now that the autonomous Dispatcher is proven (operability trio + cost + telemetry + reflector all met). Per the standing relocate-never-drop directive, the skill's normative architectural disciplines (mode/budget parameters, janitor hard-gate, structured iteration journal) already live in non-functional-requirements.md §"Orchestrator-internal Dispatcher guidance"; its exact mechanics (wave-plan grammar, journal format, dispatch table) are mechanism-level detail that retires with the driver and belongs to the orchestrator repo's own specification. Nothing load-bearing existed only in the skill.

### Proposed Changes

Two body-text edits within existing sections (no `## ` heading is added, renamed, or removed; tests/heading-coverage.json is unaffected).

1. In `spec.md` §"Contract + reference implementations architecture", replace the `**No required cross-repo loop driver.**` paragraph so it records the skill as RETIRED (was interim working tooling WITHOUT contract status) now that the reference Beads/Dolt + Fabro orchestrator realizes the Dispatcher and carries routine cross-repo work unattended, with normative loop discipline surviving as the orchestrator-internal Dispatcher guidance in non-functional-requirements.md and the rest belonging to the orchestrator repo's own specification.

2. In `non-functional-requirements.md` §"Orchestrator-internal Dispatcher guidance", replace the closing sentence of the section's final paragraph so it likewise records the skill as RETIRED now that a reference orchestrator realizes the Dispatcher (the Beads/Dolt + Fabro dark factory carries routine cross-repo work unattended), keeping the cross-reference to spec.md §"Contract + reference implementations architecture".

The principle 'No repository is REQUIRED or expected to carry a cross-repo loop driver as core contract surface' is preserved verbatim in both passages.
