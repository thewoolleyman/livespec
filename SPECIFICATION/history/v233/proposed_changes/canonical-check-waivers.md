---
topic: canonical-check-waivers
author: claude-opus-5-5
created_at: 2026-10-28T12:15:10Z
---

## Proposal: Reasoned waivers of canonical checks

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/scenarios.md

### Summary

A consumer MAY waive a canonical livespec-dev-tooling check, one slug at a time, with a committed non-empty reason. All three wiring-completeness layers exempt a waived slug and fail on a stale or malformed waiver. livespec-dev-tooling's contracts.md owns the declaration surface.

### Motivation

The Wiring-completeness invariant requires every canonical check in every consumer's aggregate, with no exception, and the fleet-conformance row canonical-check-slugs-wired enforces it. On 2026-10-28 the livespec-dev-tooling v1.137.1 release fan-out (run 40678729717) excluded livespec-console-beads-fabro, the fleet's Rust member, on that row. Measured against its master, 53 of the 60 omitted canonical checks pass as-is. check-heading-coverage cannot pass without a second coverage map, because console's tests/heading-coverage.json is a scenario-keyed schema owned by its own Rust check-behavior-coverage. Forcing a duplicate map was ruled against (coordinator, 2026-10-28). Until the member rejoins the fan-out it receives no livespec-dev-tooling fix. A committed reason per waived slug keeps the gap visible and reviewable, and the stale-waiver failure stops a waiver from outliving its cause. Work items: livespec-dev-tooling-cmy3kd and livespec-console-beads-fabro-wzrct7.

### Proposed Changes

Amend non-functional-requirements.md §"Shared code sync — livespec-dev-tooling", the **Wiring-completeness invariant** paragraph and the three-layer enforcement list that follows it.

1. Append to the **Wiring-completeness invariant** paragraph:

"A consumer MAY waive a canonical check whose subject it does not have, or whose concern a consumer-private check already owns, by declaring the waiver in committed, tracked data in its own repository. Each waiver MUST name exactly one canonical slug and MUST carry a non-empty reason. A waived slug is exempt from this invariant: its absence from the consumer's `just check` aggregate MUST NOT fail any of the three enforcement layers below. A waiver whose slug the consumer's aggregate DOES select is stale. Each layer MUST fail on a stale waiver, naming the slug, so a waiver cannot outlive the gap it explains. A waiver with an empty reason, or one naming a slug outside the canonical set, MUST fail every layer as malformed. The declaration surface (its file, key and shape) MUST be defined by `livespec-dev-tooling`'s own `contracts.md`, and all three layers MUST read that one surface."

2. In layer 1 (**In-repo gate**), after "fails on any missing canonical slug", insert: "that the consumer has not waived per the invariant above, and on any stale or malformed waiver".

3. In layer 3 (**Cross-repo backstop**), change "asserts, for every `fleet`-array member of the fleet manifest that carries a tracked `just check` target inventory, that the inventory contains every canonical slug." to "asserts, for every `fleet`-array member of the fleet manifest that carries a tracked `just check` target inventory, that the inventory contains every canonical slug the member has not waived, and that the member declares no stale or malformed waiver." Apply the same waived-slug exemption to the doctor invariant's `fail` and `warn` reports in that layer.

Append to scenarios.md a new H2 section, placed after `## An instruction-only adopter is held to plugin currency and to no other baseline concern`:

## A fleet member waives a canonical check with a committed reason

```gherkin
Feature: Reasoned waivers of canonical checks

Scenario: A waived canonical check is not required in the aggregate
  Given a fleet member whose committed waiver declaration names a canonical slug with a non-empty reason
  And its just check aggregate does not select that slug
  When the in-repo gate and the fleet-conformance check evaluate the member
  Then neither reports the waived slug as missing
  And the fleet-conformance check reports the waiver with its reason

Scenario: An unwaived omission still fails
  Given a fleet member whose just check aggregate omits a canonical slug that no waiver names
  When the fleet-conformance check evaluates the member
  Then it reports an error finding naming the member and the slug

Scenario: A stale waiver fails
  Given a fleet member whose committed waiver names a canonical slug that its just check aggregate selects
  When the in-repo gate evaluates the member
  Then it fails, naming the slug as a stale waiver
```
